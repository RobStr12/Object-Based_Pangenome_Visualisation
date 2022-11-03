import igraph as ig

g = ig.Graph(n=9, edges=[[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [3, 6], [4, 6], [5, 7], [6, 8], [7, 8]])
layout = g.layout_reingold_tilford(root=[0])

g.vs["label"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

ig.plot(g, layout=layout, target="./Data/RgTf.png")
