#!/usr/bin/env python2

"""
    Original code from https://github.com/vbajpai/atsquery
    Modified to suit the needs of this specific tool
"""
import os

import requests
import datetime
import time
import hmac
import hashlib
import base64
import collections
import xml.etree.ElementTree as ET
import yaml
import argparse
import json

"""Base constant setup"""
HOST = 'ats.amazonaws.com'
ACTION = 'TopSites'
RESPONSE_GROUP = "Country"
START = 1
COUNT = 100
SIGNATURE_VERSION = 2
SIGNATURE_METHOD = 'HmacSHA256'

access_key_id = None
country_code = ''


def http_get(access_key_id, secret_access_key, country_code='', signature=''):
    """sends a HTTP GET to alexa top sites web service using requests;
     parses the XML response using xml; filters the response XML for domain
     names and returns the list of domain entries"""

    TIMESTAMP = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    query = {
        "Action"           : ACTION,
        "AWSAccessKeyId"   : access_key_id,
        "Timestamp"        : TIMESTAMP,
        "ResponseGroup"    : RESPONSE_GROUP,
        "Start"            : START,
        "Count"            : COUNT,
        "CountryCode"      : country_code,
        "SignatureVersion" : SIGNATURE_VERSION,
        "SignatureMethod"  : SIGNATURE_METHOD
    }

    query = collections.OrderedDict(sorted(query.items()))
    req = requests.Request(
                            method='GET',
                            url='http://%s' % HOST,
                            params=query
                          )
    try:
        prep = req.prepare()
    except Exception as e:
        print e

    string_to_sign = '\n'.join([prep.method, HOST, '/', prep.path_url[2:]])
    print(string_to_sign)
    signature = hmac.new(
        key=secret_access_key,
        msg=bytes(string_to_sign),
        digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(signature)
    prep.url = '%s&Signature=%s'%(prep.url, signature)

    s = requests.Session()
    try:
        res = s.send(prep)
    except Exception as e:
        print e
    else:
        try:
            if res.status_code is not requests.codes.ok:
                res.raise_for_status()
        except Exception as e:
            print e
            return None

    xml = res.text
    entries = []
    NSMAP = {'aws': 'http://ats.amazonaws.com/doc/2005-11-21'}
    try:
        tree = ET.fromstring(xml)
        xml_elems = tree.findall('.//aws:DataUrl', NSMAP)
        entries = [entry.text for entry in xml_elems]
    except Exception as e:
        print e
        return None

    return entries


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Fetches Top 100 sites per country "
                                     "from Alexa Top Sites")
    parser.add_argument('--auth', type=str, required=False, default='auth.yaml',
                        help="YAML file with the access credentials")
    parser.add_argument('--datadir', type=str, required=True,
                        help="Directory to read config from and save data to")
    args = parser.parse_args()

    """Read the auth credentials"""
    with open(args.auth, 'r') as f:
        auth = yaml.load(f)

    """Read config file"""
    with open(os.path.join(args.datadir, 'config.json')) as conf_file:
        config = json.load(conf_file)

    """Read the list of sites we don't want in the list"""
    undesirable = set()
    with open('data/undesirable-sites.txt') as skip_file:
        for line in skip_file.readlines():
            undesirable.add(line.rstrip('\n'))

    """Go to Alexa, fetch the list of sites, save it"""
    site_set = set()
    success_flag = True
    for country in config['PrimaryCountry']:
        try:
            print("Country: %s" % country)
            alexa_sites = http_get(auth['access_key_id'],
                                   auth['secret_access_key'], country)
            if alexa_sites is not None:
                site_set |= set([e for e in alexa_sites if e not in
                                 undesirable])
            else:
                success_flag &= False
            # Sleep for a bit to avoid hammering Alexa
            time.sleep(2)
        except TypeError as e:
            print e

    if success_flag:
        with open(os.path.join(args.datadir, 'known-sites.json'), 'wb') as f:
            json.dump(list(site_set), f)
    else:
        print("ERROR: Fetching failed, won't save a list")
