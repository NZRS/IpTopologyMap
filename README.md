# IP Topology Map

Tool to generate a visual representation of BGP peering, derived for a large 
number of traceroutes generated using the RIPE Atlas network.

Intended to generate the topology map of a country, by using active probing 
and a variety of data sources.

## Requirements

Listed in the requirements.txt file. You will also need to install:

CAIDA BGPstream
https://bgpstream.caida.org

MaxMind GeoIP
https://www.maxmind.com/en/geoip2-services-and-databases

## Methodology

Using all the active RIPE Atlas probes in a given country, it will use three 
sets to generate a number of ICMP traceroutes.

1. From each RIPE Atlas probe, to any other probe in the country
2. Using data from BGP, identify the list of active network prefixes and 
search for live addresses using data from scans.io
3. Using the Top 100 Sites according to Alexa. This is helpful to detect the 
presence of CDNs.

A one-off traceroute will be executed and later results collected. By 
combining all the resulting traceroutes, a complete view of the topology can 
be achieved. By mapping addresses to their ASNs, the peering relationships 
can be found. An special work has been done to mark the IX used in the 
country, with information from PeeringDB.

## How to run

General form is:

```
make DATADIR=data/map_for_my_country PRIM_COUNTRIES=my_country 
SEC_COUNTRIES=other_countries deploy-vis-bgp
```

For example, to generate the map for New Zealand (NZ) and giving Australian 
organizations a distinctive color:

```
make DATADIR=data/test_$(date +%F)_NZ PRIM_COUNTRIES=NZ SEC_COUNTRIES=AU deploy-vis-bgp
```

The primary country is the country used to determine the destinations for the
 traceroutes. The secondary country(ies) is/are used to color them 
 distinctively when it's relevant for analysis purposes.
 
## Caveats

The Internet is a wild place. In many cases traceroutes don't reach their 
final destinations, or packets are filtered in the path. In some cases some 
addresses are not mappable to their origin AS as they are for transit and not announced 
in the BGP table. This code does some effort to map as much as possible, and 
to handle border cases in a sensible way.

## Acknowledgements

This work has been developed in parallel with [IXP Country Jedi]
(https://github.com/emileaben/ixp-country-jedi) and shares a few ideas. We'd 
like to appreciate the discussions with Emile Aben, the author, about pros 
and cons of doing things in certain way.

To obtain BGP data, this tool is using [BGPStream](https://github
.com/CAIDA/bgpstream) from [CAIDA](https://www.caida.org)

To map addresses to country and origin AS, uses [GeoIP](https://www.maxmind.com)

To visualize the topology, uses the excellent JavaScript library [VisJS]
(http://visjs.org/)
