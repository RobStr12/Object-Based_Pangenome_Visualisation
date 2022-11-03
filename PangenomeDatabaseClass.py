from typedb.client import TypeDB, SessionType, TransactionType
from typedb.common.exception import TypeDBClientException
from alive_progress import alive_bar
from datetime import timedelta
from subprocess import Popen
from subprocess import run
from sys import platform
import psutil
import ijson
import gzip
import time
import os


class PangenomeDatabase:

    def __init__(self, name: str):
        # Initialize all variables
        self.name = name
        self.server = None
        self.client = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self):
        # Because github can not have empty folders, the ./server/data folder needs to be re-implemented each time
        path = "./server/data"
        if not os.path.isdir(path):
            os.mkdir(path)

        # Start the server at localhost:1730 & start the client
        servers = {"win32": ["server.bat", "&"], "darwin": ("server.sh", "server")}
        if platform == "win32":
            self.server = Popen(servers[platform])
        else:
            self.server = run(servers[platform])
        self.client = TypeDB.core_client("localhost:1730")

    def close(self, kill_java: bool = True):
        # close the client & terminate the server
        self.client.close()
        if platform == "win32":
            self.server.terminate()

        # in order to be able to delete, change, ... certain files in the server folder, the OpenJDK Platfrom binary
        # needs to be shut down. To accomplish this, following code is implemented. When initialising the class again,
        # The OpenJDK Platform binary will restart again on its own.
        for process in (process for process in psutil.process_iter() if process.name()=="java.exe"):
            if kill_java:
                process.kill()

    def exists(self):
        # check if the database exists
        return self.client.databases().contains(self.name)

    def delete(self):
        # delete the database
        try:
            self.client.databases().get(self.name).delete()
        except TypeDBClientException:
            print("Database does not exist...")

    def create(self, replace: bool = False, file: str = "./Data/schema.tql"):

        if replace is True:
            print("(Re-)Creating Database")
            self.delete()
            self.client.databases().create(self.name)
            with open(file, "r") as schema:
                query = schema.read().replace("\n", "")
            with self.client.session(self.name, SessionType.SCHEMA) as session:
                with session.transaction(TransactionType.WRITE) as transaction:
                    transaction.query().define(query)
                    transaction.commit()
        elif not self.exists():
            self.create(replace=True)
        else:
            print(f"There already exists a database called {self.name}.")

    def migrate(self, file: str, template, batch_size: int = 5000):
        print(f"Importing data from: '{file}':")
        if file.endswith(".json.gz"):
            in_file = gzip.open(file, "rb")
        elif file.endswith(".json"):
            in_file = open(file, "r")
        else:
            print("Incorrect File Format. Needs to be either .json or .json.gz file...")
        items = list(ijson.items(in_file, "item"))
        in_file.close()
        data = []
        size = len(items)
        with alive_bar(size) as bar:
            for item in items:
                data.append(template(item))
                bar()

        batch_index = [(batch_size * i, batch_size * (i + 1)) for i in range(size // batch_size + 1)]
        batch_num = len(batch_index)

        print(f"Migrating data from '{file}' to the {self.name} database:")
        with self.client.session(self.name, SessionType.DATA) as session:
            with alive_bar(batch_num) as bar:
                for x, y in batch_index:
                    with session.transaction(TransactionType.WRITE) as transaction:
                        for insert in data[x:y]:
                            transaction.query().insert(insert)
                        transaction.commit()
                    bar()

    def gene_template(self, input):
        insert = f'insert $gene isa Gene, '
        for key, value in input.items():
            try:
                value = int(value)
                insert += f'has {key} {value}, '
            except ValueError:
                insert += f'has {key} "{value}", '

        return insert[:-2] + ";"

    def genelink_template(self, input):
        insert = "match "
        for key, value in input.items():
            insert += f'${key} isa Gene, has Gene_Name "{value}";'
        insert += "insert (GeneA: $GeneA, GeneB: $GeneB) isa GeneLink;"

        return insert

    def query_str(self, query: str):
        print(f"Query:\n{query}")
        vars = get_vars(query=query)
        with self.client.session(self.name, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as transaction:
                iterator = transaction.query().match(query)

                results = [{var: res.get(var).get_value() for var in vars} for res in iterator]

        return results

    def query_tql(self, file: str = "./Data/getGeneNames.tql"):
        with open(file, "r") as in_file:
            query = in_file.read().replace("\n", "")
        return self.query_str(query=query)


def get_vars(query: str):
    vars = [var.lstrip(" get ") for var in query.split(";") if var.startswith(" get ")][0]
    vars = [var.lstrip("$") for var in vars.split(", ")]
    return vars


if __name__ == "__main__":
    with PangenomeDatabase("Spidermite") as Db:
        start_time = time.time()
        Db.create(replace=True)
        created_time = time.time()
        Db.migrate("./Data/Genes.json.gz", Db.gene_template)
        genes_time = time.time()
        Db.migrate("./Data/GeneLinks.json.gz", Db.genelink_template)
        genelinks_time = time.time()
        results = Db.query_tql("./Data/getGeneLinks.tql")
        query_time = time.time()
        Db.delete()
        delete_time = time.time()

    print("First query result:")
    print(results[0], end=", ...\n")

    print("\n+--------------------------+---------+")
    print(f"| Total execution time     | {timedelta(seconds=round(delete_time - start_time))} |")
    print("+--------------------------+---------+")
    print(f"| Database creation time   | {timedelta(seconds=round(created_time - start_time))} |")
    print("+--------------------------+---------+")
    print(f"| Genes migration time     | {timedelta(seconds=round(genes_time - created_time))} |")
    print("+--------------------------+---------+")
    print(f"| GeneLinks migration time | {timedelta(seconds=round(genelinks_time - genes_time))} |")
    print("+--------------------------+---------+")
    print(f"| Query time               | {timedelta(seconds=round(query_time - genelinks_time))} |")
    print("+--------------------------+---------+")
    print(f"| Database deletion time   | {timedelta(seconds=round(delete_time - query_time))} |")
    print("+--------------------------+---------+")
