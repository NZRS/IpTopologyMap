__author__ = 'secastro'

import json
import argparse
import urllib2
import random
import time
import sys, os
from collections import defaultdict


def read_auth(filename):
    with open(filename, 'rb') as auth_file:
        key = auth_file.readline()[:-1]

    return key


def probe_ids(probe_set, myid):
    return [str(id) for id in probe_set-set([myid])]


def schedule_measurement(dest, probes):
    msm_status = defaultdict(list)

    data = {"definitions": [
        {
            "target": dest,
            "description": "Traceroute to address {}".format(dest),
            "type": "traceroute",
            "protocol": "ICMP",
            "paris": 16,
            "af": 4,
            "is_oneoff": True,
            "can_visualize": False,
            "is_public": False
        }],
        "probes": [{"requested": len(probes), "type": "probes", "value": ",".join(probes)}]
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
        for m in results['measurements']:
            msm_status['list'].append(m)
        conn.close()
        time.sleep(1)
    except urllib2.HTTPError as e:
        msm_status['failed'].append(dest)
        print "Fatal Error: {}".format(e.read())
        print req_data

    return msm_status

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
"""First stage: Schedule the measurements going to an specific probe from all the remaining available probes"""
for probe in probe_list:
    status = schedule_measurement(probe['address_v4'], probe_ids(probe_id_set, probe['id']))
    msm_list = msm_list + status['list']
    failed_msm = failed_msm + status['failed']

"""Second stage: Schedule the measurement to a selected address from a sample"""


with open('{}/measurements.json'.format(args.datadir), 'wb') as msm_file:
    json.dump(msm_list, msm_file)

with open('{}/failed-probes.json'.format(args.datadir), 'wb') as failed_file:
    json.dump(failed_msm, failed_file)
