import json
import igraph
from collections import defaultdict
from networkx.readwrite import json_graph
from time import strftime, localtime
from asn_name_lookup import AsnNameLookupService
import argparse
import as_relationship.parser as asrp
import as_relationship.fetcher as asrf
import os
import pycountry

__author__ = 'secastro'

parser = argparse.ArgumentParser("Prepare graph file for visualization")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
args = parser.parse_args()

"""Load the configuration file with the list of countries we are interested"""
with open(os.path.join(args.datadir, 'config.json')) as f:
    config = json.load(f)

countries = set(config['PrimaryCountry'] + config['SecondaryCountry'] + ['IX'])

with open("{}/bgp.json".format(args.datadir), 'rb') as bgp_file:
    map_data = json.load(bgp_file)
    bgp_map = json_graph.node_link_graph(map_data)

# Annotate the bgp_map metadata with the names of the countries
bgp_map.graph['metadata']['PriCountry'] = ", ".join([pycountry.countries.get(
    alpha2=c).name for c in config['PrimaryCountry']])
bgp_map.graph['metadata']['SecCountry'] = ", ".join([pycountry.countries.get(
    alpha2=c).name for c in config['SecondaryCountry']])


as_info = {}
with open('data/base-as-info.json', 'rb') as base_as_info_file:
    base_info = json.load(base_as_info_file)
    as_info.update(base_info)

with open(os.path.join(args.datadir, 'collected-as-info.json')) as f:
    collected_info = json.load(f)
    as_info.update(collected_info)

with open(os.path.join(args.datadir, 'as-info.pre.json'), 'wb') as as_file:
    json.dump(as_info, as_file, indent=2, sort_keys=True)

# TODO: Exclude from the list of lookups ASNs for which we do have
# TODO: information in one way or other
s = AsnNameLookupService()
nodes_in_map = set([str(node) for node in bgp_map.nodes_iter()])
nodes_with_info = set([k for k, v in as_info.items()
                       if v.get('complete', True)])
print("INFO: ASes in map %s" % nodes_in_map)
print("INFO: ASes with info %s" % nodes_with_info)
ases_to_look = nodes_in_map - nodes_with_info
print("INFO: AS info to lookup: %s" % ases_to_look)
as_lookup_info = s.lookup_many(ases_to_look)

as_info.update(as_lookup_info)

# Save the collected AS info if needed for inspecting
with open(os.path.join(args.datadir, 'as-info.json'), 'wb') as as_file:
    json.dump(as_info, as_file, indent=2, sort_keys=True)

# AS Relationship data from CAIDA
as_rel_file = asrf.get_as_relationship_file(datadir=args.datadir)
as_rel = asrp.AsRelationship(as_rel_file)
tier1 = as_rel.tier1_asn()

degree_set = defaultdict(set)
# Go over the list of nodes and add the degree attribute
for node_deg in bgp_map.degree_iter():
    [asn, degree] = node_deg
    asn_str = str(asn)
    bgp_map.node[asn]['degree'] = degree
    bgp_map.node[asn]['upstream'] = bgp_map.neighbors(asn)[0] \
        if degree == 1 else asn
    # If I have info for this ASN and no info has been recorded before
    if asn_str in as_info and 'name' not in bgp_map.node[asn]:
        bgp_map.node[asn]['name'] = as_info[asn_str]['short_descr']
        bgp_map.node[asn]['descr'] = as_info[asn_str]['long_descr']
        bgp_map.node[asn]['ASN'] = asn_str
        # Add a group based on the country for all nodes
        bgp_map.node[asn]['country'] = as_info[asn_str]['country']
        if asn_str in tier1:
            print "Found a Tier1 %s" % asn_str
            bgp_map.node[asn]['group'] = 'tier1'
        else:
            bgp_map.node[asn]['group'] = as_info[asn_str]['country'] if \
                as_info[asn_str]['country'] in countries else 'other'
    else:
        if asn_str not in as_info:
            print("** Couldn't lookup %s" % asn_str)
        if 'name' in bgp_map.node[asn]:
            print("** Node with info %s" % asn)

    if 'group' in bgp_map.node[asn]:
        degree_set[bgp_map.node[asn]['group']].add(node_deg[1])
    else:
        print("** ASN %s has incomplete information: %s" % (asn,
                                                            bgp_map.node[asn]))

degree_range = []
for country in degree_set:
    print("Country = {0}".format(country))
    print("Max = {0}, Min = {1}".format(max(degree_set[country]), min(degree_set[country])))
    degree_range.append(dict(country=country, min=min(degree_set[country]), max=max(degree_set[country])))

VG = igraph.Graph.Formula()

json_dump = json_graph.node_link_data(bgp_map)
n_idx = {}
for node in json_dump['nodes']:
    node['id'] = int(node['id'])
    n_idx[node['id']] = VG.vcount()
    VG.add_vertex({'name': node['id'], 'label': node['id']})

for link in json_dump['links']:
    link['_weight'] = 1
    link['source'] = json_dump['nodes'][link['source']]['id']
    link['target'] = json_dump['nodes'][link['target']]['id']
    link['_class'] = as_rel.rel2class(link['source'], link['target'])
    VG.add_edge(n_idx[link['source']], n_idx[link['target']])

layout = VG.layout("large")
print layout.boundaries()
(bx, by) = layout.boundaries()
cx = (bx[0] + (bx[1] - bx[0])/2)
cy = (by[0] + (by[1] - by[0])/2)
print "Centroid X: ", cx
print "Centroid Y: ", cy
# layout.center(p=[cx, cy])
# print layout.boundaries()
layout.scale(scale=30)


# Add the calculated position to the existing graph representation
for node in json_dump['nodes']:
    idx = n_idx[node['id']]
    node['x'] = layout[idx][0]
    node['y'] = layout[idx][1]

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
        bgp_nodes[n['id']] = {'label': n['name'],
                              'descr': n['descr'],
                              'group': n['group'],
                              'ASN': n['ASN'],
                              'country': n['country'],
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
                              'width': 1,
                              'pairs': edge['pairs']})

    nodes_export = [{'id': node_idx[n],
                     'label': v['label'],
                     'descr': v['descr'],
                     'group': v['group'],
                     'country': v['country'],
                     'ASN': v['ASN'],
                     'value': v['degree']} for n, v in bgp_nodes.iteritems()]
    vis_file.write("var nodes = {};\n".format(json.dumps(nodes_export)))
    vis_file.write("var edges = {};\n".format(json.dumps(bgp_edges)))
    vis_file.write("var metadata = {};\n".format(json.dumps(bgp_map.graph['metadata'])))

# Generate the same data but exported in JSON format
with open(os.path.join(args.datadir, 'vis-bgp-graph.json'), 'wb') as json_file:
    json.dump({'metadata': bgp_map.graph['metadata'],
               'nodes': nodes_export,
               'edges': bgp_edges}, json_file)
