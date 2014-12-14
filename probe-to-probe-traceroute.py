__author__ = 'secastro'

import json
import argparse
import urllib2
import random
import time
import sys, os


def read_auth(filename):
    with open(filename, 'rb') as auth_file:
        key = auth_file.readline()[:-1]

    return key


parser = argparse.ArgumentParser("Creates probe to probe traceroutes")
parser.add_argument('--datadir', required=True, help="directory to save output")
args = parser.parse_args()

if not os.path.exists(args.datadir):
    os.makedirs(args.datadir)

authkey = read_auth("create-key.txt")
if authkey is None:
    print "Auth file not found, aborting"
    sys.exit(1)

with open('data/probes.json', 'rb') as probe_file:
    probe_list = json.load(probe_file)

base_url = "https://atlas.ripe.net/api/v1/measurement/?key={}".format(authkey)

msm_list = []
for probe in probe_list:
    dest = random.choice(probe_list)

    data = {"definitions": [
        {
            "target": dest['address_v4'],
            "description": "Traceroute to probe {}".format(dest['id']),
            "type": "traceroute",
            "protocol": "ICMP",
            "af": 4,
            "is_oneoff": True,
            "can_visualize": False,
            "is_public": False
        }],
        "probes": [{"requested": 1, "type": "probes", "value": ",".join([str(probe["id"])])}]
    }

    try:
        req_data = json.dumps(data)
        request = urllib2.Request(base_url)
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        conn = urllib2.urlopen(request, req_data)
        results = json.load(conn)
        print results
        print req_data
        msm_list.append(results['measurements'])
        conn.close()
        time.sleep(3)
    except urllib2.HTTPError as e:
        print "Fatal Error: {}".format(e.read())
        print req_data

with open('{}/measurements.json'.format(args.datadir), 'wb') as msm_file:
    json.dump(msm_list, msm_file)
