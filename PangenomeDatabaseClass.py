from typedb.client import TypeDB, SessionType, TransactionType
from typedb.common.exception import TypeDBClientException
from subprocess import Popen


class PangenomeDatabase:

    def __init__(self, name: str):
        # Initialize all variables
        self.name = name
        self.server = None
        self.client = None

    def __enter__(self):
        self.server = Popen("server.bat")
        self.client = TypeDB.core_client("localhost:1730")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        self.server.terminate()

    def exists(self):
        return self.client.databases().contains("self.name")

    def delete(self):
        self.client.databases().get(self.name).delete()

    def create(self, replace: bool = True):

        if replace is True:

            print("(Re-)Creating Database")

            try:
                self.delete()
            except TypeDBClientException:
                pass
            finally:
                self.client.databases().create(self.name)
                with open("./Data/schema.tql", "r") as schema:
                    query = schema.read().replace("\n", "")
                with self.client.session(self.name, SessionType.SCHEMA) as session:
                    with session.transaction(TransactionType.WRITE) as transaction:
                        transaction.query().define(query)
                        transaction.commit()

    def migrate(self):
        pass

    def query(self, query: str):
        pass

if __name__ == "__main__":
    with PangenomeDatabase("Spidermite") as PDB:
        PDB.delete()
