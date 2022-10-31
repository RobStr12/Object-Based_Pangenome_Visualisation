from PangenomeDatabaseClass import PangenomeDatabase
import matplotlib.pyplot as plt
import igraph as ig

if __name__ == "__main__":
    with PangenomeDatabase("Spidermite") as Db:
        results = Db.query()[:1000]
        print(results)

    Graph = ig.Graph()
    Graph.add_vertices(len(results))
    Graph.vs["name"] = results

    layout = Graph.layout()
    fig, ax = plt.subplots()
    ig.plot(Graph, layout=layout, target=ax)
    plt.show()
