#!/usr/bin/python

import urllib2
import json
import sys
from collections import Counter
import requests


def read_auth(filename):
    with open(filename, 'rb') as auth_file:
        key = auth_file.readline()[:-1]

    return key


authkey = read_auth("read-key.txt")
if authkey is None:
    print "Auth file with ATLAS API key not found, aborting"
    sys.exit(1)

base_url = "https://atlas.ripe.net/"
url = base_url + "/api/v1/measurement/"
headers = {"Content-Type": "application/json",
           "Accept": "application/json"}
base_params = {'mine': True, 'limit': 50, 'key': authkey, 'msm_id__gt': 3376620}

request = requests.get(url, headers=headers, params=base_params)
probe_list = []
probe_asn = Counter()
try:
    result = request.json()
    total_msm = result['meta']['total_count']
    msm_cnt = 0
    while msm_cnt < total_msm:
        next_url = result['meta']['next']
#        print("Next url: %s\n" % next_url)
        for obj in result['objects']:
            msm_cnt += 1
            print(obj)
        if next_url is not None:
            request = requests.get(base_url + next_url, headers=headers)
            result = request.json()
except urllib2.HTTPError as e:
    print >>sys.stderr, ("Fatal error: %s" % e.read())
    raise

