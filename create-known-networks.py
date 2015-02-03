__author__ = 'secastro'

import json

networks = [dict(net='202.7.0.0/23', group='WIX'), dict(net='192.203.154.0/24', group='APE'),
            dict(net='122.56.116.0/24', group='AS4648'), dict(net='122.56.223.0/24', group='AS4648'),
            dict(net='122.56.118.0/24', group='AS4648'), dict(net='122.56.222.0/24', group='AS4648'),
            dict(net='122.56.233.0/24', group='AS4648'), dict(net='122.56.234.0/24', group='AS4648'),
            dict(net='210.55.202.0/24', group='AS4648'), dict(net='122.56.127.0/24', group='AS4648'),
            dict(net='203.96.66.246/32', group='AS45177'), dict(net='103.26.68.0/24', group='Megaport'),
            dict(net='43.243.22.14/32', group='Megaport'), dict(net='202.167.228.0/24', group='Equinix'),
            dict(net='202.50.232.0/24', group='AS4648'), dict(net='202.50.233.0/24', group='AS4648'),
            dict(net='203.96.120.0/24', group='AS4648'), dict(net='203.96.66.0/24', group='AS4648'),
            dict(net='202.50.234.0/24', group='AS4648'), dict(net='43.243.21.0/24', group='NZ-AKL-IX')]

with open('data/known-networks.json', 'wb') as net_file:
    json.dump(networks, net_file)
