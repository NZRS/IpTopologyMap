#!/usr/bin/python

import requests
import sys
import argparse
import os
from collections import Counter, defaultdict
import json


def get_probes_from_country(cc):
    base_url = "https://atlas.ripe.net/"
    url = base_url + "/api/v1/probe/"
    query_param = {
        'country_code': cc,
        'format': 'json',
        'limit': 50
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    probe_cc_list = []
    probe_asn = Counter()

    req = requests.get(url, params=query_param, headers=headers)
    result = req.json()
    total_msm = result['meta']['total_count']
    msm_cnt = 0
    while msm_cnt < total_msm:
        next_url = result['meta']['next']
        # print("Next url: %s\n" % next_url)
        for obj in result['objects']:
            msm_cnt += 1
            if obj['status_name'] == 'Connected' and None != obj['address_v4']:
                print("{id:d} {address_v4:<20s} {asn_v4} {country_code}".format(
                    **obj))
                probe_cc_list.append(dict((k, obj[k]) for k in ['id',
                                                              'address_v4',
                                                             'asn_v4']))
                probe_asn[obj['asn_v4']] += 1
        if next_url is not None:
            req = requests.get(base_url + next_url, headers=headers)
            result = req.json()

    return probe_cc_list


parser = argparse.ArgumentParser("Fetches ATLAS probes information for a "
                                 "given country")
parser.add_argument('--datadir', required=True, help="directory to save output")
args = parser.parse_args()

# Read the configuration file
with open(os.path.join(args.datadir, 'config.json')) as f:
    config = json.load(f)

probe_list = defaultdict(list)
for country in config['PrimaryCountry']:
    probe_list[country] = probe_list[country] + get_probes_from_country(country)
    print("Country: %s, Number of Probes: %d" % (country,
                                                 len(probe_list[country])))


with open(os.path.join(args.datadir, 'probes.json'), 'wb') as probe_file:
    json.dump(probe_list, probe_file)
#
# probes_per_origin = pd.DataFrame()
# with open(os.path.join(args.datadir, 'as-list.txt'), 'wb') as asn_file:
#     for asn, count in probe_asn.iteritems():
#         asn_file.write("%s\n" % asn)
#         probes_per_origin.append(dict(origin=asn, count=count), ignore_index=True)
#
# print(probes_per_origin)
