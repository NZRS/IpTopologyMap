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
parser.add_argument('--msm', required=False, type=int, help="Fetch specific measurement id")
args = parser.parse_args()

if not os.path.exists(args.datadir):
    print("Data directory %s must exists!" % args.datadir)
    sys.exit(1)

atlas_read_api_key = 'read-key.txt'
authkey = read_auth(atlas_read_api_key)
if authkey is None:
    print("Auth file %s not found, aborting" % atlas_read_api_key)
    sys.exit(1)

if not args.msm:
    with open("{}/measurements.json".format(args.datadir), "rb") as msm_file:
        msm_list = json.load(msm_file)
else:
    msm_list = [args.msm]

result_list = []
for msm in msm_list:
    print("Fetching results for measurement %s" % msm)
    api_url = "https://atlas.ripe.net/api/v1/measurement/{}/result/?key={}".format(msm, authkey)
    request = urllib2.Request(api_url)
    request.add_header("Accept", "application/json")
    try:
        conn = urllib2.urlopen(request)
        msm_data = json.load(conn)
        for result in msm_data:
            result_list.append(result)
        conn.close()
    except urllib2.HTTPError as e:
        print >> sys.stderr, ("Fatal error: %s" % e.read())
        raise

with open('{}/results.json'.format(args.datadir), 'wb') as res_file:
    json.dump(result_list, res_file)
