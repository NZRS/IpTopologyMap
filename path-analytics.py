__author__ = 'secastro'

import json
import argparse
from collections import Counter
import GeoIP
import re
from radix import Radix

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
    return "\n".join(["{0:>6} {1:>10} {2}".format(e.get('country', '**'), e['asn'], e['addr']) for e in p])


rt = Radix()
with open('data/known-networks.json', 'rb') as known_net_file:
    known_networks = json.load(known_net_file)

    for p in known_networks:
        # Only keep prefixes that we know their country
        if 'country' in p:
            n = rt.add(p['net'])
            n.data['cc'] = p['country']


parser = argparse.ArgumentParser("Analyses IP Path data")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
args = parser.parse_args()

gi = GeoIP.open('data/GeoIP.dat', GeoIP.GEOIP_STANDARD)
with open("{}/ip-path.json".format(args.datadir), 'rb') as ip_file:
    ip_path = json.load(ip_file)

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


deviated_cnt = Counter()
for path in ip_path:
    s = path['path'][0]
    t = path['path'][-1]

    if t['country'] == dest_cc:
        # Iterate the path and see if we depart from the destination country
        departed = False
        for hop in path['path']:
            departed |= hop['country'] not in [dest_cc, unk_cc]

        path['departed'] = departed
        if departed:
            deviated_cnt['off-country'] += 1
            print "=" * 20
            print path2string(path['path'])
            print "\n"
        else:
            deviated_cnt['in-country'] += 1

with open("{}/expanded-ip-path.json".format(args.datadir), 'wb') as o_file:
    json.dump(ip_path, o_file, indent=2)

# print ip_path
print completed
print deviated_cnt
