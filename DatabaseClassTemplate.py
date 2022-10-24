# Following class is just a template/inspiration for a more permanent class dealing with the Vaticle typeDB client API
from typedb.client import TypeDB, SessionType, TransactionType
from typedb.common.exception import TypeDBClientException
import ijson


class PangenomeGraphDatabase:

    # __init__, __enter__, and __exit__ functions
    def __init__(self, localhost: str, name: str):
        self.localhost = localhost
        self.name = name
        self.inputs = [
            {"file": "./Data/Genes.json", "template": self.gene_template},
            {"file": "./Data/Chromosomes.json", "template": self.chromosome_template},
            {"file": "./Data/Loci.json", "template": self.locus_template}
        ]

    def __enter__(self):
        self.client = TypeDB.core_client(self.localhost)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    # Basic class function for easier management and support of the class
    def exists(self):
        return self.client.databases().contains(self.name)

    def delete(self):
        self.client.databases().get(self.name).delete()

    def parser(self):
        for input in self.inputs:
            with open(input["file"], "r") as data:
                items = [input["template"](item) for item in ijson.items(data, "item")]
                self.migrate(items)

    # Define the template function that convert the inputs from the json file into typeQL insert statements
    def gene_template(self, input):
        insert = f'insert $gene isa gene, has seq_id "{input["seq_id"]}",'
        insert += f' has seq_length {input["length"]},'
        insert += f' has start_at {input["start-at"]};'
        return insert

    def chromosome_template(self, input):
        insert = f'insert $chromosome isa chromosome, has chr_id "{input["chr_id"]}",'
        insert += f' has chr_length {input["chr_length"]};'
        return insert

    def locus_template(self, input):
        insert = f'match $gene isa gene, has seq_id "{input["seq_id"]}";'
        insert += f' $chromosome isa chromosome, has chr_id "{input["chr_id"]}";'
        insert += f' insert (gene: $gene, chromosome: $chromosome) isa locus;'
        return insert

    # Define the create, migrate, and query functions for the actual database handling
    def create(self, path: str, replace: bool = None):
        # Check if database already exists
        exists = self.client.databases().contains(self.name)

        if (exists and replace) or (not exists):
            # If it does not exists, or it does and you want to replace it:
            print("(re-)create database")
            try:
                self.client.databases().get(self.name).delete()
            except TypeDBClientException:
                pass
            finally:
                self.client.databases().create(self.name)
                with open(path, "r") as schema:
                    query = schema.read().replace("\n", "")
                with self.client.session(self.name, SessionType.SCHEMA) as session:
                    with session.transaction(TransactionType.WRITE) as transaction:
                        transaction.query().define(query)
                        transaction.commit()

        elif replace is None:
            # If ity exists, ask if you want to replace it
            doReplace = bool(input("Database Already exists. Do you want to replace it? ").lower() == "y")
            if doReplace:
                self.create(path, True)

    def migrate(self, items):
        with self.client.session(self.name, SessionType.DATA) as session:
            with session.transaction(TransactionType.WRITE) as transaction:
                for item in items:
                    print(item)
                    transaction.query().insert(item)
                transaction.commit()

    def query(self, query):
        pass


if __name__ == "__main__":
    with PangenomeGraphDatabase("localhost:1729", "Spidermite") as db:
        db.create("./Data/DatabaseSchemaTemplate.tql", True)
        db.parser()
