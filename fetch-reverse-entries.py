#!/usr/bin/env python

import sys
import dns.reversename
import ipaddr
from twisted.names import client, error
from twisted.internet import reactor
from twisted.internet import defer, task
import argparse
import json


def send_dns_query((qname, resolver, addr)):
    d = resolver.lookupPointer(qname)
    d.addCallback(receive_dns_response, qname, addr)
    d.addErrback(printError, qname, addr)
    return d
    

def do_parallel_dns(name_list, count, callable, *args, **named):
    coop = task.Cooperator()
    work = (callable(name, *args, **named) for name in name_list)
    return defer.DeferredList([coop.coiterate(work) for i in xrange(count)])


def receive_dns_response(records, qname, addr):
    """
    Receives TXT records and parses them
    """
    answers, authority, additional = records
    if answers:
        for x in answers:
            try:
                print str(x.payload.name)
                addr_info[addr] = dict(name=str(x.payload.name))
            except ValueError:
                sys.stderr.write('ERROR decoding payload %s for %s\n' %
                (str(x.payload), qname))
                addr_info[addr] = dict(name=addr)
    else:
        sys.stderr.write(
            'ERROR: No TXT records found for name %r\n' % (qname,))


def printError(failure, domainname, asn):
    """
    Print a friendly error message if the domainname could not be
    resolved.
    """
    failure.trap(error.DNSNameError, error.DNSServerError)
    sys.stderr.write('ERROR: domain name not found %r\n' % (domainname,))


if __name__ == '__main__':
    NUM_WORKERS = 8
    addr_info = {}

    parser = argparse.ArgumentParser("Fetches AS details for a list of ASN")
    parser.add_argument('--input', required=True, help="Input file with ASNs")
    parser.add_argument('--output', required=True, help="JSON file to save ASN info")
    args = parser.parse_args()

    addresses = []
    resolver = client.Resolver('/etc/resolv.conf')
    with open(args.input, 'rb') as name_file:
        addr_list = json.load(name_file)

    for addr in addr_list:
        print addr
        a = ipaddr.IPv4Address(addr)
        if a.is_private:
            addr_info[addr] = dict(name="Private")
        else:
            addresses.append([dns.reversename.from_address(addr).to_text(), resolver, addr])

    finished = do_parallel_dns(addresses, NUM_WORKERS, send_dns_query)

    finished.addCallback(lambda ignored: reactor.stop())
    finished.addErrback(printError)

    reactor.run()

    # Save the information we may have obtained
    with open(args.output, 'wb') as as_info_output:
        json.dump(addr_info, as_info_output)
