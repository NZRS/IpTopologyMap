#!/usr/bin/python

__author__ = 'secastro'

import json
from ripe.atlas.sagan import TracerouteResult
import argparse
import networkx as nx
import ipaddr
from collections import defaultdict, Counter
import re
import GeoIP
import itertools
from networkx.readwrite import json_graph
from reverse_lookup import ReverseLookupService
import random
import os
import datetime
from radix import Radix


probe_addr = dict()
g = GeoIP.open("data/GeoIPASNum.dat", GeoIP.GEOIP_STANDARD)
remapped_addr = {}
rt = Radix()
net_idx = {}
known_as = {}


def dpath(fname):
    return os.path.join(args.datadir, fname)


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

    # First, we try this source which is a list of curated networks plus
    # information from PeeringDB. We want to identify IXs first
    entry = rt.search_best(network=a, masklen=32)
    if entry is not None:
        try:
            # We know something about this AS, save the information for
            # later use
            ne = net_idx[entry.prefix]
            known_as[ne['ASN']] = {'country': ne['country'],
                                   'short_descr': ne['name'],
                                   'long_descr': ne['long_name'],
                                   'complete': ne['complete']}
            return ne['ASN']
        except KeyError as e:
            print("ERROR: Matching prefix %s for address %s is "
                  "inconsistent: %s (%s)" % (entry.prefix, a, e,
                                             ne['source']))
    else:
        # Second, we try the list of mapped addresses, which come from RIPE
        if a in remapped_addr:
            return remapped_addr[a]
        else:
            # Third, we use GeoIP
            org = g.org_by_name(a)
            if org is not None:
                return org.split(' ')[0][2:]

    # Last resort
    return "UNK"


def class_from_name(node):
    if re.search('^Hop', node):
        return [3, "X0"]
    elif re.search('^Private', node):
        return [2, "Priv"]
    elif re.search('^Probe', node):
        # Try to use the probe info first
        if node in probe_info:
            return [1, str(probe_info[node]['asn_v4'])]
        else:
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


def ip_link(src, tgt):
    """
    :param src: String representation of an IP address
    :param tgt: String representation of an IP address
    :return: String representation of an IP link, where source and target
    addresses are ordered
    """
    return " - ".join(sorted([src, tgt]))


def valid_percent(s):
    v = float(s)
    if v < 0.01 or v > 100:
        raise argparse.ArgumentTypeError("sample value out of range [0.01, 100]")

    return v

parser = argparse.ArgumentParser("Analyses results")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
parser.add_argument('--sample', required=True, type=valid_percent,
                    help="Use a sample instead of all traces available")
parser.add_argument('-v', required=False, action='store_true',
                    help="Be more verbose")
args = parser.parse_args()

# Preload a list of known network that are not in the routing table
with open('data/known-networks.json', 'rb') as net_file:
    known_networks = json.load(net_file)

    for entry in known_networks:
        rt.add(network=entry['net'])
        net_idx[entry['net']] = {'ASN': entry['group'],
                                 'name': entry['group'],
                                 'country': entry.get('country', ''),
                                 'long_name': entry['group'],
                                 'complete': False,
                                 'source': 'config'}

# Preload a list of addresses that are not mapped by GeoIP
remapped_file = dpath('remapped-addresses.json')
if os.path.exists(remapped_file):
    with open(remapped_file) as f:
        remapped_addr = json.load(f)

# Preload the information we have from PeeringDB
with open(dpath('peeringdb-dump.json')) as f:
    ix_info = json.load(f)

    # Iterate over the list and build a route table
    for ix in ix_info:
        for ixpfx in ix['ixpfx']:
            rt.add(network=ixpfx)
            net_idx[ixpfx] = {'ASN': ix['rs_asn'],
                              'country': 'IX',
                              'name': ix['name'],
                              'long_name': ix['name_long'],
                              'complete': True,
                              'source': 'pdb'}


addr_list = set()
ip_path_list = []
probe_info = {}
cc_set = set()

