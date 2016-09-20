import argparse
import json
import os

"""
merge-network-layout.py

Takes two files: long-format-map.json and node-position.json and generates a
third file with the network representation with the layout location included
in advance.
"""

parser = argparse.ArgumentParser("Combines network representation with "
                                 "calculated node layout")
parser.add_argument('--datadir', required=True,
                    help="directory to read input and save output")
args = parser.parse_args()


with open(os.path.join(args.datadir, 'vis-bgp-graph.json')) as f1,\
        open(os.path.join(args.datadir, 'node-position.json')) as f2:
    network = json.load(f1)
    pos = json.load(f2)

for node in network['nodes']:
    node['id'] = str(node['id'])
    if node['id'] in pos:
        node['x_pos'] = pos[node['id']]['x']
        node['y_pos'] = pos[node['id']]['y']
    else:
        print("WARN: Node %s doesn't have position" % node['id'])

with open(os.path.join(args.datadir, 'full-network.json'), 'wb') as f:
    json.dump(network, f)



