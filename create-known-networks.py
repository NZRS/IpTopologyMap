__author__ = 'secastro'

"""Creates the file known-networks.json, to track prefixes that are not
   routable, but seen in the traces mostly used in Peering Exchanges.
   In the case where the IX architecture doesn't include their own AS,
   I create a fantasy one to complete the path.
   Some of this information comes from PeeringDB"""

import json

networks = [dict(net='202.7.0.0/23', group='9439'),  # WIX
            dict(net='192.203.154.0/24', group='9560'),  # APE
            dict(net='122.56.95.0/24', group='4648'),
            dict(net='122.56.99.0/24', group='4648'),
            dict(net='122.56.101.0/24', group='4648'),
            dict(net='122.56.110.0/24', group='4648'),
            dict(net='122.56.111.0/24', group='4648'),
            dict(net='122.56.116.0/24', group='4648'),
            dict(net='122.56.118.0/24', group='4648'),
            dict(net='122.56.222.0/24', group='4648'),
            dict(net='122.56.223.0/24', group='4648'),
            dict(net='122.56.224.0/24', group='4648'),
            dict(net='122.56.233.0/24', group='4648'),
            dict(net='122.56.234.0/24', group='4648'),
            dict(net='210.55.202.0/24', group='4648'),
            dict(net='122.56.127.0/24', group='4648'),
            dict(net='202.50.232.0/24', group='4648'),
            dict(net='202.50.233.0/24', group='4648'),
            dict(net='202.50.237.0/24', group='4648'),
            dict(net='203.96.120.0/24', group='4648'),
            dict(net='203.96.66.0/24', group='4648'),
            dict(net='202.50.234.0/24', group='4648'),
            dict(net='202.50.235.0/24', group='4648'),
            dict(net='202.50.237.0/24', group='4648'),
            dict(net='202.50.238.0/24', group='4648'),
            dict(net='203.96.66.246/32', group='45177'),
            dict(net='202.10.10.0/24', group='2764'),  # AAPT Australia
            dict(net='202.10.12.0/24', group='2764'),  # AAPT Australia
            dict(net='203.131.60.0/24', group='2764'),  # AAPT Australia
            dict(net='203.131.61.0/24', group='2764'),  # AAPT Australia
            dict(net='203.131.62.0/24', group='2764'),  # AAPT Australia
            dict(net='103.26.68.0/24', group='180000', country='NZ'),  # Megaport AKL
            dict(net='43.243.22.0/23', group='180000', country='NZ'), # Megaport AKL
            dict(net='43.243.21.0/24', group='180001', country='NZ'), # AKL-IX
            dict(net='206.72.210.0/23', group='180002'), # CoreSite Any2 California
            dict(net='198.32.176.0/24', group='180003', country='US'), # PAIX
            dict(net='218.100.52.0/24', group='180004'), # IX Australia NSW
            dict(net='218.100.54.0/24', group='180005'), # IX Australia SA
            dict(net='103.26.71.0/24', group='180006'), # Megaport Melbourne
            dict(net='202.167.228.0/24', group='180010', country='AU'), # Equinix Sydney
            dict(net='206.223.123.0/24', group='180011', country='US'), # Equinix LA
            dict(net='206.223.119.0/24', group='180012', country='US'), # Equinix Chicago
            dict(net='206.41.106.0/24', group='180013'), # AMS-IX Bay
            dict(net='206.51.41.0/24', group='180014'), # CoreSite Any2 NoCal
            dict(net='52.95.36.0/24', group='180015'), # AWS
            dict(net='218.100.21.0/24', group='9281'),
            dict(net='218.100.24.0/24', group='24388'),
            dict(net='202.174.183.0/24', group='24183'), # DTS New Zealand
            dict(net='125.236.34.0/24', group='4771'), # Spark NZ
            dict(net='222.152.45.0/24', group='4771'), # Spark NZ
            dict(net='198.32.146.0/24', group='13538'), # TeleHouse IIX
            dict(net='195.66.236.0/22', group='8714'), # LINX
            dict(net='206.197.187.0/24', group='12276'), # San Francisco Metropolitan IX
            dict(net='192.100.53.0/24', group='9872', country='NZ')  # Actrix Linknets
            ]

with open('data/known-networks.json', 'wb') as net_file:
    json.dump(networks, net_file)
