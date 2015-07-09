__author__ = 'aaron'

import json

#  Construct an IP -> Domain mapping.
with open("map", "rb") as f:
    domain2ip = json.load(f)
    ips2domains = { v["name"]:k for k,v in domain2ip.items() }

# Load domain groupings to be converted.
with open("domains-grouped.json", "rb") as f:
    companies = json.load(f)

# Lists of IPs which should be grouped together.
groups = []

# Turn domains back into IPs.
for company in companies:
    print company
    routers = companies[company]
    for router in routers:
        if router == "?": continue
        domains = routers[router]
        ips = [ips2domains[x] for x in domains]
        groups.append(ips)

# Output.
with open("reverse-lookup.json", "wb") as f:
    json.dump(groups, f, indent=2)