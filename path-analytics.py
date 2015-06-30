__author__ = 'secastro'

import json
import argparse
from collections import Counter
import GeoIP
import re
from radix import Radix
from operator import itemgetter

dest_cc = 'NZ'
unk_cc  = '*'

def get_country(addr, asn):
    """Force an exception with Vocus"""
    if asn in ['9560']:
        return 'NZ'
    else:
        n = rt.search_best(network=addr, masklen=32)
        if n is not None:
            return n.data['cc']
        else:
            return gi.country_code_by_addr(elem['addr'])

def path2string(p):
    return "\n".join(["{0:>6} {1:>10} {2:15} {3:.2f}".format(e.get('country', '++'), e['asn'], e['addr'], e['rtt']) for e in p])
    # return "\n".join(["{country:>6} {asn:>10} {addr}".format(e) for e in p])

rt = Radix()
with open('data/known-networks.json', 'rb') as known_net_file:
    known_networks = json.load(known_net_file)

    for p in known_networks:
        # Only keep prefixes that we know their country
        if 'country' in p:
            n = rt.add(p['net'])
            n.data['cc'] = p['country']

# parses command-line arguments
parser = argparse.ArgumentParser("Analyses IP Path data")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
args = parser.parse_args()

# set up geoip and load the traced paths
gi = GeoIP.open('data/GeoIP.dat', GeoIP.GEOIP_STANDARD)
with open("{}/ip-path.json".format(args.datadir), 'rb') as ip_file:
    ip_path = json.load(ip_file)

# figure out country for each node along the path
completed = Counter()
for path in ip_path:
    completed['yes' if path['responded'] else 'no'] += 1
    for elem in path['path']:
        if re.match("Probe", elem['addr']):
            elem['country'] = 'NZ'
        elif re.match('Private', elem['addr']) or re.match('Hop', elem['addr']):
            elem['country'] = unk_cc
        else:
            elem['country'] = get_country(elem['addr'], elem['asn'])

# count deviation
deviated_cnt = Counter()
common_deviated_target = Counter()
deviated_path = []
deviated_hops = {}
hop_switches = []

for path in ip_path:
    origin = path['path'][0]
    goal = path['path'][-1]

    # only look at traces within the same country
    if goal['country'] != dest_cc: continue


for path in ip_path:
    s, t = path['path'][0], path['path'][-1]
    addr_origin, addr_goal = s['addr'], t['addr']

    if t['country'] == dest_cc:

        # Iterate the path and see if we depart from the destination country
        departed = False
        prev_cc, prev_ip = dest_cc, None

        for hop in path['path']:

            # check for hops from nz to another country
            cc = hop['country']
            if cc not in [dest_cc, unk_cc] and prev_cc in [dest_cc]:
                hop_switches.append({ 'overseas_addr' : hop['addr'],
                                      'asn' : hop['asn'],
                                      'country' : hop['country'],
                                      'prev_addr' : prev_ip,
                                      'origin' : origin['addr'],
                                      'goal' : goal['addr'] })
            prev_ip = hop['addr']
            prev_cc = cc

            # record hops in another country
            if hop['country'] not in [dest_cc, unk_cc]:
                departed |= True
                deviated_hops[hop['addr']] = dict((k, hop[k]) for k in hop.iterkeys() if k in ['country', 'asn'])

        path['departed'] = departed
        if departed:
            deviated_cnt['off-country'] += 1
            common_deviated_target[t['addr']] += 1
            deviated_path.append(path2string(path['path']))
        else:
            deviated_cnt['in-country'] += 1

with open("{}/expanded-ip-path.json".format(args.datadir), 'wb') as o_file:
    json.dump(ip_path, o_file, indent=2)

with open("{}/deviated-hops.json".format(args.datadir), 'wb') as o_file:
    json.dump(deviated_hops, o_file, indent=2)

with open("{}/deviated-paths.txt".format(args.datadir), 'wb') as p_file:
    p_file.writelines([l + "\n\n" for l in deviated_path])

with open("{}/hop-switches.json".format(args.datadir), 'wb') as o_file:
    json.dump(hop_switches, o_file, indent=2)

# print ip_path
print completed
print deviated_cnt
print "Common target with deviated paths"
for k, v in sorted(common_deviated_target.items(), key=itemgetter(1), reverse=True):
    print k, v
