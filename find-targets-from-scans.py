__author__ = 'secastro'

import gzip
import csv
import json
import ipaddress

nz_addr = set()
other_addr = set()
nz_prefix = set()
nz_prefix_list = []


def is_ip_contained(a):
    contained = False
    try:
        ip = ipaddress.ip_network(a)
        for p in nz_prefix_list:
            if p.overlaps(ip):
                contained = True
                break
    except ValueError:
        print "ERROR: address caused exception", a

    return contained

with open('data/rv-nz-aspath.json', 'rb') as nz_prefixes:
    nz_aspath = json.load(nz_prefixes)
    for path in nz_aspath['aspath']:
        for prefix in path['prefixes']:
            nz_prefix.add(prefix)

"""We need some objects to check if an IP address is covered by a prefix, better to do it once"""
for prefix in nz_prefix:
    nz_prefix_list.append(ipaddress.ip_network(prefix))


with gzip.open('data/scans/20150309-dns-53.csv.gz', 'rb') as dns_scan:
    csv_r = csv.reader(dns_scan)

    # There is a header, skip it
    next(csv_r)

    idx = 0
    for row in csv_r:
        # row[1] is the address we want to check
        idx += 1
        if not row[1] in nz_addr and not row[1] in other_addr:
            """ I haven't seen this address before, check against the list of prefixes of interest"""
            if is_ip_contained(row[1]):
                nz_addr.add(row[1])
            else:
                other_addr.add(row[1])

        if idx % 10000 == 0:
            print "."

with open('data/nz-dest-addr.csv', 'wb') as nz_addr_file:
    csv_w = csv.writer(nz_addr_file)
    csv_w.writerows(nz_addr)

