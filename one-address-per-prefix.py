__author__ = 'secastro'

import json
import random
from collections import defaultdict

with open('data/nz-dest-addr.json', 'rb') as nz_addr_file:
    nz_dest = json.load(nz_addr_file)

dest_addr = defaultdict(list)
for dest in nz_dest:
    dest_addr[dest['prefix']].append(dest['address'])

sample = []
for prefix, addresses in dest_addr.iteritems():
    for a in random.sample(addresses, 1):
        sample.append([prefix, a])

print "%d addresses in sample" % len(sample)
print json.dumps(sample, indent=2)
