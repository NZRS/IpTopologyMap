#!/usr/bin/env python2

import json
import argparse
import os

parser = argparse.ArgumentParser("Prepares base configuration file")
parser.add_argument('--datadir', required=True,
                    help="Directory to save configuration file")
parser.add_argument('--primary', required=True, nargs='*',
                    help="List of countries to generate the map for")
parser.add_argument('--secondary', required=False, nargs='*',
                    help="List of secondary countries to color differently")
args = parser.parse_args()


with open(os.path.join(args.datadir, 'config.json'), 'wb') as f:
    json.dump({'PrimaryCountry': args.primary,
               'SecondaryCountry': args.secondary}, f)
