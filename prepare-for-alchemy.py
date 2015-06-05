__author__ = 'secastro'

import json
import networkx as nx
from collections import defaultdict
from networkx.readwrite import json_graph
from time import strftime, localtime
from asn_name_lookup import AsnNameLookupService
import argparse
from as_relationship import AsRelationshipService

parser = argparse.ArgumentParser("Prepare graph file for visualization")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
parser.add_argument('--relfile', required=True, help="File with AS relationship data")
args = parser.parse_args()


with open("{}/bgp.json".format(args.datadir), 'rb') as bgp_file:
    map_data = json.load(bgp_file)
    # bgp_map = nx.Graph(map_data)
    bgp_map = json_graph.node_link_graph(map_data)

s = AsnNameLookupService()
as_info = s.lookup_many([node for node in bgp_map.nodes_iter()])

with open('data/base-as-info.json', 'rb') as base_as_info_file:
    base_info = json.load(base_as_info_file)
    as_info.update(base_info)


degree_set = defaultdict(set)
# Go over the list of nodes and add the degree attribute
for node_deg in bgp_map.degree_iter():
    [asn, degree] = node_deg
    bgp_map.node[asn]['degree'] = degree
    bgp_map.node[asn]['upstream'] = bgp_map.neighbors(asn)[0] if degree == 1 else asn
    # If I have info for this ASN and no info has been recorded before
    if as_info.has_key(asn) and not bgp_map.node[asn].has_key('name'):
        bgp_map.node[asn]['name'] = as_info[asn]['short_descr']
        bgp_map.node[asn]['descr'] = as_info[asn]['long_descr']
        # Add a group based on the country for all nodes
        bgp_map.node[asn]['country'] = as_info[asn]['country'] if as_info[asn]['country'] in ['NZ', 'AU', 'IX'] else 'other'

    degree_set[bgp_map.node[asn]['country']].add(node_deg[1])

degree_range = []
for country in degree_set:
    print "Country = {0}".format(country)
    print "Max = {0}, Min = {1}".format(max(degree_set[country]), min(degree_set[country]))
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
