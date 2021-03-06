#!/usr/bin/python

import urllib2
import json
import sys
from collections import Counter
import pandas as pd

base_url = "https://atlas.ripe.net/"
url = base_url + "/api/v1/probe/?country_code=NZ&format=json&limit=50"

request = urllib2.Request(url)
request.add_header("Content-Type", "application/json")
request.add_header("Accept", "application/json")
probe_list = []
probe_asn = Counter()
try:
    conn = urllib2.urlopen(request)
    result = json.load(conn) 
    total_msm = result['meta']['total_count']
    msm_cnt = 0
    while msm_cnt < total_msm: 
        next_url = result['meta']['next']
#        print("Next url: %s\n" % next_url)
        for obj in result['objects']:
            msm_cnt += 1
            if obj['status'] == 1 and None != obj.get('address_v4', None):
                print "{0:d} {1:<20s} {2}".format(obj['id'], obj['address_v4'], obj['asn_v4'])
                probe_list.append(dict((k, obj[k]) for k in ('id', 'address_v4', 'asn_v4')))
                probe_asn[obj['asn_v4']] += 1
        if next_url is not None:
            conn = urllib2.urlopen(base_url + next_url)
            result = json.load(conn) 
    conn.close()
except urllib2.HTTPError as e:
    print >>sys.stderr, ("Fatal error: %s" % e.read())
    raise
conn.close()

print len(probe_list)
with open('data/probes.json', 'wb') as probe_file:
    json.dump(probe_list, probe_file)

probes_per_origin = pd.DataFrame()
with open('data/as-list.txt', 'wb') as asn_file:
    for asn, count in probe_asn.iteritems():
        asn_file.write("%s\n" % asn)
        probes_per_origin.append(dict(origin=asn, count=count), ignore_index=True)

origin_weight = pd.read_csv('data/relevant-origin.csv', sep="\t", header=None, names=('origin', 'weight'))

print probes_per_origin
print origin_weight
