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


def probe_ids(probe_set, myid):
    return [str(id) for id in probe_set-set([myid])]


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
probe_id_set = set([probe['id'] for probe in probe_list])
failed_msm = []
for probe in probe_list:
    data = {"definitions": [
        {
            "target": probe['address_v4'],
            "description": "Traceroute to probe {}".format(probe['id']),
            "type": "traceroute",
            "protocol": "ICMP",
            "af": 4,
            "is_oneoff": True,
            "can_visualize": False,
            "is_public": False
        }],
        "probes": [{"requested": len(probe_id_set)-1, "type": "probes", "value": ",".join(probe_ids(probe_id_set, probe['id']))}]
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
        msm_list.append([m for m in results['measurements']])
        conn.close()
        time.sleep(3)
    except urllib2.HTTPError as e:
        failed_msm.append(probe)
        print "Fatal Error: {}".format(e.read())
        print req_data

with open('{}/measurements.json'.format(args.datadir), 'wb') as msm_file:
    json.dump(msm_list, msm_file)

with open('{}/failed-probes.json'.format(args.datadir), 'wb') as failed_file:
    json.dump(failed_msm, failed_file)
