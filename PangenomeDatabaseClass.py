from typedb.client import TypeDB, SessionType, TransactionType
import subprocess
import os


class PangenomeDatabase:

    def __init__(self, name: str):

        # Initialize class variables
        self.name = name
        self.server = None
        self.client = None

    def __enter__(self):
        # open server locally + start client
        self.openServer()
        self.client = TypeDB.core_client("localhost:1729")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # exit from client + terminate server
        self.client.close()
        self.server.terminate()

    def openServer(self):
        typedb_home = os.getcwd()
        g_cp = f"{typedb_home}/server/conf/;{typedb_home}/server/lib/common/*;{typedb_home}/server/lib/prod/*"
        command = f'java %SERVER_JAVAOPTS% -cp "{g_cp}" -Dtypedb.dir="{typedb_home}" com.vaticle.typedb.core.server.TypeDBServer %2 %3 %4 %5 %6 %7 %8 %9'
        self.server = subprocess.Popen(command)

    def session(self):
        with self.client.session(self.name, SessionType.SCHEMA) as session:
            return session


if __name__ == "__main__":
    with PangenomeDatabase("Spidermite") as PDB:
        session = PDB.session()
        print("OK")
