from typedb.client import TypeDB, SessionType, TransactionType
from typedb.common.exception import TypeDBClientException
from alive_progress import alive_bar
from datetime import timedelta
from subprocess import Popen
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
        self.server = Popen("server.sh server")
        self.client = TypeDB.core_client("localhost:1730")

    def close(self):
        # close the client & terminate the server
        self.client.close()
        self.server.terminate()

        # in order to be able to delete, change, ... certain files in the server folder, the OpenJDK Platfrom binary
        # needs to be shut down. To accomplish this, following code is implemented. When initialising the class again,
        # The OpenJDK Platform binary will restart again on its own.
        for process in (process for process in psutil.process_iter() if process.name()=="java.exe"):
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

    def migrate(self, file: str, template, batch_size: int = 2000):
        print(f"Importing data from: '{file}':")
        with gzip.open(file, "rb") as in_file:
            # data = [template(item) for item in ijson.items(in_file, "item")]
            items = list(ijson.items(in_file, "item"))
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

    def query(self, query: str = "./Data/getGeneNames.tql"):
        with self.client.session(self.name, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as transaction:
                with open(query, 'r') as query:
                    query = query.read().replace("\n", "")

                iterator = transaction.query().match(query)
                get = query.split("$")[-1].rstrip(";")

                results = [res.get(get).get_value() for res in iterator]

        return results


if __name__ == "__main__":
    with PangenomeDatabase("Spidermite") as Db:
        start_time = time.time()
        Db.create(replace=True)
        created_time = time.time()
        Db.migrate("./Data/Genes.json.gz", Db.gene_template)
        genes_time = time.time()
        Db.migrate("./Data/GeneLinks.json.gz", Db.genelink_template)
        genelinks_time = time.time()
        results = Db.query()
        query_time = time.time()
        Db.delete()
        delete_time = time.time()

    print(f"\nTotal execution time: {timedelta(seconds=(delete_time - start_time))}\n")
    print(f"Database creation time: {timedelta(seconds=(created_time - start_time))}\n")
    print(f"Genes migration time: {timedelta(seconds=(genes_time - created_time))}\n")
    print(f"GeneLinks migration time: {timedelta(seconds=(genelinks_time - genes_time))}\n")
    print(f"Query time: {timedelta(seconds=(query_time - genelinks_time))}\n")
    print(f"Database deletion time: {timedelta(seconds=(delete_time - query_time))}\n")
