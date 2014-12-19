__author__ = 'secastro'

import json
from ripe.atlas.sagan import TracerouteResult
import argparse

parser = argparse.ArgumentParser("Analyses results")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
args = parser.parse_args()

addr_list = set()
res_file = "{}/results.json".format(args.datadir)

with open(res_file, 'rb') as res_fd:
    res_blob = json.load(res_fd)

nodes = set()
edges = []

for res in res_blob:
    sagan_res = TracerouteResult(res)

    print "Source = {}".format(sagan_res.source_address)
    addr_list.add(sagan_res.source_address)
    print "Destination = {}".format(sagan_res.destination_address)
    print "Hops = {}".format(sagan_res.total_hops)
    print "Destination responded = {}".format(sagan_res.destination_ip_responded)
    last_hop_detected = False
    clean_ip_path = []
    hop_cnt = sagan_res.total_hops
    for ip_list in reversed(sagan_res.ip_path):
        addr_in_hop = set()
        for ip in ip_list:
            if ip is not None:
                addr_list.add(ip)
                addr_in_hop.add(ip)

        hop_cnt -= 1
        if len(addr_in_hop) == 0 and not last_hop_detected:
            # This is a hop that failed at the end of the path
            continue
        elif len(addr_in_hop) > 0:
            last_hop_detected = True

        # This hop was problematic, but it still part of the path
        if len(addr_in_hop) == 0:
            addr_in_hop_list = ["Hop %s-%s" % (sagan_res.probe_id, hop_cnt)]
        else:
            addr_in_hop_list = list(addr_in_hop)
        clean_ip_path.insert(0, addr_in_hop_list)

    clean_ip_path.insert(0, ["Probe %s" % sagan_res.probe_id])
    # clean_ip_path now contains a sanitized version of the IP path
    print clean_ip_path
    for i in range(1, len(clean_ip_path)):
        for s in clean_ip_path[i-1]:
            for d in clean_ip_path[i]:
                nodes.add(s)
                edges.append(dict(data=dict(weight=1, source=s, target=d)))


with open("{}/addresses.json".format(args.datadir), 'wb') as addr_file:
    json.dump(list(addr_list), addr_file)

with open("{}/graph.json".format(args.datadir), 'wb') as graph_file:
    json.dump(dict(edges=edges, nodes=[dict(data=dict(id=n)) for n in nodes]), graph_file)
