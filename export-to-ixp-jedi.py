import json
import argparse
import os
from ripe.atlas.cousteau import Probe, Measurement
from collections import defaultdict

""" export-to-ixp-jedi.py
    Takes the set of files created by an IP Topology Map run and converts
    them to the structure expected by the IXP Country Jedi to generate the
    visualization and analysis
"""

def dpath(fname):
    return os.path.join(args.datadir, fname)

def epath(fname):
    return os.path.join(args.exportdir, fname)


parser = argparse.ArgumentParser("Exports IP Topology Map datafiles into IXP "
                                 "Country Jedi format")
parser.add_argument('--datadir', required=True,
                    help="directory to read files")
parser.add_argument('--exportdir', required=True,
                    help="Directory to save files")
args = parser.parse_args()


# Step 1: Read config file and generate config file
print("Exporting config")
if os.path.isfile(epath('config.json')):
    print("\tSkipping, config already exists")
else:
    with open(dpath('config.json')) as in_conf, open(epath('config.json'),
                                                     'wb') as out_conf:
        config = json.load(in_conf)
        new_conf = {'country': config['PrimaryCountry']}
        json.dump(new_conf, out_conf)

# Step 2: Generate the list of probes
print("Exporting probe info")
if os.path.isfile(epath('probeset.json')):
    print("\tSkipping, probeset already exists")
else:
    with open(dpath('probes.json')) as in_prb, \
            open(epath('probeset.json'), 'wb') as out_prb:
        in_prb_set = json.load(in_prb)
        out_prb_set = []
        for cc, probe_list in in_prb_set.iteritems():
            for prb in probe_list:
                # Fetch the full info from the probe as we don't keep as much as IXP
                # Jedi needs
                probe_info = Probe(id=prb['id'])
                out_prb_set.append({'country_code': cc,
                                    'dists': {},
                                    'tags': probe_info.tags,
                                    'asn_v4': probe_info.asn_v4,
                                    'asn_v6': probe_info.asn_v6,
                                    'address_v4': probe_info.address_v4,
                                    'address_v6': probe_info.address_v6,
                                    'probe_id': probe_info.id,
                                    'lat': probe_info.geometry['coordinates'][0],
                                    'lon': probe_info.geometry['coordinates'][1]
                                    })

        json.dump(out_prb_set, out_prb)

if os.path.isfile(epath('measurementset.json')):
    print("\tSkipping, measurement file already exists")
else:
    # Step 3a: Read the list of measurements and identify the ones corresponding
    # to the probe-mesh
    print("Finding measurements")
    stage_msm = defaultdict(list)
    with open(dpath('measurements.json')) as in_msm_file:
        msm_dict = json.load(in_msm_file)
        for cc, msm_list in msm_dict.iteritems():
            for msm_id in msm_list:
                msm_info = Measurement(id=msm_id)
                tag, descr = msm_info.description.split(':')
                stage = tag.split('_')[-1]
                stage_msm[stage].append(msm_id)

    print("Exporting measurements")
    new_msm_set = set()
    with open(dpath('results.json')) as in_msm_file, \
        open(epath('measurementset.json'), 'wb') as out_msm_file:
        in_msm = json.load(in_msm_file)
        for cc, msm_list in in_msm.iteritems():
            for old_msm in msm_list:
                if old_msm['msm_id'] in stage_msm['S1']:
                    new_msm_set.add((old_msm['dst_name'], old_msm['msm_id']))

        print("%d measurements to save" % len(new_msm_set))
        json.dump({'v6': [],
                   'v4': [{'dst': d,
                           'msm_id': m,
                           'type': 'probe-mesh'} for d, m in new_msm_set]},
                  out_msm_file)

# Step 4, export the information we have about IXs in the country and feed it
#  into basedata
print("Exporting updated basedata")
peering_lan = {}
base = {}
with open(dpath('peeringdb-dump.json')) as in_pdb_file,\
        open(epath('basedata.json')) as in_base_file:
    pdb = json.load(in_pdb_file)
    base = json.load(in_base_file)
    # Iterate over the list of IXs and generate a structure suitable for
    # basedata
    for ix in pdb:
        if ix['country'] in base['countries']:
            peering_lan[ix['name']] = {'peeringlans': ix['ixpfx']}

# Overwrite the ixps entry in the basedata
base['ixps'] = peering_lan
with open(epath('basedata.json'), 'wb') as out_base_file:
    json.dump(base, out_base_file, indent=2)
