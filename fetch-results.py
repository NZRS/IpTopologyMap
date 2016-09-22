#!/usr/bin/env python2

import json
import sys
import os
import argparse
from collections import defaultdict
from progressbar import ProgressBar
from multiprocessing import Pool
from ripe.atlas.cousteau import AtlasResultsRequest

# Needed globally
results = []
pbar = ProgressBar()


def fetch_result(msm):
    kwargs = {'msm_id': msm['id']}

    (is_success, response) = AtlasResultsRequest(**kwargs).create()

    if is_success:
        return msm['cc'], response

    return None


def log_result(r):
    results.append(r)
    pbar.update(len(results))


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
    with open(os.path.join(args.datadir, 'measurements.json')) as msm_file:
        msm_data = json.load(msm_file)
else:
    msm_data = {'cc': [args.msm]}


pool = Pool(processes=4)
msm_to_fetch = [{'cc': cc, 'id': msm_id} for cc, msm_list in
                msm_data.iteritems() for msm_id in msm_list]
print("Will fetch %d measurements" % len(msm_to_fetch))
pbar.start(max_value=len(msm_to_fetch))
for msm in msm_to_fetch:
    pool.apply_async(fetch_result, args=(msm, ), callback=log_result)

pool.close()
pool.join()
pbar.finish()

with open(os.path.join(args.datadir, 'results.json'), 'wb') as res_file:
    final_res = defaultdict(list)
    for r in results:
        if r is None:
            continue
        cc, msm_res = r
        for res in msm_res:
            final_res[cc].append(res)
    json.dump(final_res, res_file)
