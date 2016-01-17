#!/usr/bin/python

__author__ = 'secastro'

import json
import argparse
import urllib2
import random
import time
import sys
import os
import os.path
from collections import defaultdict


def valid_fraction(s):
    if 0.0 <= float(s) <= 1.0:
        return float(s)
    else:
        raise argparse.ArgumentTypeError("%r is out of bounds [0.0, 1.0]" % s)


def load_existing(source_dir, filename):
    e = []
    file_loc = "{}/{}".format(source_dir, filename)
    if os.path.isfile(file_loc):
        with open(file_loc, 'rb') as s_file:
            e = json.load(s_file)

    return e


def get_address_sample(infile, fraction):
    with open(infile, 'rb') as addr_file:
        dest_list = json.load(addr_file)

    """Group the addresses by the prefix covering it"""
    dest_addr = defaultdict(list)
    for dest in dest_list:
        dest_addr[dest['prefix']].append(dest['address'])

    selected = []
    """Pick one address per prefix"""
    for prefix, addresses in dest_addr.iteritems():
        for a in random.sample(addresses, 1):
            selected.append(a)

    # Generate a sample from the list of selected addresses
    return random.sample(selected, int(len(selected)*fraction))


def read_auth(filename):
    with open(filename, 'rb') as auth_file:
        key = auth_file.readline()[:-1]

    return key


def probe_ids(probe_set, myid):
    return [str(id) for id in probe_set-{myid}]


def schedule_measurement(dest, probes):
    msm_status = defaultdict(list)

    data = {"definitions": [
        {
            "target": dest,
            "description": "Traceroute to {}".format(dest),
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
        # This sleep is important to give time to the scheduled measurements to complete before trying more.
        time.sleep(3)
    except urllib2.HTTPError as e:
        msm_status['failed'].append(dest)
        print "Fatal Error: {}".format(e.read())
        print req_data

    return msm_status

parser = argparse.ArgumentParser("Creates probe to probe traceroutes")
parser.add_argument('--datadir', required=True, help="directory to save output")
parser.add_argument('--stage', required=False,
                    help="Stage of measurement to execute (1, 2, 3, all)")
parser.add_argument('--sample', required=False, default=0.2,
                    type=valid_fraction,
                    help="Fraction of addresses to sample")
args = parser.parse_args()
if (args.stage is None) or (args.stage == 'all'):
    stage = [1, 2, 3]
else:
    stage = [int(s) for s in args.stage.split(",")]


if not os.path.exists(args.datadir):
    os.makedirs(args.datadir)

authkey = read_auth("create-key.txt")
if authkey is None:
    print "Auth file with ATLAS API key not found, aborting"
    sys.exit(1)

with open(os.path.join(args.datadir, 'probes.json'), 'rb') as probe_file:
    probe_list = json.load(probe_file)

base_url = "https://atlas.ripe.net/api/v1/measurement/?key={}".format(authkey)

msm_list = []
probe_id_set = set([probe['id'] for probe in probe_list])
failed_msm = []
"""First stage: Schedule the measurements going to an specific probe from all the remaining available probes"""
if 1 in stage:
    print "Executing Stage 1"
    for probe in probe_list:
        status = schedule_measurement(probe['address_v4'], probe_ids(probe_id_set, probe['id']))
        msm_list = msm_list + status['list']
        failed_msm = failed_msm + status['failed']

"""Second stage: Schedule the measurement to a selected address from a sample"""
if 2 in stage:
    print "Executing Stage 2"
    for addr in get_address_sample(os.path.join(args.datadir, 'dest-addr.json'), args.sample):
        status = schedule_measurement(addr, [str(id) for id in probe_id_set])
        msm_list = msm_list + status['list']
        failed_msm = failed_msm + status['failed']

"""Third stage: Sent traceroute to known sites"""
if 3 in stage:
    print "Executing Stage 3"
    with open('data/known-sites.txt', 'rb') as site_file:
        for site in site_file:
            status = schedule_measurement(site.rstrip(), [str(id) for id in probe_id_set])
            msm_list = msm_list + status['list']
            failed_msm = failed_msm + status['failed']

existing_msm = load_existing(args.datadir, 'measurements.json')
with open(os.path.join(args.datadir, 'measurements.json'), 'wb') as msm_file:
    json.dump(msm_list + existing_msm, msm_file)

existing_failures = load_existing(args.datadir, 'failed-probes.json')
with open(os.path.join(args.datadir, 'failed-probes.json'), 'wb') as failed_file:
    json.dump(failed_msm + existing_failures, failed_file)
