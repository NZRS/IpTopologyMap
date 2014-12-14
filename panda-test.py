__author__ = 'secastro'

import pandas as pd
import json
import numpy as np

# with open('data/probes.json', 'rb') as probe_file:
#    probe_list = json.load(probe_file)

origin_weight = pd.read_csv('data/relevant-origin.csv', sep="\t", header=None, names=('origin', 'weight'))
as_info = pd.read_json('data/second-as-list-info.json', orient="index")
as_info['origin'] = as_info.index
as_info.reset_index(level=0, inplace=True)
df2 = origin_weight.merge(as_info)

probe_df = pd.read_json('data/probes.json', orient="records")
df3 = probe_df.groupby('asn_v4').size().to_frame()
df3.reset_index(level=0, inplace=True)
df3.columns = ['origin', 'count']
df4 = df2.merge(df3, how='left')
print df4.sort(columns='weight', ascending=False).head(20)