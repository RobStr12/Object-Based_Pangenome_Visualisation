import json
from glob import glob
import pysam
from Bio.Seq import Seq
from Bio.Seq import translate
from Bio.Alphabet import IUPAC


def gettingGeneSeq(id, start, stop, inputfasta: str = "./Data/sequences.fasta"):
    fastref = pysam.FastaFile(inputfasta)
    seq = fastref.fetch(id, start, stop)
    return seq


# sequence = gettingGeneSeq(id="LG1",start=5,stop=12)
# print(sequence)
def translating(inputsequence):
    proteinseq = translate(inputsequence)
    return proteinseq


def parsingbedfile(inputfile):
    exondict = {}
    stranddict = {}
    for line in open(inputfile):
        line = line.rstrip().split("\t")
        type, start, stop, strand, name = line[2], line[3], line[4], line[6], line[8].split(".")[0].replace("ID=", "")
        stranddict[name] = strand
        if "E." in type:
            if name in exondict:
                exondict[name] = exondict[name] + f";{start}..{stop}"
            else:
                exondict[name] = f"{line[0]}+{start}..{stop}"
    return (exondict,stranddict)

def reversecomplement(inputsequence):
    my_dna = Seq(inputsequence, IUPAC.ambiguous_dna)
    complement = my_dna.reverse_complement()
    return(complement)



parsed_dictionary,stranddict = parsingbedfile("/Users/jannessauer/Downloads/Tetur_V4/Tetur_4_gff_LATEST/LG2.gff")
sequencelist = []
for key, value in parsed_dictionary.items():
    chrom = value.split("+")[0]
    positions = value.split("+")[1].split(";")
    sequence = ""
    for pos in positions:
        pos = pos.split("..")
        sequence = sequence + gettingGeneSeq(id=chrom, start=int(pos[0])-1, stop=int(pos[1]))
    if stranddict[key] == "-":
        rev = str(translating(reversecomplement(sequence)))
        sequencedict = {"gene": key, "sequence": rev}
    else:
        sequencedict = {"gene": key, "sequence": translating(sequence)}
    sequencelist.append(sequencedict)
print(sequencelist)
# sequence = gettingGeneSeq(id="LG1",start=5,stop=12)
# print(sequence)

def gettingGeneSeq(id, start, stop, inputfasta: str = "./Data/sequences.fasta"):
    fastref = pysam.FastaFile(inputfasta)
    seq = fastref.fetch(id, start, stop)
    return seq
#sequence = gettingGeneSeq(id="LG1",start=5,stop=12)
#print(sequence)
def translating(inputsequence):
    proteinseq = translate(inputsequence)
    return proteinseq


print("this is a test commit")

finalgenelist = []
linklist = []
sequencelist = []
for bedfile in glob("/Users/jannessauer/Downloads/Tetur_V4/Tetur_4_bed_LATEST/*.bed"):
    genelist = []
    for line in open(bedfile):
        line = line.rstrip().split("\t")
        # with open("/Users/jannessauer/Downloads/Tetur_V4/data.tql","a") as tqloutput:
        # tqloutput.write(f'insert $gene isa Gene,has Gene_Name "{line[3]}", has Start_Position "{line[1]}", has End_Position "{line[2]}", has Strand "{line[5]}", has Chromosome "{line[0]}";\n')
        Genedict = {"Chromosome": line[0], "Start_Position": line[1], "End_Position": line[2], "Gene_Name": line[3],
                    "Strand": line[5]}
        try:
            sequence = gettingGeneSeq(id=line[0], start=int(line[1]) - 1, stop=int(line[2]))
            sequencedict = {"gene": line[3], "sequence": translating(sequence)}
            sequencelist.append(sequencedict)
        except:
            continue
        genelist.append(Genedict)
        finalgenelist.append(Genedict)

    n = 2
    for i in range(len(genelist) - n + 1):
        batch = genelist[i:i + n]
        gene1, gene2 = batch[0]['Gene_Name'], batch[1]['Gene_Name']
        Genelink = {"GeneA": gene1, "GeneB": gene2}
        linklist.append(Genelink)

with open("/Users/jannessauer/Downloads/Tetur_V4/Gene.json", "w") as jsonFile:
    json.dump(finalgenelist, jsonFile, indent=4)
jsonFile.close()

with open("/Users/jannessauer/Downloads/Tetur_V4/Genelinks.json", "w") as jsonFile:
    json.dump(linklist, jsonFile, indent=4)
jsonFile.close()

with open("/Users/jannessauer/Downloads/Tetur_V4/proteinsequences.json", "w") as jsonFile:
    json.dump(sequencelist, jsonFile, indent=4)
jsonFile.close()

