__author__ = 'secastro'

import json
import random
from ripe.atlas.sagan import TracerouteResult
from collections import Counter

with open('data/final_test_1/results.json', 'rb') as res_fd:
    res_blob = random.sample(json.load(res_fd), 50)

for res in res_blob:
    print "=" * 30
    sagan_res = TracerouteResult(res)

    for h in reversed(sagan_res.hops):
        rtt_sum = Counter()
        rtt_cnt = Counter()
        for p in h.packets:
            if p.origin is None:
                continue

            if p.rtt is not None:
                rtt_sum[p.origin] += p.rtt
                rtt_cnt[p.origin] += 1

            print p.origin, p.rtt

        for a in rtt_cnt:
            print "** ", a, rtt_sum[a] / rtt_cnt[a]

    print "\n"
