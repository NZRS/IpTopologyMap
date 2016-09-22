#!/usr/bin/env python2

__author__ = 'secastro'

import requests
import bs4
import re
import argparse
import os
from progressbar import ProgressBar


"""download-scan-data.py

    Uses the site scans.io from University of Michigan to download the
    latest dataset from the UDP Internet-Wide Scan Data Repository, to be used
    as source of potential addresses to traceroute
"""


start_url = 'https://scans.io/study/sonar.udp'

parser = argparse.ArgumentParser("Downloads datasets from scans.io")
parser.add_argument('--datadir', required=True, help="directory to save output")
args = parser.parse_args()

req = requests.get(start_url)
html = bs4.BeautifulSoup(req.text, "html.parser")
chunk_sz = 64*1024

sources = {}
days = set()
# dl_pat = '\-(mdns\-53)'
dl_pat = '\-(dns\-53|sip\-5060)'
# Collect all the links we are interested
for link in html.findAll('a', text=re.compile(dl_pat, re.I)):
    sources[link.text] = link['href']
    days.add(link.text[:8])

# Among the list of links, find the latest date
max_day = max(days)
print("Latest day %s" % max(days))

for k in [e for e in sources.keys() if max_day in e]:
    # Each e has a filename and a URL
    fname = k[9:]
    print("Saving URL %s to file %s" % (sources[k], fname))
    with open(os.path.join(args.datadir, fname), 'wb') as fd:
        file_req = requests.get(sources[k])
        # Use file_req.headers['content-length'] if available to make a
        # progress bar
        pbar = ProgressBar(maxval=int(file_req.headers[
                                          'content-length'])).start()
        dl_sz = 0
        for chunk in file_req.iter_content(chunk_sz):
            fd.write(chunk)
            dl_sz += len(chunk)
            pbar.update(dl_sz)
        pbar.finish()
