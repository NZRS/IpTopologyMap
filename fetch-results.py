#!/usr/bin/python

import urllib2
import json
import sys
import os
import argparse


def read_auth(filename):
    with open(filename, 'rb') as auth_file:
        key = auth_file.readline()[:-1]

    return key


parser = argparse.ArgumentParser("Retrieves traceroute results")
parser.add_argument('--datadir', required=True, help="directory to save output")
args = parser.parse_args()

if not os.path.exists(args.datadir):
    print "datadir must exists!"
    sys.exit(1)

authkey = read_auth("read-key.txt")
if authkey is None:
    print "Auth file not found, aborting"
    sys.exit(1)

with open("{}/measurements.json".format(args.datadir), "rb") as msm_file:
    msm_list = json.load(msm_file)

result_list = []
for msm in msm_list:
    api_url = "https://atlas.ripe.net/api/v1/measurement/{}/result/?key={}".format(msm[0], authkey)
    request = urllib2.Request(api_url)
    request.add_header("Accept", "application/json")
    try:
        conn = urllib2.urlopen(request)
        result = json.load(conn)
        result_list.append(result)
        conn.close()
    except urllib2.HTTPError as e:
        print >> sys.stderr, ("Fatal error: %s" % e.read())
        raise

with open('{}/results.json'.format(args.datadir), 'wb') as res_file:
    json.dump(result_list, res_file)
