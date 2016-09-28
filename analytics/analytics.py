__author__ = 'secastro'
__author__ = 'aj'

import json
import argparse
from collections import Counter
from collections import defaultdict
from operator import itemgetter
import geoloc
import os

dest_cc = 'NZ'
unk_cc  = '*' # cc of a private ip address, etc.
mystery_cc = '!' # cc which could not be geolocated

OUTPUT_DIR = "analytics"
PATHS = None


def path2string(p):
    return "\n".join(["{0:>6} {1:>10} {2:15} {3:.2f}".format(e.get('country', '++'), e['asn'], e['addr'], e['rtt']) for e in p])
    # return "\n".join(["{country:>6} {asn:>10} {addr}".format(e) for e in p])


def geolocation_anomalies():
    '''
    Look for potential ip addresses in the traces whose geolocations are in dispute.
    Saves results in potential-anomalies.json
    :param paths: paths to check.
    '''

    global PATHS
    potential_anomalies = {}
    for path in PATHS:
        for hop in path['path']:
            addr = hop["addr"]
            if undecidable(addr): continue
            georesult = geoloc.country_code_all(addr, filter_nones=True)
            if "known_networks" in georesult: continue # authoritative answer
            unique_answers = list(set(georesult.values()))
            if len(unique_answers) == 1: continue # definitive answer
            potential_anomalies[addr] = unique_answers

    global OUTPUT_DIR
    with open(OUTPUT_DIR + "/potential-anomalies.json", "wb") as f:
        json.dump(potential_anomalies, f, indent=2)


def cc(ip_addr, asn):
    '''
    Find the best potential geolocation for the ip address with the given asn number.
    :param ip_addr: address
    :param asn: its asn number
    :return:
    '''
    if asn in ['9560']: return "NZ"
    if "Probe" in ip_addr: return "NZ"
    if "Private" in ip_addr or "Hop" in ip_addr: return unk_cc
    results = geoloc.country_code_all(ip_addr, filter_nones=True)
    if "known_networks" in results: return results["known_networks"]
    if "geoip" in results: return results["geoip"]
    if "ip2location" in results: return results["ip2location"]
    return mystery_cc # could not geolocate

def tag_countries():
    '''
    Tag all countries in the paths with their geolocation.
    :param paths:
    '''
    global PATHS
    for path in PATHS:
        for hop in path['path']:
            addr, asn = hop["addr"], hop["asn"]
            hop["country"] = cc(addr, hop["asn"])

def deviation_paths():
    '''
    Find all paths that contain deviations. Output to deviations-paths.json
    :param paths: the paths to check.
    '''
    global PATHS
    stroutput = []
    for path in PATHS:
        source, goal = path["path"][0], path["path"][-1]
        if source != goal and goal != unk_cc:
            continue
        departed = False
        for hop in path["path"]:
            if hop["country"] not in [dest_cc, unk_cc]:
                departed = True
                break
        if departed:
            stroutput.append(path2string(path["path"]))

    global OUTPUT_DIR
    with open(OUTPUT_DIR + "/deviation-paths.json", "wb") as f:
        for path in stroutput:
            f.write(path + "\n")
            f.write("\n")

    return len(stroutput)

def undecidable(addr):
    return "Private" in addr or "Hop" in addr or "Probe" in addr

def deviation_hops():
    '''
    Find all hops from an NZ location to a non-NZ location. Output to
    deviations-hops.json
    :param paths: the paths to check.
    '''

    global PATHS

    # keep track of where deviation hops end up
    destinations = {}

    # list of all hops which deviate
    deviation_hops = []

    for path in PATHS:
        source, goal = path["path"][0], path["path"][-1]
        prev_cc, prev_ip, prev_asn = dest_cc, None, None

        for hop in path["path"]:

            cc, addr, asn = [hop[x] for x in ["country", "addr", "asn"]]

            # hop to another country
            if cc not in [dest_cc, unk_cc] and prev_cc in [dest_cc] and not undecidable(addr):
                deviation_hops.append({ "foreign_cc" : cc,
                                        "foreign_ip" : addr,
                                        "foreign_asn" : asn,
                                        "domestic_cc" : prev_cc,
                                        "domestic_ip" : prev_ip,
                                        "domestic_asn" : prev_asn,
                                        "origin" : source,
                                        "goal" : goal })

                # update destinations dict
                if addr not in destinations:
                    destinations[addr] = { "count" : 1, "country" : cc }
                else:
                    destinations[addr]["count"] += 1

            prev_asn, prev_ip, prev_cc = asn, addr, cc

    global OUTPUT_DIR
    with open(OUTPUT_DIR + "/deviation-hops.json", "wb") as f:
        json.dump(deviation_hops, f, indent=2, sort_keys=True)
    with open(OUTPUT_DIR + "/deviation-hop-destinations.json", "wb") as f:
        json.dump(destinations, f, indent=2)

    return len(destinations)

def facts(num_bad_paths, num_unique_destinations):
    '''
    Output some facts about number of anomalies, deviations, etc.
    :param paths: paths to check.
    '''
    global PATHS
    global OUTPUT_DIR
    with open(OUTPUT_DIR + "/facts.txt", "wb") as f:
        pct_bad_paths = 1.0 * num_bad_paths / len(PATHS)
        pct = round(pct_bad_paths, 2)
        f.write("{}/{} paths departed {} ({}%)\n".format(num_bad_paths,
                                                        len(PATHS),
                                                         dest_cc, pct))
        f.write("Hops went to {} unique IPs.".format(num_unique_destinations))

def main():

    # Parse cmd args
    parser = argparse.ArgumentParser("Analyses IP Path data")
    parser.add_argument('--data-dir', required=True,
                        help="directory to read generic data files")
    parser.add_argument('--path-dir', required=True,
                        help="Directory to read IP paths and save analytics")
    parser.add_argument('--country', required=False, default='NZ',
                        help="Country to analyze paths against")
    args = parser.parse_args()

    global OUTPUT_DIR
    OUTPUT_DIR = os.path.join(args.path_dir, 'analytics')
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    dest_cc = args.country

    # Set up geolocation stuff
    print "Loaded geolocation data."
    geoloc.load_db("geoip", args.data_dir + "/GeoIP.dat")
    geoloc.load_db("ip2location", args.data_dir + "/IP-COUNTRY.bin")
    geoloc.load_db("known_networks", args.data_dir + "/known-networks.json")

    # Load traced paths
    print "Loaded paths."
    global PATHS
    with open("{}/ip-path.json".format(args.path_dir), 'rb') as ip_file:
        PATHS = json.load(ip_file)

    print "Running analytics. (0/5)"

    # Figure out potential geolocation anomalies.
    geolocation_anomalies()
    print "Finished finding geolocation anomalies. (1/5)"

    # Tag each hop with the country returned by known_networks or GeoIP.
    tag_countries()
    print "Finished tagging countries. (2/5)"

    # Extract/output paths which have deviations.
    num_bad_paths = deviation_paths()
    print "Finished finding deviating paths. (3/5)"

    # Extract/output hops to other countries.
    num_unique_destinations = deviation_hops()
    print "Finished finding deviating hops. (4/5)"

    # Some facts about number of anomalies, deviations, etc.
    facts(num_bad_paths, num_unique_destinations)
    print "Finished printing facts. (5/5)"

    print "Finished all."

if __name__ == "__main__":
    main()
