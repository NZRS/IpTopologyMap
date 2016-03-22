__author__ = 'aaron'

import json
from math import exp
from collections import defaultdict

def transfer_dx(x):
    '''
    Derivative of the transfer function w.r.t. x
    :param x:
    :return:
    '''
    transfer(x) * (1 - transfer(x))

def transfer(x):
    1.0/(1 + exp(-x))

class Network(object):

    def __init__(self, inputs, outputs, nodes):
        self.inputs = inputs
        self.outputs = outputs
        self.nodes = nodes

    @staticmethod
    def from_json(self, fname):
        '''
        Construct a network from the paths in the given file. The file should specify the
        nodes in the network by the traceroute paths. For example:
           [ip1, ip2, ip3],
           [ip4, ip5, ip6], ...
        :param fname: name of file.
        :return: a Network object.
        '''
        with open(fname, "rb") as f:
            traceroutes = json.load(f)

            # Get paths.
            paths, rtt_deltas = [], []
            for route in traceroutes:
                paths.append(route["path"])
                rtt_deltas.append(route["rtt_deltas"])

            # Figure out longest path length.
            path_len = -1
            for p in paths:
                if len(p) > path_len: path_len = len(p)

            # All nodes indexed by their name.
            nodes = defaultdict(lambda name : Node(name))

            # Construct edges.
            for path, deltas in zip(paths, rtt_deltas):
                for i, name in enumerate(path):
                    curr_node = nodes[name]
                    if i == 0: continue
                    delta = rtt_deltas[i-1]
                    prev_node = nodes[path[i-1]]
                    prev_node.add_next_node(curr_node, delta)
                    curr_node.add_prev_node(prev_node, delta)

            # Find input and output nodes.
            input_nodes, output_nodes = set(), set()
            for node in nodes:
                if len(node.prev_nodes) == 0: input_nodes.add(node)
                if len(node.next_nodes) == 0: output_nodes.add(node)

            return Network(input_nodes, output_nodes, nodes.values())

    def back_propagation(self):
        '''
        Perform back_propagation for the errors.
        :return: a mapping of pairs of nodes to their error/update value.
        '''
        pass


class Node(object):
    '''
    Represents a single node in a traceroute.
    '''

    def __init__(self, name):
        '''
        :param name: Unique identifying name for node (e.g.: ip address or router name)
        '''
        self.ip = name
        # these are dicts of node : float
        self.prev_nodes = {} # nodes in previous layer -> rtt from that node to prev node
        self.next_nodes = {} # nodes in next layer -> rtt from this node to next node
        self.reset()

    def add_next_node(self, node, weight):
        self.next_layer[node] = weight

    def add_prev_node(self, node, weight):
        self.prev_layer[node] = weight

    def __hash__(self):
        return self.ip.__hash__()

    def __eq__(self, other):
        if type(other) != Node: return False
        return other.ip == self.ip


