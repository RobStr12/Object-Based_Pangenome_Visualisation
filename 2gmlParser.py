from PangenomeDatabaseClass import *
import igraph as ig

with PangenomeDatabase("Spidermite") as pdb:
    if not pdb.exists():
        pdb.create()
        pdb.migrate("./Data/Genes.json.gz", pdb.gene_template)
        pdb.migrate("./Data/GeneLinks.json.gz", pdb.genelink_template)

    genes = pdb.query_tql("./Data/getGeneNames.tql")
    genelinks = pdb.query_tql("./Data/getGeneLinks.tql")

    vs_genes = {gene["name"]: i for i, gene in enumerate(genes)}
    edges = [[vs_genes[link["nameA"]], vs_genes[link["nameB"]]] for link in genelinks]

    graph = ig.Graph(directed=True, n=len(genes), edges=edges)

    for gene in genes:
        name = gene["name"]
        chrom = gene["chrom"]
        i = vs_genes[name]

        graph.vs[i]["name"] = name
        graph.vs[i]["chromosome"] = chrom

    with open("./Data/Genes_GeneLinks.gml", "w") as file:
        ig._write_graph_to_file(graph, file)

    ig.plot(graph, target=("./Data/plot.png"), bbox=(20000, 20000))
