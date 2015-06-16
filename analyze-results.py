#!/usr/bin/python

__author__ = 'secastro'

import json
from ripe.atlas.sagan import TracerouteResult
import argparse
import networkx as nx
import ipaddr
from collections import defaultdict
import re
import GeoIP
import itertools
from networkx.readwrite import json_graph
from reverse_lookup import ReverseLookupService
import random


probe_addr = dict()
g = GeoIP.open("data/GeoIPASNum.dat", GeoIP.GEOIP_STANDARD)

# Preload a list of known network that are not in the routing table
with open('data/known-networks.json', 'rb') as net_file:
    known_net = json.load(net_file)

    for prefix in known_net:
        # Replace the member with the object that represents an IPv4Network
        prefix['net'] = ipaddr.IPv4Network(prefix['net'])

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


def org_from_addr(a):
    """
    :type a: string
    :param a: string
    :return: string
    """
    org = g.org_by_name(a)
    if org is not None:
        return org.split(' ')[0][2:]
    else:
        # Last attempt to look into the list of networks we know
        for prefix in known_net:
            if ipaddr.IPv4Address(a) in prefix['net']:
                return prefix['group']

        # Last resort
        return "UNK"


def class_from_name(node):
    if re.search('^Hop', node):
        return [3, "X0"]
    elif re.search('^Private', node):
        return [2, "Priv"]
    elif re.search('^Probe', node):
        org = org_from_addr(probe_addr[node])
        return [1, org]
    else:
        try:
            if ipaddr.IPv4Address(node).version == 4:
                org = org_from_addr(node)
                return [4, org]
        except ipaddr.AddressValueError:
            return [4, "UNK"]


def invalid_group(g):
    return g in ['UNK', 'X0', 'Priv']


parser = argparse.ArgumentParser("Analyses results")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
parser.add_argument('--sample', help="Use a sample instead of all traces available", action="store_true")
args = parser.parse_args()

addr_list = set()
res_file = "{}/results.json".format(args.datadir)
ip_path_list = []

with open(res_file, 'rb') as res_fd:
    res_blob = json.load(res_fd)

    if args.sample:
        res_blob = random.sample(res_blob, 1000)

G = nx.Graph()
bgp = nx.Graph()
nodes = set()
edges = []

node_hops = defaultdict(set)
unknown_addr = set()
address_to_lookup = set()

for res in res_blob:
    sagan_res = TracerouteResult(res)

    print "Source = {}".format(sagan_res.source_address)
    print "Origin = {}".format(sagan_res.origin)
    address_to_lookup.add(sagan_res.origin)
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
    probe_addr["Probe %s" % sagan_res.probe_id] = sagan_res.origin

    # Identify the AS corresponding to each hop
    node_path = []
    # print "** PATH with errors"
    for i in range(0, len(clean_ip_path)):
        hop_elem = []
        for h in clean_ip_path[i]:
            name = name_hop(h, sagan_res.probe_id, i)
            [_c, grp] = class_from_name(name)
            if grp == 'UNK':
                unknown_addr.add(name)
            hop_elem.append(dict(name=name, _class=_c, group=grp))
            address_to_lookup.add(name)
            # print h, name, grp
        node_path.append(hop_elem)

    # Fill up the gaps where the AS obtained is not available
    last_good = dict(group=None, idx=0)
    invalid_in_path = False
    for i in range(0, len(node_path)):
        for hop in node_path[i]:
            if not invalid_group(hop['group']):
                if invalid_in_path and hop['group'] == last_good['group']:
                    # Repair the sequence between here and the last good
                    # print "** Attempting to repair index %s -> %s" % (last_good['idx']+1, i-1)
                    for j in range(last_good['idx']+1, i):
                        for hop_elem in node_path[j]:
                            # print "-- Changing %s by %s" % (hop_elem['group'], hop['group'])
                            if hop_elem['group'] in ['X0', 'Priv']:
                                hop_elem['group'] = hop['group']
                    invalid_in_path = False
                last_good = dict(group=hop['group'], idx=i)
            else:
                invalid_in_path = True

    # Third iteration
    # If there are still groups not determined, there is not much we can do to guess them,
    # so we extend the last good group to cover for those
    last_good_group = None
    clean_path = []
    for i in range(0, len(node_path)):
        for hop in node_path[i]:
            clean_path.append([hop['name'], hop['group']])
            if invalid_group(hop['group']):
                print "Pass3: Replace %s by %s" % (hop['group'], last_good_group)
                hop['group'] = last_good_group
            else:
                last_good_group = hop['group']

    temp_path = []
    for n1, n2 in itertools.izip(node_path, clean_path):
        print "{name:>20}  {group:>8}".format(**n1[0]), " | ", "{0[0]:>20}  {0[1]:>8}".format(n2)
        temp_path.append({'addr': n1[0]['name'], 'asn': n1[0]['group']})

    ip_path_list.append({'responded': sagan_res.destination_ip_responded, 'path': temp_path})

    """node_path now contains a sanitized version of the IP path"""
    for i in range(1, len(node_path)):
        for s in node_path[i - 1]:
            for d in node_path[i]:
                G.add_edge(s['name'], d['name'])
                if s['group'] != d['group']:
                    bgp.add_edge(s['group'], d['group'])
                G.node[s['name']]['group'] = s['group']
                G.node[d['name']]['group'] = d['group']
                G.node[s['name']]['_class'] = s['_class']
                G.node[d['name']]['_class'] = d['_class']

