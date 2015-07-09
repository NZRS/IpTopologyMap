__author__ = 'aaron'

import json
import router_regex as rout
import re
import argparse
from collections import defaultdict

rgx = None
regexes = { x : re.compile(rout.regex_company(x), re.IGNORECASE) for x in rout.companies }

def frouter(company, domain):
    '''
    Figure out router for the given domain name belonging to the
    specified company.
    :param company: company who owns the domain.
    :param domain: it is what it is.
    :return: string
    '''

    # XXXXXX.wnmur-rt1.fx.net.nz --> wnmur-rt1
    if company == "fx":
        domain = re.search(regexes["fx"], domain).group()
        return domain.rstrip(".fx.net.nz")

    elif company == "snap":
        return "?"

    # XXXXXXXX.akl05.akl.VOCUS.net.nz --> akl105.akl
    elif company == "vocus":
        domain = re.search(regexes["vocus"], domain).group()
        domain = domain.split(".")
        return domain[0] + domain[1]

    elif company == "nzix":
        return "?"

    # XXXXXXXXX.v4wlg0.acsdata.co.nz --> v4wlg0
    elif company == "acsdata":
        domain = re.search(regexes[company], domain).group()
        domain = domain.split(".")
        return domain[0]

    else:
        return "?"

def fcompany(domain):
    '''
    Figure out the company owning the domain.
    :param domain: the domain.
    :return: string
    '''

    # Check among existing regexes.
    for company, regex in regexes.items():
        if re.search(regex, domain) is not None:
            return company

    # If there isn't one, take company name by stripping hld.
    zones = domain.split(".")

    if zones[-1] == "net": return ".".join(zones[-2:])
    else: return ".".join(zones[-3:])

def main():

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="domains to classify")
    args = parser.parse_args()

    # load data
    with open(args.input, "rb") as f:
        domains = json.load(f)

    # { str : {str : [str]} }
    # { company : {router : [domains]} }
    dataframe = defaultdict(lambda : defaultdict(list))
    # for example:
    # {
    #   "fx" : {
    #     "aktnz-rt1" : [abcdefg.aktnz-rt1.fx.net.nz, hijklmn.aktnz-rt1.fx.net.nz],
    #     "aktnz-rt2" : [XXXXX.aktnz-rt2.fx.net.nz]
    #   },
    #   "vocus" : {
    #     ...
    #   },
    #   ...
    # }

    # build the dataframe
    for domain in domains:
        company = fcompany(domain)
        router = frouter(company, domain)
        dataframe[company][router].append(domain)

    # output
    output_fname = args.input[:-5] + ("-grouped.json")
    with open(output_fname, "wb") as f:
        json.dump(dataframe, f, indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
