from typedb.client import TypeDB, SessionType, TransactionType
from typedb.common.exception import TypeDBClientException
from alive_progress import alive_bar
from subprocess import Popen
from sys import platform
import psutil
import ijson
import json
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
    return vars


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
    insert = f'insert $cluster isa Cluster, has Cluster_Name "{input["Cluster_Name"]}", has Cluster_Type "{input["Cluster_Type"]}";'
    return insert


def genelink_template(input):
    insert = "match "
    insert += f'$GeneA isa Gene, has Gene_Name "{input["GeneA"]}";'
    insert += f'$GeneB isa Gene, has Gene_Name "{input["GeneB"]}";'
    insert += f'insert (GeneA: $GeneA, GeneB: $GeneB) isa GeneLink, has GeneLink_Type "{input["GeneLink_Type"]}";'
    return insert


def clusterlink_template(input):
    if input["ClusterLink_Type"] == "Cluster->Gene":
        child = "Gene"
    else:
        child = "Cluster"

    insert = f'match $parent isa Cluster, has Cluster_Name "{input["Parent_Name"]}"; '
    insert += f' $child isa {child}, has {child}_Name "{input["Child_Name"]}"; '
    insert += f'insert (Parent: $parent, Child: $child) isa ClusterLink, has ClusterLink_Type "{input["ClusterLink_Type"]}";'

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
            migrating = f"Migrating from list to {self.name}..."
        elif type(insert) == dict:
            print(f"Fetching inserts from dict...")
            items = fetch_data([insert], template)
            migrating = f"Migrating from dict to {self.name}"
        elif insert.endswith(".json") or insert.endswith(".json.gz"):
            print(f"Fetching inserts from {insert}...")
            inserts = getInsert(insert)
            items = fetch_data(inserts, template)
            migrating = f"Migrating inserts from {insert} to {self.name}..."
        elif "insert" in insert:
            print(f"Fetching inserts from string...")
            items = [insert]
            migrating = f"Migrating insert {insert} to {self.name}"
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

    def cluster(self, name: str, type: str, query: str):
        # Step 1: Check inputs + load external outputs
        # Step 1.1: Inputs
        print("Checking Type input...")
        c_types = ["Genome", "Chromosome", "ProteinFamily", "GeneCluster", "Other"]
        if type not in c_types:
            print("Incorrect Cluster Type...")
            return

        # Step 1.2:outputs
        path = "./Data/Clusters.json"
        try:
            with open(path, "r") as f_in:
                file = json.load(f_in)
        except FileNotFoundError:
            file = {"Clusters": [], "ClusterLinks": []}

        # Step 2: Create Cluster + add to Clusters.json
        new = {"Cluster_Name": name, "Cluster_Type": type}
        file["Clusters"].append(new)
        self.migrate(new, cluster_template)

        # Step 3: Query database
        results = self.query(query)
        genes = [result["gene_name"] for result in results]

        # Step 4: Create ClusterLinks of type Cluster->Gene
        links = [{"Parent_Name": name, "Child_Name": gene, "ClusterLink_Type": "Cluster->Gene"} for gene in genes]

        # Step 5: Checking if cluster is parent or child
        # Step 5.1: retrieving all clusters
        clusters = [cluster["cluster_name"] for cluster in self.query("./Data/getClusters.tql")]
        print(clusters)

        # Step 5.2: find parent-child clusters
        for cluster in clusters:
            # Step 5.2.1: Check to compare different clusters
            if cluster == name:
                continue

            # Step 5.2.2: Get genes from other cluster
            q = f'match $cluster isa Cluster, has Cluster_Name "{cluster}"; ' \
                f'$gene isa Gene, has Gene_Name $gene_name; ' \
                f'(Parent: $cluster, Child: $gene) isa ClusterLink; ' \
                f'get $gene_name;'
            results = self.query(q)
            cluster_genes = [gene["gene_name"] for gene in results]

            # Step 5.2.3: Compare clusters
            if len(genes) > len(cluster_genes):
                parent, child, p_genes, c_genes = name, cluster, genes, cluster_genes
            elif len(genes) < len(cluster_genes):
                parent, child, p_genes, c_genes = cluster, name, cluster_genes, genes
            elif set(genes) == set(cluster_genes):
                print(f"{name} is the same cluster as {cluster}...")
            else:
                continue

            print(f"comparing  parent cluster {parent} and child cluster {child}")
            equal = []
            with alive_bar(len(c_genes)) as bar:
                for gene in c_genes:
                    equal.append(gene in p_genes)
                    bar()

            if any(equal):
                print(f'{parent} is a parent cluster of {child}')
                relation = {"Parent_Name": parent, "Child_Name": child, "ClusterLink_Type": "Cluster->Cluster"}
                links.append(relation)
                file["ClusterLinks"].append(relation)
            else:
                print(f'{parent} is not a parent cluster of {child}')

        # Step 6 migrate links
        self.migrate(links, clusterlink_template)

        # Export file
        with open("./Data/Clusters.json", "w") as f_out:
            json.dump(file, f_out)


if __name__ == "__main__":
    with PangenomeDatabase("Spider mite", "schema.tql") as PDb:
        PDb.migrate("./Data/Genes.json", gene_template)
        PDb.migrate("./Data/GeneLinks.json", genelink_template)

        PDb.cluster("All", "Other", "./Data/getGenes.tql")
        PDb.cluster("Tetur", "Genome", """match $gene isa Gene, has Gene_Name $gene_name, has Genome "Tetur"; get $gene_name;""")
        PDb.cluster("Tetli", "Genome",
                    """match $gene isa Gene, has Gene_Name $gene_name, has Genome "Tetli"; get $gene_name;""")
