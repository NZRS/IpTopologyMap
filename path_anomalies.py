__author__ = 'aaron'

import geoloc
import json
import argparse

def main():
    '''
    Example usage
        python path_anomalies --input data/final_test_1/ip-path.json --output anomalies
    '''
    parser = argparse.ArgumentParser("Detects anomalous geolocation results")
    parser.add_argument('--input', required=True, help="File to check")
    parser.add_argument('--output', required=True, help="File to dump results to")
    args = parser.parse_args()

    # load files.
    print "Loading input file..."
    paths = None
    with open(args.input, "rb") as file:
        paths = json.load(file)
    print "Loading geolocation databases..."
    geoloc.quickload()
    geoloc.oracle("known_networks") # considered authoritative source
    print "Finished loading\n"

    # if address field has these strings in it, its value could not be determined
    print "Checking anomalies..."

    # undecidables should be ignored
    undecidables = ["Probe", "Private", "Hop"]
    def undecidable(addr):
        for unk in undecidables:
            if unk in addr: return True
        return False

    # each probe is a single JSON entry
    probe2anomalies = {}

    # check each path
    for path in paths:
        hops = path['path']
        probe = hops[0]['addr']
        anomalies = []
        for hop in hops[1:]:
            ip_addr = hop['addr']
            if undecidable(ip_addr): continue
            elif geoloc.anomalous(ip_addr): anomalies.append(ip_addr)

        #if probe in probe2anomalies:
        #    print "Name clash! Two probes are called {}.".format(probe)

        # don't record pure traces
        if len(anomalies) == 0: continue

        # record
        probe_obj = {
            'length_trace' : len(hops),
            'ips_anomalous' : anomalies,
            'num_anomalies' : len(anomalies),
        }
        probe2anomalies[probe] = probe_obj
    print "Finished checking anomalies\n"

    # output to file
    print "Outputting to {}".format(args.output)
    with open(args.output, "wb") as file:
        json.dump(probe2anomalies, file, indent=2, sort_keys=True)
    print "Finished anomaly check\n"

    print "Checked {} traces".format(len(paths))
    pct = 100.0 * len(probe2anomalies) / len(paths)
    print "Found {} traces with potential anomalies ({:.4f}%)".format(len(probe2anomalies), pct)


#ip-path.json
if __name__ == "__main__":
    main()
