# Following class is just a template/inspiration for a more permanent class dealing with the Vaticle typeDB client API
from typedb.client import TypeDB, SessionType, TransactionType
from typedb.common.exception import TypeDBClientException
import ijson
import subprocess


class PangenomeGraphDatabase:

    # __init__, __enter__, and __exit__ functions
    def __init__(self, name: str):
        self.name = name
        self.inputs = [
            {"file": "./Data/Genes.json", "template": self.gene_template},
            {"file": "./Data/Chromosomes.json", "template": self.chromosome_template},
            {"file": "./Data/Loci.json", "template": self.locus_template}
        ]
        self.relations = {"locus": ["gene", "chromosome"]}

    def __enter__(self):
        self.server = subprocess.Popen("typedb.bat server")
        self.client = TypeDB.core_client("localhost:1729")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        self.server.terminate()

    # Basic class function for easier management and support of the class
    def exists(self):
        return self.client.databases().contains(self.name)

    def delete(self):
        self.client.databases().get(self.name).delete()

    # Parsers for different data types
    def json_parser(self):
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
        with self.client.session(self.name, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as transaction:
                iterator = transaction.query().match(query[0])

                result = [res.get(query[1]).get_value() for res in iterator]
                return result

    # Define Crude(!!!) Query templates and Generator
    # These crude templates can serve as inspiration or buidling blocks of more complex queries
    # and query generators.
    def entity_query_template(self, entity: str):
        return f'${entity} isa {entity}'

    def relation_query_template(self, relation: str):
        e1 = self.relations[relation][0]
        e2 = self.relations[relation][1]
        return f"${relation}({e1}: ${e1}, {e2}: ${e2}) isa {relation}"

    def attribute_query_template(self, entity, attribute):
        return self.entity_query_template(entity) + f", has {attribute} ${attribute}"

    def example_crude_query_generator(self):
        query = "match "
        query += self.attribute_query_template("chromosome", "chr_id") + "; "
        query += self.relation_query_template("locus") + "; "
        query += "get $chr_id;"
        return [query, "chr_id"]

if __name__ == "__main__":
    with PangenomeGraphDatabase("Spidermite") as db:
        query = db.example_crude_query_generator()
        print(f"Query:\n{query[0]}\nResults:\n{db.query(query)}")

