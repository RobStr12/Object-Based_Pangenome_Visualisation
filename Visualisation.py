from PangenomeDatabaseClass import *
from igraph import Graph, plot


if __name__ == "__main__":
    with PangenomeDatabase("Spidermite") as PgDb:
        if not PgDb.exists():
            PgDb.create()
            PgDb.migrate(file="./Data/Genes.json.gz", template=PgDb.gene_template, batch_size=5000)
            PgDb.migrate(file="./Data/GeneLinks.json.gz", template=PgDb.genelink_template, batch_size=5000)
        genes = PgDb.query_tql()

        GeneLinks = {gene: PgDb.query(query=f'match $gA isa Gene, has Gene_Name "{gene}";'
                                              f' $gB isa Gene, has Gene_Name $B;'
                                              f' (GeneA: $gA, GeneB: $gB) isa GeneLink; get $B;', get="B") for gene in genes[:1000]}
        print(GeneLinks)

        print("Generating Graph...")
        g = Graph.ListDict(GeneLinks, directed=True)
        g.vs["label"] = genes
        grid = g.layout_grid()
        graphopt = g.layout_graphopt()
        reingold_tilford = g.layout_reingold_tilford()

        print("Plotting Graph...")
        plot(g, layout=grid, target="./Data/plot_grid.png", bbox=(20000, 20000))
        plot(g, layout=graphopt, target="./Data/plot_graphopt.png", bbox=(20000, 20000))
        plot(g, layout=reingold_tilford, target="./Data/plot_reingold_tilford.png", bbox=(20000, 20000))
