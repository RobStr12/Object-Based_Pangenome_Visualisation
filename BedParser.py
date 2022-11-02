import json
from glob import glob


print("this is a test commit")

finalgenelist = []
linklist = []
for bedfile in glob("/Users/jannessauer/Downloads/Tetur_V4/Tetur_4_bed_LATEST/*.bed"):
    genelist = []
    for line in open(bedfile):
        line = line.rstrip().split("\t")
        #with open("/Users/jannessauer/Downloads/Tetur_V4/data.tql","a") as tqloutput:
            #tqloutput.write(f'insert $gene isa Gene,has Gene_Name "{line[3]}", has Start_Position "{line[1]}", has End_Position "{line[2]}", has Strand "{line[5]}", has Chromosome "{line[0]}";\n')
        Genedict = {"Chromosome": line[0], "Start_Position": line[1], "End_Position": line[2], "Gene_Name": line[3],
                    "Strand": line[5]}
        genelist.append(Genedict)
        finalgenelist.append(Genedict)

    n = 2
    for i in range(len(genelist) - n + 1):
        batch = genelist[i:i + n]
        gene1, gene2 = batch[0]['Gene_Name'], batch[1]['Gene_Name']
        Genelink = {"GeneA": gene1, "GeneB": gene2}
        linklist.append(Genelink)

with open("/Users/jannessauer/Downloads/Tetur_V4/Gene.json", "w") as jsonFile:
    json.dump(finalgenelist, jsonFile, indent=4, sort_keys=True)
jsonFile.close()

with open("/Users/jannessauer/Downloads/Tetur_V4/Genelinks.json", "w") as jsonFile:
    json.dump(linklist, jsonFile, indent=4, sort_keys=True)
jsonFile.close()