__author__ = 'secastro'

import csv
import re
import networkx as nx
import json


def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


G = nx.Graph()

with open('/Users/secastro/Downloads/links.csv', 'rb') as l_file:
    csv_r = csv.reader(l_file)

    for r, p, l, c in csv_r:
        if is_valid_hostname(p) and is_valid_hostname(l):
            G.add_edge(p, l, weight=c)

node_idx = dict()
node_list = []
idx = 0
for n in G.nodes_iter():
    node_list.append(dict(name=n))
    node_idx[n] = idx
    idx += 1

nx.write_dot(G, "web.dot")
with open('web-for-viz.json', 'wb') as graph_file:
    json.dump(
        dict(links=[dict(source=node_idx[s], target=node_idx[t], weight=a['weight']) for s, t, a in G.edges_iter(data=True)],
             nodes=node_list), graph_file)

