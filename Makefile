REL_DAY=20150201
DATADIR ?= data

data/$(REL_DAY).as-rel.txt:
	wget -O - http://data.caida.org/datasets/as-relationships/serial-1/$(REL_DAY).as-rel.txt.bz2 | bzip2 -cd > $@_
	mv $@_ $@

data/known-networks.json: create-known-networks.py
	python create-known-networks.py

${DATADIR}/measurements.json: data/probes.json data/nz-dest-addr.json data/known-sites.txt
	! test -d ${DATADIR} && mkdir -p ${DATADIR} && python probe-to-probe-traceroute.py --datadir ${DATADIR}

${DATADIR}/results.json: ${DATADIR}/measurements.json
	python fetch-results.py --datadir ${DATADIR}

${DATADIR}/bgp.json: ${DATADIR}/results.json data/known-networks.json
	python analyze-results.py --datadir ${DATADIR}

${DATADIR}/bgp.alchemy.json: prepare-for-alchemy.py ${DATADIR}/bgp.json
	python prepare-for-alchemy.py --datadir ${DATADIR} --relfile data/$(REL_DAY).as-rel.txt

deploy-data: ${DATADIR}/bgp.alchemy.json
	rsync -a ${DATADIR}/bgp.alchemy.json /var/www/misc/data/nz-ip-map.json
	rsync -a scripts/map-config.js /var/www/scripts
	rsync -a html/credits.html /var/www/
