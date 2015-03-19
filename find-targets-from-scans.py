__author__ = 'secastro'

import gzip
import csv
import json
import ipaddress
from progressbar import ProgressBar

nz_prefix = set()
failed_addr = set()


def is_ip_contained(a):
    contained = False
    try:
        ip = ipaddress.ip_network(unicode(a))
    except ValueError:
        # print "ERROR: address caused exception '%s'" % a
        failed_addr.add(a)
        return False

    for p in nz_prefix_list:
        if p.overlaps(ip):
            contained = True
            break

    return contained

with open('data/rv-nz-aspath.json', 'rb') as nz_prefixes:
    nz_aspath = json.load(nz_prefixes)
    for path in nz_aspath['aspath']:
        for prefix in path['prefixes']:
            nz_prefix.add(prefix)

"""We need some objects to check if an IP address is covered by a prefix, better to do it once"""
nz_prefix_list = [p2 for p2 in ipaddress.collapse_addresses([ipaddress.ip_network(p1) for p1 in nz_prefix])]


addr_list = set()
with gzip.open('data/scans/20150309-dns-53.csv.gz', 'rb') as dns_scan:
    csv_r = csv.reader(dns_scan)

    # There is a header, skip it
    next(csv_r)

    idx = 0
    for row in csv_r:
        # row[1] is the address we want to check
        idx += 1
        addr_list.add(row[1])

        if idx % 100000 == 0:
            print "Read %d records" % idx

        if idx > 100000:
            break

print "%d addresses will be checked" % (len(addr_list))
print "%d NZ prefixes" % (len(nz_prefix_list))
nz_addr = set()
pbar = ProgressBar(maxval=len(addr_list)).start()
cnt = 0
for addr in addr_list:
    if is_ip_contained(addr):
        nz_addr.add(addr)
    cnt += 1
    if cnt % 100 == 0:
        pbar.update(cnt)

pbar.finish()


print "%d NZ addresses found" % len(nz_addr)
with open('data/nz-dest-addr.json', 'wb') as nz_addr_file:
    json.dump([a for a in nz_addr], nz_addr_file)

print "%d failed addresses" % len(failed_addr)
with open('data/failed-addresses.json', 'wb') as failed_file:
    json.dump([a for a in failed_addr], failed_file)
