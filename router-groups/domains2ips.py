__author__ = 'aaron'

import json

#  Construct an IP -> Domain mapping.
with open("reverse-lookup.json", "rb") as f:
    domain2ip = json.load(f)
    ips2domains = { v["name"]:k for k,v in domain2ip.items() }

# Load domain groupings to be converted.
with open("domains-grouped.json", "rb") as f:
    companies = json.load(f)

# Lists of IPs which should be grouped together.
ips2routers = {}

# Turn domains back into IPs.
for company in companies:
    print company
    routers = companies[company]
    for router in routers:
        if router == "?": continue
        for domain in routers[router]:
            ip = ips2domains[domain]
            ips2routers[ip] = router

# Output.
with open("ip2router.json", "wb") as f:
    json.dump(ips2routers, f, indent=2)