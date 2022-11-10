import igraph as ig
from sklearn.preprocessing import LabelEncoder

G = ig.Graph.Read_GML('/Users/jannessauer/Downloads/Genes_GeneLinks.gml_kopie')
labels = list(G.vs)
N = len(labels)
E = [e.tuple for e in G.es]  # list of edges

labels=[]
group=[]


for node in G.vs:
    labels.append(node['name'])
    group.append(node['chromosome'])
print(group)

le = LabelEncoder()
group = le.fit_transform(group)

layt = G.layout('fr')  # kamada-kawai layout
type(layt)

import chart_studio.plotly as py
from plotly.graph_objs import *
import plotly.offline as pyoff

Xn = [layt[k][0] for k in range(N)]
Yn = [layt[k][1] for k in range(N)]
Xe = []
Ye = []
for e in E:
    Xe += [layt[e[0]][0], layt[e[1]][0], None]
    Ye += [layt[e[0]][1], layt[e[1]][1], None]

trace1 = Scatter(x=Xe,
                 y=Ye,
                 mode='lines',
                 line=dict(color='rgb(210,210,210)', width=1),
                 hoverinfo='none'
                 )
trace2 = Scatter(x=Xn,
                 y=Yn,
                 mode='markers',
                 name='ntw',
                 marker=dict(symbol='circle',
                             size=5,
                             color=group,
                             colorscale='spectral',
                             line=dict(color='rgb(50,50,50)', width=0.5)
                             ),
                 text=labels,
                 hoverinfo='text'
                 )

axis = dict(showline=False,  # hide axis line, grid, ticklabels and  title
            zeroline=False,
            showgrid=False,
            showticklabels=False,
            title=''
            )

width = 800
height = 800
layout = Layout(title="Pangenome Project",
                font=dict(size=12),
                showlegend=False,
                autosize=False,
                width=width,
                height=height,
                xaxis=layout.XAxis(axis),
                yaxis=layout.YAxis(axis),
                margin=layout.Margin(
                    l=40,
                    r=40,
                    b=85,
                    t=100,
                ),
                hovermode='closest',
                annotations=[
                    dict(
                        showarrow=False,
                        text='This igraph.Graph has the Kamada-Kawai layout',
                        xref='paper',
                        yref='paper',
                        x=0,
                        y=-0.1,
                        xanchor='left',
                        yanchor='bottom',
                        font=dict(
                            size=14
                        )
                    )
                ]
                )

data = [trace1, trace2]
fig = Figure(data=data, layout=layout)
pyoff.iplot(fig, filename='Pangenome')
