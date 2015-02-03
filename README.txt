How to create measurements.

1. Run atlas-nz-probes.py to update the list of probes
2.Run probe-to-probe-traceroute.py --datadir <DATADIR> to order the execution of a measurement between all probes. The measurement IDs will be saved into the specified directory.
3. fetch-results.py --datadir <DATADIR> will fetch the results for the measurements ID saved in the specific directory
4. analyze-results.py --datadir <DATADIR> will combine and analyze the results present in the specified directory