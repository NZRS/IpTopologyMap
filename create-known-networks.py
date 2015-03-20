__author__ = 'secastro'

import json

networks = [dict(net='202.7.0.0/23', group='9439'), # WIX
            dict(net='192.203.154.0/24', group='9560'), # APE
            dict(net='122.56.116.0/24', group='4648'),
            dict(net='122.56.223.0/24', group='4648'),
            dict(net='122.56.118.0/24', group='4648'),
            dict(net='122.56.222.0/24', group='4648'),
            dict(net='122.56.233.0/24', group='4648'),
            dict(net='122.56.234.0/24', group='4648'),
            dict(net='210.55.202.0/24', group='4648'),
            dict(net='122.56.127.0/24', group='4648'),
            dict(net='202.50.232.0/24', group='4648'),
            dict(net='202.50.233.0/24', group='4648'),
            dict(net='203.96.120.0/24', group='4648'),
            dict(net='203.96.66.0/24', group='4648'),
            dict(net='202.50.234.0/24', group='4648'),
            dict(net='202.50.235.0/24', group='4648'),
            dict(net='202.50.238.0/24', group='4648'),
            dict(net='203.96.66.246/32', group='45177'),
            dict(net='103.26.68.0/24', group='180000'), # Megaport
            dict(net='43.243.22.0/23', group='180000'), # Megaport
            dict(net='202.167.228.0/24', group='180010'), # Equinix Sydney
            dict(net='43.243.21.0/24', group='180001'), # AKL-IX
            dict(net='198.32.176.0/24', group='180003'), # PAIX
            dict(net='206.72.210.0/23', group='180002'), # CoreSite Any2 California
            dict(net='218.100.21.0/24', group='9281'),
            dict(net='218.100.24.0/24', group='24388'),
            dict(net='222.152.45.0/24', group='4771')
            ]

with open('data/known-networks.json', 'wb') as net_file:
    json.dump(networks, net_file)
