# Following class is just a template/inspiration for a more permanent class dealing with the Vaticle typeDB client API
from typedb.client import TypeDB, SessionType, TransactionType


class PangenomeGraphDatabase:

    def __init__(self, localhost: str, name: str):
        self.localhost = localhost
        self.name = name

    def __enter__(self):
        self.client = TypeDB.core_client(self.localhost)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def exists(self):
        return self.client.databases().contains(self.name)

    def create(self):
        self.client.databases().create(self.name)

    def delete(self):
        self.client.databases().get(self.name).delete()


if __name__ == "__main__":
    with PangenomeGraphDatabase("localhost:1729", "Spidermite") as db:
        print(db.exists())
        db.delete()
        print(db.exists())
