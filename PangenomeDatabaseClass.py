from typedb.client import TypeDB, SessionType, TransactionType
from typedb.common.exception import TypeDBClientException
from alive_progress import alive_bar
from subprocess import Popen
from sys import platform
import psutil
import ijson
import gzip
import os


def getInsert(file: str):
    if file.endswith(".json"):
        f_in = open(file, "r")
    else:
        f_in = gzip.open(file, "r")
    return list(ijson.items(f_in, "item"))


def get_vars(query: str):
    vars = [var.lstrip(" get ") for var in query.split(";") if var.startswith(" get ")][0]
    vars = [var.lstrip("$") for var in vars.split(", ")]
    return


def fetch_data(inserts, template):
    items = []
    with alive_bar(len(inserts)) as bar:
        for ins in inserts:
            items.append(template(ins))
            bar()
    return items


def gene_template(input):
    insert = f'insert $gene isa Gene, '
    for key, value in input.items():
        try:
            value = int(value)
            insert += f'has {key} {value}, '
        except ValueError:
            insert += f'has {key} "{value}", '

    return insert[:-2] + ";"


def cluster_template(input):
    insert = f'insert $cluster isa Cluster, has Cluster_Name {input["cluster_name"]}'
    return insert


def genelink_template(input):
    insert = "match "
    for key, value in input.items():
        insert += f'${key} isa Gene, has Gene_Name "{value}";'
    insert += "insert (GeneA: $GeneA, GeneB: $GeneB) isa GeneLink;"

    return insert


def cluster_gene_link_template(input):
    insert = f'match $gene isa Gene, has Gene_Name "{input["gene_name"]}";' \
             f' $cluster isa Cluster, has Cluster_Name "{input["cluster_name"]}";' \
             f' insert (Parent: $cluster, Child: $gene) isa ClusterLink, has Cluster_Link_Type "Cluster->Gene";'
    return insert


def cluster_cluster_link_template(input):
    insert = f'match $child isa Gene, has Gene_Name "{input["child_name"]}";' \
             f' $parent isa Cluster, has Cluster_Name "{input["parent_name"]}";' \
             f' insert (Parent: $parent, Child: $child) isa ClusterLink, has Cluster_Link_Type "Cluster->Cluster";'
    return insert


class PangenomeDatabase:

    def __init__(self, name: str, schema: str, kill_java: bool = True, replace: bool = True):

        # Initialize variables & possible missing paths
        self.name = name
        self.schema = "./Data/" + schema
        self.kill_java = kill_java

        path = "./server/data"
        if not os.path.isdir(path):
            os.mkdir(path)

        # Initialize server, client, and sessions
        if platform == "win32":
            self.server = Popen("server.bat")
        self.client = TypeDB.core_client("localhost:1730")

        # Create Database
        self.create(replace)

        self.session = self.client.session(self.name, SessionType.DATA)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.session.close()
        self.client.close()

        # in order to be able to delete, change, ... certain files in the server folder, the OpenJDK Platform binary
        # needs to be shut down. To accomplish this, following code is implemented. When initialising the class again,
        # The OpenJDK Platform binary will restart again on its own.
        for process in (process for process in psutil.process_iter() if process.name() == "java.exe"):
            if self.kill_java:
                process.kill()

        if platform == "win32":
            self.server.terminate()

    def delete(self):
        self.client.databases().get(self.name).delete()

    def create(self, replace: bool):
        if replace:
            try:
                self.delete()
                print("Deleting Database...")
                print("Recreating Database...")
            except TypeDBClientException:
                print("Creating Database...")
            finally:
                self.client.databases().create(self.name)
                with open(self.schema, "r") as f_in:
                    define = f_in.read().replace("\n", "")
                with self.client.session(self.name, SessionType.SCHEMA) as session:
                    with session.transaction(TransactionType.WRITE) as transaction:
                        transaction.query().define(define)
                        transaction.commit()
        elif self.client.databases().contains(self.name) and replace is None:
            i = input("Do you want to replace the existing database? [y/n]: ").lower()
            self.create(replace=(i == "y"))
        elif replace is None:
            self.create(replace=True)
        else:
            print("Database already exists...")

    def migrate(self, insert, template=None, batch_size: int = 5000):
        if type(insert) == list:
            print(f"Fetching inserts from list...")
            items = fetch_data(insert, template)
        elif type(insert) == dict:
            print(f"Fetching inserts from dict...")
            items = fetch_data([insert], template)
        elif insert.endswith(".json") or insert.endswith(".json.gz"):
            print(f"Fetching inserts from {insert}...")
            inserts = getInsert(insert)
            items = fetch_data(inserts, template)
            migrating = f"Migrating inserts from {insert} to {self.name}..."
        elif "insert" in insert:
            print(f"Fetching inserts from string...")
            items = [insert]
            migrating = f"Migrating insert to {self.name}"
        else:
            print("[Cannot migrate data]")
            return

        size = len(items)
        batch_index = [(batch_size * i, batch_size * (i + 1)) for i in range(size // batch_size + 1)]
        batch_num = len(batch_index)

        print(migrating)
        with alive_bar(batch_num) as bar:
            for x, y in batch_index:
                with self.session.transaction(TransactionType.WRITE) as transaction:
                    for item in items[x:y]:
                        transaction.query().insert(item)
                    transaction.commit()
                bar()

    def query(self, query: str):
        if query.endswith(".tql"):
            with open(query, "r") as f_in:
                query = f_in.read().replace("\n", "")
        print("Query:")
        print(query)

        vars = get_vars(query)

        with self.session.transaction(TransactionType.READ) as transaction:
            iterator = transaction.query().match(query)

            results = [{var: res.get(var).get_value() for var in vars} for res in iterator]

        return results


with PangenomeDatabase("Spider mite", "schema.tql") as PDb:
    PDb.migrate("./Data/Gene.json", gene_template)
