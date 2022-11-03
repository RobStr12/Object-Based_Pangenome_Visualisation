from PangenomeDatabaseClass import *
import igraph as ig

if __name__ == "__main__":
    with PangenomeDatabase("Spidermite") as spidermite:
        if not spidermite.exists():
            spidermite.create()
            spidermite.migrate(file="./Data/Genes.json.gz", template=spidermite.gene_template)
            spidermite.migrate(file="./Data/GeneLinks.json.gz", template=spidermite.genelink_template)
        GeneLinks = spidermite.query_tql("./Data/getGeneLinks.tql")
