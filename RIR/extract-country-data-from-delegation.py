#!/usr/bin/env python

import csv
from collections import defaultdict
import argparse
import glob
import json

parser = argparse.ArgumentParser("Parses the delegation files from the RIR"
                                 "to extract ASes and prefixes belonging to a country")
parser.add_argument('--config', required=True, type=str,
                    help="Configuration file")
parser.add_argument('--outfile', required=True, type=str,
                    help="File to save the collected data")
args = parser.parse_args()

with open(args.config) as f:
    config = json.load(f)

print("Selected countries %s" % config['PrimaryCountry'])

# Each file has a line that looks like this
# apnic|JP|asn|173|1|20020801|allocated

as_country = set([cc.upper() for cc in config['PrimaryCountry']])
cc_resources = defaultdict(lambda: defaultdict(list))
for rir_file in glob.glob("delegated-*-latest"):
    with open(rir_file, 'rb') as csvfile:
        csvin = csv.reader(csvfile, delimiter='|')

        for row in csvin:
            if row[-1] == 'allocated':
                if row[2] == 'asn' and row[1] in as_country:
                    cc_resources[row[1]]['AS'].append(row[3])
                if row[2] == 'ipv4' and row[1] in as_country:
                    prefix = row[3]
                    mask = 32 - (int(row[4]) - 1).bit_length()
                    prefix = "{0}/{1}".format(row[3], mask)
                    cc_resources[row[1]]['prefixes'].append(prefix)


with open(args.outfile, 'wb') as rir_file:
    json.dump(cc_resources, rir_file)

