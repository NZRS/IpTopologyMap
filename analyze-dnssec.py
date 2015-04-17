__author__ = 'secastro'

import json
from ripe.atlas.sagan import DnsResult
import argparse
import datetime
from dateutil import tz
import csv

local_tz = tz.tzlocal()
utc_tz = tz.tzutc()

parser = argparse.ArgumentParser("Analyses results")
parser.add_argument('--datadir', required=True, help="directory to read input and save output")
args = parser.parse_args()

res_file = "{}/results.json".format(args.datadir)

with open(res_file, 'rb') as res_fd:
    res_blob = json.load(res_fd)

compiled_results = []
for res in res_blob:
    sagan_res = DnsResult(res)
    res_time = datetime.datetime.utcfromtimestamp(sagan_res.created_timestamp).replace(tzinfo=utc_tz).astimezone(local_tz).strftime("%F %T")

    for response in sagan_res.responses:
        raw_dns = response.abuf.raw_data
        for answer in raw_dns['AnswerSection']:
            if answer['Type'] == 'A':
                print sagan_res.probe_id, res_time, response.destination_address, raw_dns['HEADER']['AD'], answer['Name'], answer['Address'], answer['TTL']
                compiled_results.append([sagan_res.probe_id, res_time, raw_dns['HEADER']['AD'], answer['TTL']])
        # dns_msg = dns.message.from_wire(base64.b64decode(response.abuf))
        # print dns_msg

with open('%s/compiled_results.csv' % args.datadir, "wb") as res_file:
    csv_w = csv.writer(res_file)

    csv_w.writerow(['probe_id', 'res_time', 'ad_flag', 'ttl'])
    csv_w.writerows(compiled_results)

