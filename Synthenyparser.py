import json
from glob import glob
import pysam
from Bio.Seq import Seq
from Bio.Seq import translate
from Bio.Alphabet import IUPAC

linklist = []

for line in open("/Users/jannessauer/Downloads/pangenome_project/Tetli.collinearity"):
    if "#" in line:
        continue
    else:
        line = line.rstrip().split("\t")
        Genelink = {"GeneA": line[2], "GeneB": line[1]}
        print(Genelink)
        linklist.append(Genelink)

with open("/Users/jannessauer/Downloads/pangenome_project/Synthenylinks.json", "w") as jsonFile:
    json.dump(linklist, jsonFile, indent=4)
jsonFile.close()