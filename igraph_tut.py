import igraph as ig

ig.config["plotting.backend"] = "cairo"
ig.config.save()

g = ig.Graph([(0,1), (0,2), (2,3), (3,4), (4,2), (2,5), (5,0), (6,3), (5,6)])

g.vs["name"] = ["Alice", "Bob", "Claire", "Dennis", "Esther", "Frank", "George"]
g.vs["age"] = [25, 31, 18, 47, 22, 23, 50]
g.vs["gender"] = ["f", "m", "f", "m", "f", "m", "m"]
g.es["is_formal"] = [False, False, True, True, True, False, True, False, False]

g.vs["label"] = g.vs["name"]
color_dict = {"m": "blue", "f": "pink"}
layout = g.layout_kamada_kawai()

visual_style = {"vertex_size": 20, "vertex_color": [color_dict[gender] for gender in g.vs["gender"]],
                "vertex_label": g.vs["name"], "edge_width": [1 + 2 * int(is_formal) for is_formal in g.es["is_formal"]],
                "layout": layout, "bbox": (300, 300), "margin": 20}

ig.plot(g, **visual_style, target="./Data/plot.png")

dd = {"Alice": ["Bob"], "Bob": ["Dylan", "Charlie"], "Charlie": ["Eva"], "Dylan": ["Eva"], "Eva": ["Frans"]}

g = ig.Graph.ListDict(dd, directed=True, vertex_name_attr="label")

ig.plot(g, vertex_shape="rectangle", target="./Data/plot2.png")
