#!/usr/bin/env python2

""" get-pdb-info
    Fetches information about IXs in the world using the PeeringDB API"""
import argparse
import os
import requests
import json
from progressbar import ProgressBar

"""Start query is to get the full list of IXs"""
pdb_url = "https://www.peeringdb.com/api/ix"

parser = argparse.ArgumentParser("Fetches data from PeeringDB to build a list of known IXs")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
args = parser.parse_args()


req = requests.get(pdb_url, params={'depth': 3})

ix_resp = req.json()
ix_info = []
ix_cnt = 0
ix_missing = []

pbar = ProgressBar(max_value=len(ix_resp['data']))

for ix in ix_resp['data']:
    # if ix['id'] > 10:
    #     break

    try:
        # print "ID: %d, Name: %s" % (ix['id'], ix['name'])
        if ix_cnt % 10 == 0:
            pbar.update(ix_cnt)
        ix_cnt += 1
        ixpfx_id_set = set()
        for ixlan in ix['ixlan_set']:
            ixpfx_id_set |= set([p for p in ixlan['ixpfx_set']])

        # Fetch the information about the IX networks
        if len(ixpfx_id_set) > 0:
            ixpfx_req = requests.get("https://www.peeringdb.com/api/ixpfx",
                                     params={'id__in': ",".join([str(i) for i in ixpfx_id_set])})
            ixpfx_info = ixpfx_req.json()

            ix_info.append({'id': ix['id'],
                            'name': ix['name'],
                            'name_long': ix['name_long'],
                            'country': ix['country'],
                            'rs_asn': str(395165+ix['id']),
                            'ixpfx': [p['prefix'] for p in ixpfx_info['data']]})
        else:
            ix_missing.append(ix)
    except KeyError as e:
        print("ERROR: exception %s on %s" % (e, ix))

with open(os.path.join(args.datadir, 'peeringdb-dump.json'), 'wb') as f:
    json.dump(ix_info, f)

with open(os.path.join(args.datadir, 'peeringdb-errors.json'), 'wb') as f:
    json.dump(ix_missing, f)