with open(dpath("results.json"), 'rb') as res_fd:
    res_blob = json.load(res_fd)

    if args.sample:
        for cc, cc_res in res_blob.iteritems():
            cc_set.add(cc)
            sample_sz = int((args.sample/100)*len(cc_res))
            print("INFO: Picking sample {} of {} for country {}".format(
                sample_sz, len(cc_res), cc))
            res_blob[cc] = random.sample(cc_res, sample_sz)

# Preload information about the probes used
with open(dpath('probes.json'), 'rb') as probe_file:
    probe_data = json.load(probe_file)

    # Iterate over the list and generate a dict hashed by the id
    for cc, cc_probe_list in probe_data.iteritems():
        for info in cc_probe_list:
            probe_info['Probe %s' % info['id']] = {k: v for k, v in info.items() if k != 'id'}

G = nx.Graph()
bgp = nx.Graph(metadata={'probes_num': len(probe_info),
                         'country': list(cc_set),
                         'tracert_num': sum([len(v) for v in
                                             res_blob.itervalues()])})
nodes = set()
edges = []

node_hops = defaultdict(set)
unknown_addr = set()
address_to_lookup = set()

for cc, res_set in res_blob.iteritems():
    for res in res_set:
        sagan_res = TracerouteResult(res)

        if args.v:
            print("Source = %s" % sagan_res.source_address)
            print("Origin = %s" % sagan_res.origin)
            print("Destination = %s" % sagan_res.destination_address)
            print("Hops = %s" % sagan_res.total_hops)
            print("Destination responded = %s" % sagan_res.destination_ip_responded)
        address_to_lookup.add(sagan_res.origin)
        addr_list.add(sagan_res.source_address)
        last_hop_detected = False
        clean_ip_path = []
        for hop in reversed(sagan_res.hops):
            rtt_sum = Counter()
            rtt_cnt = Counter()
            rtt_avg = {}

            for packet in hop.packets:
                if packet.origin is None:
                    continue

                if packet.rtt is not None:
                    rtt_sum[packet.origin] += packet.rtt
                    rtt_cnt[packet.origin] += 1

            addr_in_hop = set()
            for addr in rtt_cnt:
                addr_list.add(addr)
                addr_in_hop.add(addr)
                rtt_avg[addr] = rtt_sum[addr] / rtt_cnt[addr]

            if len(addr_in_hop) == 0 and not last_hop_detected:
                # This is a hop that failed at the end of the path
                continue
            elif len(addr_in_hop) > 0:
                last_hop_detected = True

            # This hop was problematic, but it still part of the path
            if len(addr_in_hop) == 0:
                addr_in_hop_list = {'index': hop.index, 'hop_info': [{'addr': "unknown_hop", 'rtt': 0.0}]}
            else:
                addr_in_hop_list = {'index': hop.index, 'hop_info': [{'addr': k, 'rtt': v} for k, v in rtt_avg.items()]}
            clean_ip_path.insert(0, addr_in_hop_list)

        clean_ip_path.insert(0, {'index': 0, 'hop_info': [{'addr': "Probe %s" % sagan_res.probe_id, 'rtt': 0.0}]})
        probe_addr["Probe %s" % sagan_res.probe_id] = sagan_res.origin

        # Identify the AS corresponding to each hop
        node_path = []
        # print "** PATH with errors"
        for hop in clean_ip_path:
            hop_elem = []
            for probe in hop['hop_info']:
                name = name_hop(probe['addr'], sagan_res.probe_id, hop['index'])
                [_c, grp] = class_from_name(name)
                if grp == 'UNK':
                    unknown_addr.add(name)
                hop_elem.append({'name': name, '_class': _c, 'group': grp, 'rtt': probe['rtt']})
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
                    if args.v:
                        print("Pass3: Replace %s by %s" % (hop['group'], last_good_group))
                    hop['group'] = last_good_group
                else:
                    last_good_group = hop['group']

        temp_path = []
        for n1, n2 in zip(node_path, clean_path):
            # print("{name:>20}  {group:>8}".format(**n1[0]), " | ", "{0[0]:>20}  {0[1]:>8}".format(n2))
            if args.v:
                print("{0[0]:>20}  {0[1]:>8}".format(n2), " | ",
                      "{name:>20}  {group:>8}".format(**n1[0]))
            temp_path.append({'addr': n1[0]['name'], 'asn': n1[0]['group'], 'rtt': n1[0]['rtt']})

        ip_path_list.append({'responded': sagan_res.destination_ip_responded, 'path': temp_path})

        """node_path now contains a sanitized version of the IP path"""
        for i in range(1, len(node_path)):
            for s in node_path[i - 1]:
                for d in node_path[i]:
                    G.add_edge(s['name'], d['name'])
                    if s['group'] != d['group']:
                        # This link is across different ASes, add it to the BGP
                        # representation
                        if bgp.has_edge(s['group'], d['group']):
                            pairs = bgp[s['group']][d['group']]['pairs']
                            pairs.add(ip_link(s['name'], d['name']))
                        else:
                            pairs = set([ip_link(s['name'], d['name'])])

                        # Attribute pairs holds a set of IP links that constitute
                        #  this AS relationship. Intended to be used to track
                        # where organizations peer
                        bgp.add_edge(s['group'], d['group'], pairs=pairs)
                    if s['group'] is None:
                        print("** Node %s has NULL group" % s)
                    if d['group'] is None:
                        print("** Node %s has NULL group" % d)

                    G.node[s['name']]['group'] = s['group']
                    G.node[d['name']]['group'] = d['group']
                    G.node[s['name']]['_class'] = s['_class']
                    G.node[d['name']]['_class'] = d['_class']

