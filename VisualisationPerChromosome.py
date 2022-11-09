from PangenomeDatabaseClass import *
import igraph as ig

if __name__ == "__main__":
    with PangenomeDatabase("Spidermite") as spidermite:
        if not spidermite.exists():
            spidermite.create()
            spidermite.migrate(file="./Data/Genes.json.gz", template=spidermite.gene_template)
            spidermite.migrate(file="./Data/GeneLinks.json.gz", template=spidermite.genelink_template)
        GeneLinks = spidermite.query_tql("./Data/getGeneLinks.tql")
        Genes = spidermite.query_tql("./Data/getGeneNames.tql")
        vs_dict = {}
        graph = ig.Graph(directed=True, n=len(Genes))

        for i, gene in enumerate(Genes):
            graph.vs[0]["name"] = gene["name"]
            graph.vs[i]["chromosome"] = gene["chrom"]
            vs_dict[gene["name"]] = i

        edges = [[vs_dict[link["nameA"]], vs_dict[link["nameB"]]] for link in GeneLinks]
        graph.add_edges(edges)

        print(edges)

        ig.plot(graph, target=("./Data/plot.png"), bbox=(20000, 20000))

        with open("./Data/Genes_GeneLinks.gml", "w") as file:
            ig._write_graph_to_file(graph, file)
