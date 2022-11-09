from PangenomeDatabaseClass import *

with PangenomeDatabase("Spidermite") as PDb:
    if not PDb.exists():
        PDb.create()
        PDb.migrate("./Data/Genes.json.gz", gene_template)
        PDb.migrate("./Data/GeneLinks.json.gz", genelink_template)

    chromosomes = [chrom["chromosome"] for chrom in PDb.query_tql("./Data/getChromosomes.tql")]
    PDb.cluster("Tetur", "Genome", "./Data/getGeneNames.tql")

    for chromosome in chromosomes:
        query = f"""match $gene isa Gene, has Gene_Name $name, has Chromosome "{chromosome}"; get $name;"""
        PDb.cluster(chromosome, "Chromosome", query)
