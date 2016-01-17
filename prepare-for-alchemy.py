__author__ = 'secastro'

import json
import networkx as nx
from collections import defaultdict
from networkx.readwrite import json_graph
from time import strftime, localtime
from asn_name_lookup import AsnNameLookupService
import argparse
from as_relationship import AsRelationshipService
import os

parser = argparse.ArgumentParser("Prepare graph file for visualization")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
parser.add_argument('--relfile', required=True, help="File with AS relationship data")
args = parser.parse_args()


with open("{}/bgp.json".format(args.datadir), 'rb') as bgp_file:
    map_data = json.load(bgp_file)
    # print(json.dumps(map_data, indent=2))
    # bgp_map = nx.Graph(map_data)
    bgp_map = json_graph.node_link_graph(map_data)

s = AsnNameLookupService()
as_info = s.lookup_many([node for node in bgp_map.nodes_iter()])

with open('data/base-as-info.json', 'rb') as base_as_info_file:
    base_info = json.load(base_as_info_file)
    as_info.update(base_info)

# Save the collected AS info if needed for inspectin
with open(os.path.join(args.datadir, 'as-info.json'), 'wb') as as_file:
    json.dump(as_info, as_file, indent=2)

degree_set = defaultdict(set)
# Go over the list of nodes and add the degree attribute
for node_deg in bgp_map.degree_iter():
    [asn, degree] = node_deg
    asn_str = str(asn)
    bgp_map.node[asn]['degree'] = degree
    bgp_map.node[asn]['upstream'] = bgp_map.neighbors(asn)[0] if degree == 1 else asn
    # If I have info for this ASN and no info has been recorded before
    if asn_str in as_info and 'name' not in bgp_map.node[asn]:
        bgp_map.node[asn]['name'] = as_info[asn_str]['short_descr']
        bgp_map.node[asn]['descr'] = as_info[asn_str]['long_descr']
        # Add a group based on the country for all nodes
        bgp_map.node[asn]['country'] = as_info[asn_str]['country'] if as_info[asn_str]['country'] in ['NZ', 'AU', 'IX'] else 'other'

    if 'country' in bgp_map.node[asn]:
        degree_set[bgp_map.node[asn]['country']].add(node_deg[1])
    else:
        print("** ASN %s has incomplete information: %s" % (asn,
                                                            bgp_map.node[asn]))

degree_range = []
for country in degree_set:
    print("Country = {0}".format(country))
    print("Max = {0}, Min = {1}".format(max(degree_set[country]), min(degree_set[country])))
    degree_range.append(dict(country=country, min=min(degree_set[country]), max=max(degree_set[country])))


json_dump = json_graph.node_link_data(bgp_map)
for node in json_dump['nodes']:
    node['id'] = int(node['id'])

s = AsRelationshipService([args.relfile])
for link in json_dump['links']:
    link['_weight'] = 1
    link['source'] = json_dump['nodes'][link['source']]['id']
    link['target'] = json_dump['nodes'][link['target']]['id']
    link['_class'] = s.rel_char2class(s.find_rel(link['source'], link['target']))

json_dump['edges'] = json_dump['links']
json_dump['dr'] = degree_range
json_dump['wr'] = [1, 1]
json_dump['lastupdate'] = strftime("%B %d, %Y", localtime())
del json_dump['links']


with open("{}/bgp.alchemy.json".format(args.datadir), 'wb') as alchemy_file:
    json.dump(json_dump, alchemy_file)


# Save a version of the BGP map for VisJS
with open(os.path.join(args.datadir, 'vis-bgp-graph.js'), 'wb') as vis_file:
    bgp_nodes = {}
    for n in json_dump['nodes']:
        bgp_nodes[n['id']] = {'label': n['name'], 'group': n['country'],
                              'degree': n['degree']}

    node_idx = {}
    idx = 0
    for n in bgp_nodes.iterkeys():
        node_idx[n] = idx
        idx += 1

    bgp_edges = []
    for edge in json_dump['edges']:
        if edge['target'] != edge['source']:
            bgp_edges.append({'to': node_idx[edge['target']],
                              'from': node_idx[edge['source']],
                              'width': 1})

    vis_file.write("var nodes = {};\n".format(
        json.dumps([{'id': node_idx[n],
                     'label': v['label'],
                     'group': v['group'],
                     'value': v['degree']} for n, v in bgp_nodes.iteritems()])))
    vis_file.write("var edges = {};\n".format(json.dumps(bgp_edges)))
