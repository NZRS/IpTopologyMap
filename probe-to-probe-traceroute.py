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
    e = defaultdict(list)
    file_loc = os.path.join(source_dir, filename)
    if os.path.isfile(file_loc):
        with open(file_loc, 'rb') as s_file:
            e = json.load(s_file)

    return e


def get_address_sample(infile, fraction, cc):
    with open(infile, 'rb') as addr_file:
        dest_list = json.load(addr_file)

    """Group the addresses by the prefix covering it"""
    dest_addr = defaultdict(list)
    for dest in dest_list[cc]:
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
        # Check if we got a positive result
        if 'measurements' in results:
            for m in results['measurements']:
                msm_status['list'].append(m)
        # Check if we got an error, save the request for later
        if 'error' in results:
            msm_status['failed'].append(dest)
        conn.close()
        # This sleep is important to give time to the scheduled measurements to complete before trying more.
        time.sleep(3)
    except (urllib2.HTTPError, urllib2.URLError) as e:
        # Other kind of error
        msm_status['failed'].append(dest)
        print "Fatal Error: %s " % e
        print req_data

    return msm_status


def merge_msm(x, y):
    """
    merge_msm takes two dictionaries with string keys and list values,
    and merge them
    :param x: defaultdict(list)
    :param y: defaultdict(list)
    :return: defaultdict(list)
    """

    z = defaultdict(list)
    for key in set(x.keys() + y.keys()):
        z[key] = list(set(x.get(key, []) + y.get(key, [])))

    return z

parser = argparse.ArgumentParser("Creates probe to probe traceroutes")
parser.add_argument('--datadir', required=True, help="directory to save output")
parser.add_argument('--stage', required=False,
                    help="Stage of measurement to execute (1, 2, 3, all)")
parser.add_argument('--sample', required=False, default=0.2,
                    type=valid_fraction,
                    help="Fraction of addresses to sample")
parser.add_argument('--retry', required=False, action='store_true',
                    help="Schedule measurements for previously failed attempts")
parser.add_argument('--dry-run', required=False, action='store_true',
                    help="Calculate the destinations, but don't schedule "
                         "measurements")
args = parser.parse_args()
if (args.stage is None) or (args.stage == 'all'):
    stage = [1, 2, 3]
else:
    stage = [int(s) for s in args.stage.split(",")]

if args.retry:
    # We are cheating here, setting the list of stages to nothing
    stage = []
    print("INFO: We will retry previously failed measurements")

if not os.path.exists(args.datadir):
    os.makedirs(args.datadir)

authkey = read_auth("create-key.txt")
if authkey is None:
    print "Auth file with ATLAS API key not found, aborting"
    sys.exit(1)

with open(os.path.join(args.datadir, 'probes.json'), 'rb') as probe_file:
    cc_probe_list = json.load(probe_file)

base_url = "https://atlas.ripe.net/api/v1/measurement/?key={}".format(authkey)

msm_list = defaultdict(list)
failed_msm = defaultdict(list)
msm_cnt = 0

# We can have multiple countries, prepare this for each country
for cc, probe_list in cc_probe_list.iteritems():
    probe_id_set = set([probe['id'] for probe in probe_list])
    probe_id_list = [str(id) for id in probe_id_set]
    """First stage: Schedule the measurements going to an specific probe from all the remaining available probes"""
    if 1 in stage:
        print "Executing Stage 1, country %s" % cc
        for probe in probe_list:
            if args.dry_run:
                msm_cnt += 1
            else:
                status = schedule_measurement(probe['address_v4'],
                                              probe_ids(probe_id_set, probe['id']))
                msm_list[cc] = msm_list[cc] + status['list']
                failed_msm[cc] = failed_msm[cc] + status['failed']

    """Second stage: Schedule the measurement to a selected address from a sample"""
    if 2 in stage:
        print "Executing Stage 2, country %s" % cc
        addr_file = os.path.join(args.datadir, 'dest-addr.json')
        for addr in get_address_sample(addr_file, args.sample, cc):
            if args.dry_run:
                msm_cnt += 1
            else:
                status = schedule_measurement(addr, probe_id_list)
                msm_list[cc] = msm_list[cc] + status['list']
                failed_msm[cc] = failed_msm[cc] + status['failed']

    """Third stage: Sent traceroute to known sites"""
    if 3 in stage:
        print "Executing Stage 3, country %s" % cc
        with open(os.path.join(args.datadir, 'known-sites.json')) as f:
            site_list = json.load(f)
            for site in site_list:
                if args.dry_run:
                    msm_cnt += 1
                else:
                    status = schedule_measurement(site, probe_id_list)
                    msm_list[cc] = msm_list[cc] + status['list']
                    failed_msm[cc] = failed_msm[cc] + status['failed']

    if args.retry and not args.dry_run:
        print("Executing retries")
        with open(os.path.join(args.datadir, 'failed-msm.json')) as failed_file:
            prev_failed = json.load(failed_file)

            # Generate a set, to avoid duplicating destinations
            for prev_attempt in set(prev_failed[cc]):
                status = schedule_measurement(prev_attempt, probe_id_list)
                msm_list[cc] = msm_list[cc] + status['list']
                failed_msm[cc] = failed_msm[cc] + status['failed']


if args.dry_run:
    print("INFO: %s measurement would have been scheduled" % msm_cnt)
else:
    existing_msm = load_existing(args.datadir, 'measurements.json')
    with open(os.path.join(args.datadir, 'measurements.json'), 'wb') as msm_file:
        json.dump(merge_msm(msm_list, existing_msm), msm_file)

    existing_failures = load_existing(args.datadir, 'failed-msm.json')
    with open(os.path.join(args.datadir, 'failed-msm.json'), 'wb') as failed_file:
        json.dump(merge_msm(failed_msm, existing_failures), failed_file)