# print "Looking up reverse entries, might take a while"
# s = ReverseLookupService()
# address_info = s.lookup_many(address_to_lookup)

with open(dpath("ip-path.json"), 'wb') as ip_path_file:
    json.dump(ip_path_list, ip_path_file, indent=2)

with open(dpath("addresses.json"), 'wb') as addr_file:
    json.dump(list(addr_list), addr_file)

node_list = []
with open(dpath("graph.json"), 'wb') as graph_file:
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
                   groups=[dict(leaves=m, name=grp, padding=10) for grp, m in groups.items()]), graph_file)

with open(dpath("ip-network-graph.js"), "wb") as graph_file:
    graph_file.write("var nodes = {};\n".format(json.dumps(node_list)))
    edge_list = [{'to': t, 'from': s, 'width': 1} for s, t in G.edges_iter()]
    graph_file.write("var edges = {};\n".format(json.dumps(edge_list)))

# Save a version of IP graph in graphJSON
with open(dpath("ip.json"), 'wb') as ip_json_file:
    json.dump(json_graph.node_link_data(G), ip_json_file)

# Save a version in GraphML for gephi
# nx.write_graphml(bgp, "{}/bgp.graphml".format(args.datadir))

# Save a version in graphJSON for Alchemy
# This graph has an attribute 'pairs' that's a set, needs to be transformed
# before dumping it
for s, t, d in bgp.edges_iter(data=True):
    bgp[s][t]['pairs'] = [p for p in d['pairs']]

# Add the date of generation to the metadata in the BGP view
bgp.graph['metadata']['updated'] = str(datetime.date.today())
with open(dpath('bgp.json'), 'wb') as bgp_json_file, \
        open(dpath('bgp-node-seq.json'), 'wb') as f2:
    _tmp_repr = json_graph.node_link_data(bgp)
    json.dump(_tmp_repr, bgp_json_file)
    json.dump([(i, _tmp_repr['nodes'][i]) for i in range(0, len(_tmp_repr[
                                                                'nodes']))], f2)


with open(dpath("as-list.txt"), 'wb') as as_list_file:
    as_list_file.writelines(["{0}\n".format(n) for n in bgp.nodes_iter()])

with open(dpath('unmappable-addresses.txt'), "wb") as unk_addr_file:
    unk_addr_file.writelines([addr + "\n" for addr in sorted(unknown_addr)])

with open(dpath('collected-as-info.json'), 'wb') as f:
    json.dump(known_as, f)
