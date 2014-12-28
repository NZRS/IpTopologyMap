__author__ = 'secastro'

import json
from ripe.atlas.sagan import TracerouteResult
import argparse
import networkx as nx
import ipaddr
from collections import defaultdict
import re


def name_hop(node, probe_id, seq):
    if node == "unknown_hop":
        return "Hop %s-%s" % (probe_id, seq)

    try:
        if ipaddr.IPv4Address(node).is_private:
            return "Private %s-%s" % (probe_id, seq)
        else:
            return node
    except ipaddr.AddressValueError:
        return node


def group_from_name(node):
    if re.search('^Hop', node):
        return 3
    elif re.search('^Private', node):
        return 2
    elif re.search('^Probe', node):
        return 1
    else:
        return 4


parser = argparse.ArgumentParser("Analyses results")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
args = parser.parse_args()

addr_list = set()
res_file = "{}/results.json".format(args.datadir)

with open(res_file, 'rb') as res_fd:
    res_blob = json.load(res_fd)

G = nx.Graph()
nodes = set()
edges = []

node_hops = defaultdict(set)

for res in res_blob:
    sagan_res = TracerouteResult(res)

    print "Source = {}".format(sagan_res.source_address)
    addr_list.add(sagan_res.source_address)
    print "Destination = {}".format(sagan_res.destination_address)
    print "Hops = {}".format(sagan_res.total_hops)
    print "Destination responded = {}".format(sagan_res.destination_ip_responded)
    last_hop_detected = False
    clean_ip_path = []
    for ip_list in reversed(sagan_res.ip_path):
        addr_in_hop = set()
        for ip in ip_list:
            if ip is not None:
                addr_list.add(ip)
                addr_in_hop.add(ip)

        if len(addr_in_hop) == 0 and not last_hop_detected:
            # This is a hop that failed at the end of the path
            continue
        elif len(addr_in_hop) > 0:
            last_hop_detected = True

        # This hop was problematic, but it still part of the path
        if len(addr_in_hop) == 0:
            addr_in_hop_list = ["unknown_hop"]
        else:
            addr_in_hop_list = list(addr_in_hop)
        clean_ip_path.insert(0, addr_in_hop_list)

    clean_ip_path.insert(0, ["Probe %s" % sagan_res.probe_id])
    # clean_ip_path now contains a sanitized version of the IP path
    for i in range(1, len(clean_ip_path)):
        for s in clean_ip_path[i - 1]:
            for d in clean_ip_path[i]:
                new_s = name_hop(s, sagan_res.probe_id, i-1)
                new_d = name_hop(d, sagan_res.probe_id, i)
                G.add_edge(new_s, new_d)
                node_hops[new_s].add(i-1)
                node_hops[new_d].add(i)

# Add the degree to each node to prepare the layout later
for node_id, node_degree in G.degree_iter():
    G.node[node_id]['degree'] = max(node_hops.get(node_id))
    # G.node[node_id]['degree'] = node_degree

with open("{}/addresses.json".format(args.datadir), 'wb') as addr_file:
    json.dump(list(addr_list), addr_file)

# for key, value in node_hops.iteritems():
#     print key, value

with open("{}/graph.json".format(args.datadir), 'wb') as graph_file:
    node_idx = dict()
    node_list = []
    idx = 0
    for n in G.nodes_iter():
        node_list.append(dict(name=n, degree=G.node[n]['degree'], group=group_from_name(n)))
        node_idx[n] = idx
        idx += 1
    json.dump(dict(links=[dict(source=node_idx[s], target=node_idx[t], weight=1) for s, t in G.edges_iter()],
                   nodes=node_list), graph_file)
