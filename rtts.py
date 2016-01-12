__author__ = 'aaron'

import argparse
import json
from collections import defaultdict

def construct_paths(fname):
    '''
    Return a dict of IP address -> paths
    A path is a list of floats, where the float at index i
    is the time it took for the hop at index i to respond.
    If a hop didn't respond, its index will be "*"
    :param fname: name of file to read paths from.
    :return: { str : [[float]] }
    '''

    # Syntactic sugar. Returns true if a hop didn't respond.
    didnt_respond = lambda hop : "Hop" in hop["addr"]

    # A mapping of IP address -> [[float]].
    dest_paths = defaultdict(list)

    # Construct the paths and return.
    with open(fname, "rb") as f:
        traceroutes = json.load(f)
        for route in traceroutes:
            # Final destination of this traceroute.
            dest = route["path"][-1]["addr"]
            path = []
            for hop in route["path"]:
                if didnt_respond(hop): path.append("*")
                else: path.append(int(hop["rtt"]))
            dest_paths[dest].append(path)
    return dest_paths

def rtts(index, paths):
    '''
    Return the rtts for the specified index in the given paths.
    :param index: index of hop in the path to check.
    :param paths: list of paths to check.
    :return: float
    '''
    return rtt_deltas(0, index, paths) # rtt is the delta from origin to the index you want

def rtt_deltas(fst, snd, paths):
    '''
    Find the mean_rtt between two hops in the given paths.
    :param fst: index of first hop.
    :param snd: index of second hop.
    :param paths: list of paths to check.
    :return: the number of deltas and their sum.
    '''

    # Sanity check.
    if fst < snd: raise ValueError("Comparing two hops but first hop comes later than second hop.")

    # Syntactic sugar. Check if the two hops on the given path can be compared.
    cant_compare = lambda path : fst >= len(path) or snd >= len(path) or "*" in [path[fst], path[snd]]

    # Sum the deltas.
    deltas = []
    for path in paths:
        try:
            if "*" in path:
                print "break"
            if cant_compare(path): continue
            deltas.append(path[snd] - path[fst])
        except:
            print path[fst]
            print path[snd]
            print "break"

    return deltas

def rtt_links(path):
    '''
    Return a list containing the RTT between each pair of nodes in a path of rtts.
    :param path: a path of rtts.
    :return: [float], the rtts between each node in the path.
    '''
    links = []
    prev = path[0]
    for i in range(1, len(path)):
        curr = path[i]
        if "*" not in [prev, curr]:
            links.append(curr - prev)
        prev = curr
    return links

def mean(list): return 1.0 * sum(list) / len(list)
def mean_deltas(fst, snd, paths): return mean(rtt_deltas(fst, snd, paths))
def mean_rtts(paths): return mean(rtts(paths))

def list_concat(lists):
    return reduce(lambda x,y : x + y, lists)

def main():

    # Parse command-line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=str)
    args = parser.parse_args()
    DIR = "rtt-analysis/"

    # Create paths.
    ip2paths = construct_paths(args.input)
    with open(DIR + "rtts.json", "wb") as f:
        json.dump(ip2paths, f, indent=2, sort_keys=True)

    # Get size of largest path.
    largest = -1
    for p in ip2paths:
        if len(p) > largest: largest = len(p)

    # Aggregate all the paths into one.
    paths = list_concat(ip2paths.values())

    # Compute RTTs between links in each traceroute.
    link_rtts = [rtt_links(p) for p in paths]
    with open(DIR + "paths-link-rtts.json", "wb") as f:
        json.dump(link_rtts, f, indent=2, sort_keys=True)

    # Dump all link RTTs into a file.
    all_link_rtts = list_concat(link_rtts)
    with open(DIR + "all-link-rtts.json", "wb") as f:
        json.dump(all_link_rtts, f, indent=2)


if __name__ == "__main__":
    main()
