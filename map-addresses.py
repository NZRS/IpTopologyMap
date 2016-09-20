import GeoIP
import requests
from multiprocessing import Pool
from progressbar import ProgressBar
import json
import argparse
import os

g = GeoIP.open("data/GeoIPASNum.dat", GeoIP.GEOIP_STANDARD)

stat_ripe = "https://stat.ripe.net/data/routing-status/data.json"

parser = argparse.ArgumentParser("Uses RIPE stat to map addresses unmappable "
                                 "by GeoIP")
parser.add_argument('--datadir', required=True,
                    help="directory to read input and save output")
args = parser.parse_args()


results = []
pbar = ProgressBar()


def map_addr(a):
    r = requests.get(stat_ripe, params={'resource': a})
    response = r.json()

    origin = set()
    try:
        origin = set([o['origin'] for o in response['data']['origins']])
    except KeyError:
        pass

    if len(origin) > 0:
        return a, list(origin)[0]
    else:
        return a, None


def log_result(result):
    results.append(result)
    pbar.update(len(results))

addr = []
with open(os.path.join(args.datadir, 'unmappable-addresses.txt')) as f:
    addr = [a.rstrip("\n") for a in f.readlines()]

remap_file = os.path.join(args.datadir, 'remapped-addresses.json')
existing = {}
if os.path.exists(remap_file):
    with open(remap_file) as f:
        existing = json.load(f)

pool = Pool()
pbar.maxval = len(addr)
pbar.start()
for a in addr:
    pool.apply_async(map_addr, args=(a, ), callback=log_result)

pool.close()
pool.join()
pbar.finish()

with open(remap_file, 'wb') as f:
    existing.update(dict((k, v) for (k, v) in results if v is not None))
    json.dump(existing, f)
