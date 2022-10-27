from typedb.client import TypeDB, SessionType, TransactionType
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

    def create(self):
        pass

    def migrate(self):
        pass

    def query(self):
        pass


