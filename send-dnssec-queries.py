__author__ = 'secastro'

import json
import urllib2
import sys
import argparse
import os
import time


def read_auth(filename):
    with open(filename, 'rb') as auth_file:
        key = auth_file.readline()[:-1]

    return key

authkey = read_auth("create-key.txt")
if authkey is None:
    print "Auth file not found, aborting"
    sys.exit(1)

parser = argparse.ArgumentParser("Sends DNSSEC queries to Spark validators")
parser.add_argument('--datadir', required=True, help="directory to save output")
args = parser.parse_args()

if not os.path.exists(args.datadir):
    os.makedirs(args.datadir)


with open('data/probes.json', 'rb') as probe_file:
    probe_list = json.load(probe_file)

base_url = "https://atlas.ripe.net/api/v1/measurement/?key={}".format(authkey)

msm_list = []
probe_id_set = set()
for probe_info in probe_list:
    if probe_info['asn_v4'] == 4771:
        probe_id_set.add(str(probe_info['id']))

print "Sending to probes", probe_id_set

data = {"definitions": [
    {
        "query_argument": 'www.radionz.co.nz',
        "target": "122.56.237.1",
        "af": 4,
        "interval": 60,
        "query_type": 'A',
        "query_class": 'IN',
        "do": True,
        "recursion_desired": True,
        "description": "DNSSEC validation of Radio NZ website",
        "type": "dns",
        "protocol": "UDP",
        "is_oneoff": False,
        "can_visualize": False,
        "use_NSID": True,
        "use_probe_resolver": False,
        "is_public": False
    }],
    "probes": [{"requested": len(probe_id_set)-1, "type": "probes", "value": ",".join(probe_id_set)}],
    "stop_time": int(time.time()) + 60*10 + 1
}
req_data = json.dumps(data)

try:
    request = urllib2.Request(base_url)
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")
    conn = urllib2.urlopen(request, req_data)
    results = json.load(conn)
    print results
    print req_data
    for m in results['measurements']:
        msm_list.append(m)
    conn.close()
except urllib2.HTTPError as e:
    print "Fatal Error: {}".format(e.read())
    print req_data

with open('{}/measurements.json'.format(args.datadir), 'wb') as msm_file:
    json.dump(msm_list, msm_file)