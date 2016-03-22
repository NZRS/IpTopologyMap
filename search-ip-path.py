import json
import argparse


parser = argparse.ArgumentParser("Searches for IP links in result file")
parser.add_argument('--file', required=True, help="JSON file to read from")
parser.add_argument('--source', required=True, help="Source address")
parser.add_argument('--target', required=True, help="Source address")
args = parser.parse_args()

with open(args.file, 'rb') as f:
    data = json.load(f)

path_list = []
for e in data:
    # Use path to build a graph!
    for i in xrange(1, len(e['path'])):
        source = e['path'][i-1]['addr']
        target = e['path'][i]['addr']
        if ((source == args.source and target == args.target) or
                (source == args.target and target == args.source)):
            print(" -- ".join([p['addr'] for p in e['path']]))



# Let the search begin

