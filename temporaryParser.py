import json
import gzip

with open("./Data/Genes.json", 'r') as f_in:
    Genes = json.load(f_in)

with open("./Data/Genelinks.json", "r") as f_in:
    GeneLinks = json.load(f_in)

with open("./Data/Clusters.json", "r") as f_in:
    data = json.load(f_in)
    Clusters = data["Clusters"]
    ClusterLinks = data["ClusterLinks"]

out = {"Genes": Genes, "GeneLinks": GeneLinks, "Clusters": Clusters, "ClusterLinks": ClusterLinks}

with gzip.open("./Data/Spider_mite.json.gz", "w") as f_out:
    f_out.write(json.dumps(out, indent=4).encode("utf-8"))
