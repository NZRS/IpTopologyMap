__author__ = 'secastro'

import igraph
import json
import argparse

parser = argparse.ArgumentParser("Converts GraphJSON to VisJS graph representation")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
args = parser.parse_args()

with open("{}/ip.json".format(args.datadir)) as ip_file:
    graph_json_dump = json.load(ip_file)

# Preparing for vis.js format
## Create a graph using igraph
VG = igraph.Graph.Formula()

idx = 0
n_idx = {}
for n in graph_json_dump['nodes']:
    n_idx[n['id']] = VG.vcount()
    VG.add_vertex(name=n['id'], label=n['id'], group=n['_class'], AS=n['group'])

for e in graph_json_dump['links']:
    # print "{} -> {}".format(e['source'], e['target'])
    # print [v['name'] for v in VG.vs.select(name=e['source'])]
    # print [v['name'] for v in VG.vs.select(name=e['target'])]
    VG.add_edge(e['source'], e['target'])


layout = VG.layout("kk", dim=2)

vis_nodes = []
vis_edges = []
vis_ases = []
for n in VG.vs:
    vis_nodes.append({'id': n['name'], 'group': n['group'], 'title': '', 'AS': n['AS'],
                      'label': n['label'], 'x': 200*layout[n.index][0], 'y': 200*layout[n.index][1]})
    vis_ases.append(n['AS'])

for e in VG.es:
    vis_edges.append({'to': VG.vs[e.target]['name'], 'from': VG.vs[e.source]['name']})

with open("{}/ip-network-graph.js".format(args.datadir), 'wb') as js_file:
    js_file.write("var nodes = {};\n".format(json.dumps(vis_nodes)))
    js_file.write("var edges = {};\n".format(json.dumps(vis_edges)))
    js_file.write("var ases  = {};\n".format(json.dumps(vis_ases)))

