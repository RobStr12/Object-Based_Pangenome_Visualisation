from PangenomeDatabaseClass import *
from datetime import timedelta
import time



def get_query(input):
    return f'match $gene isa Gene, has {input["attr"]} "{input["name"]}", has Gene_Name $gene_name; get $gene_name;'

start_time = time.time()

with PangenomeDatabase("Spider mite", "schema.tql") as PDb:
    print("++==============================================++")
    print("||                Migrating Data                ||")
    print("++==============================================++")
    PDb.migrate("./Data/Genes.json", gene_template)
    PDb.migrate("./Data/GeneLinks.json", genelink_template)

    print("++==============================================++")
    print("||               Defining Clusters              ||")
    print("++==============================================++")

    clusters = [{"attr": "Genome", "name": genome["genome"]}
                for genome in PDb.query("match $gene isa Gene, has Genome $genome; get $genome;")]
    clusters.extend([{"attr": "Chromosome", "name": chromosome["chromosome"]}
                     for chromosome in PDb.query("match $gene isa Gene, has Chromosome $chromosome; get $chromosome;")])

    size = len(clusters)

    print("||")
    print(f"|| In total: <{size}> are to be created...")
    print("||")

    print("++==============================================++")
    print("||                Clustering Data               ||")
    print("++==============================================++")

    for i, cluster in enumerate(clusters):
        name = cluster["name"]
        type = cluster["attr"]
        query = get_query(cluster)
        PDb.cluster(name, type, query)
        print(f"{i + 1}/{len(clusters)} clustered")

    print("++==============================================++")
    print("||                Save Database                 ||")
    print("++==============================================++")

    PDb.save()

end_time = time.time()

print("++==============================================++")
print("||                   Summary                    ||")
print("++==============================================++")

print("")
print(f"It took this script {timedelta(seconds=(end_time - start_time))} to load the database, define the {size} clusters, and cluster them...")
