# Object-based pangenome visualisation: design project 2022-20023

This is a github for the code for our design project.

## Setting up pycharm

You can find everything you need to know about how to link this git repository to your pycharm IDE in the follwoing link:

https://www.jetbrains.com/help/pycharm/github.html

First, you need to have your github account logged in into pycharm. The above website gives you multiple ways to do this

Once you are a collaborator, you can clone the repository into pycharm and start working on it!

## The BedParser

Jannes, when you are ready, can you document your parser here?

## The PangenomeDatabase class

***PangenomeDatabase(name: str)***

Initializes the class, which needs a name (str).

### PangenomeDatabase.start()

Checks if ./server/data exists, and makes the dir if not. Starts both the server (address: localhost:1730) and the client.

### PangenomeDatabase.close()

Close the server, client, and OpenJDK Platform binary.

### PangenomeDatabase.exists()

Checks if the database exists.

### PangenomeDatabase.delete()

Tries to delete the database. If the database does not exist in the first place, it will output "database does not exist...".

### PangenomeDatabase.create(replace: bool = False, file: str = "./Data/schema.tql")

Creates the database. If the database already exists, the replace value will determine if the existing database should be overwritten.

The path to the .tql file containing the database schema should be given to the file argument.

### PangenomeDatabase.migrate(file: str, template, batch_size: int = 2000)