# print "Looking up reverse entries, might take a while"
# s = ReverseLookupService()
# address_info = s.lookup_many(address_to_lookup)

with open("{}/ip-path.json".format(args.datadir), 'wb') as ip_path_file:
    json.dump(ip_path_list, ip_path_file, indent=2)

with open("{}/addresses.json".format(args.datadir), 'wb') as addr_file:
    json.dump(list(addr_list), addr_file)

node_list = []
with open("{}/graph.json".format(args.datadir), 'wb') as graph_file:
    node_idx = dict()
    idx = 0
    groups = defaultdict(list)
    for n in G.nodes_iter():
        node_list.append({'name': n, 'label': n, 'id': n, '_class': G.node[n]['_class'], 'group': G.node[n]['group']})
        node_idx[n] = idx
        groups[G.node[n]['group']].append(idx)
        idx += 1
    json.dump(dict(links=[dict(source=node_idx[s], target=node_idx[t], weight=1) for s, t in G.edges_iter()],
                   nodes=node_list,
                   groups=[dict(leaves=m, name=grp, padding=10) for grp, m in groups.iteritems()]), graph_file)

with open("{}/ip-network-graph.js".format(args.datadir), "wb") as graph_file:
    graph_file.write("var nodes = {};\n".format(json.dumps(node_list)))
    edge_list = [{'to': t, 'from': s, 'width': 1} for s, t in G.edges_iter()]
    graph_file.write("var edges = {};\n".format(json.dumps(edge_list)))

# Save a version of IP graph in graphJSON
with open("{}/ip.json".format(args.datadir), 'wb') as ip_json_file:
    json.dump(json_graph.node_link_data(G), ip_json_file)

# Save a version in GraphML for gephi
nx.write_graphml(bgp, "{}/bgp.graphml".format(args.datadir))

# Save a version in graphJSON for Alchemy
with open("{}/bgp.json".format(args.datadir), 'wb') as bgp_json_file:
    json.dump(json_graph.node_link_data(bgp), bgp_json_file)

with open("{}/as-list.txt".format(args.datadir), 'wb') as as_list_file:
    as_list_file.writelines(["{0}\n".format(n) for n in bgp.nodes_iter()])

with open("{}/unmappable-addresses.txt".format(args.datadir), "wb") as unk_addr_file:
    unk_addr_file.writelines([addr + "\n" for addr in sorted(unknown_addr)])
