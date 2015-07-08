Some of the routers in the traceroutes have multiple aliases. This folder is dedicated to locating those.

files:

router_regex.py
---------------
This contains a regex for matching various NZ routers. The main use of interest is
router_regex.regex(), which returns a compiled regex which pattern matches each on the
routers.

router_group.py
---------------
Takes as input a file containing a .json list of domains. It then outputs the domains
but grouped by company and router ("?" denotes an unknown router/company). Run like
so:   python router_group.py --input nz-domains.json
  


