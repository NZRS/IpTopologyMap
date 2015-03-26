REL_DAY=20150201
DATADIR ?= data

as-rank/$(REL_DAY).as-rel.txt:
	wget -O - http://data.caida.org/datasets/as-relationships/serial-1/$(REL_DAY).as-rel.txt.bz2 | bzip2 -cd > $@_
	mv $@_ $@

data/known-networks.json: create-known-networks.py
	python create-known-networks.py

${DATADIR}/results.json: ${DATADIR}/measurements.json
	python fetch-results.py --datadir ${DATADIR}

${DATADIR}/bgp.json: ${DATADIR}/results.json data/known-networks.json
	python analyze-results.py --datadir ${DATADIR}

${DATADIR}/bgp.alchemy.json: prepare-for-alchemy.py ${DATADIR}/bgp.json
	python prepare-for-alchemy.py --datadir ${DATADIR}

deploy-data: ${DATADIR}/bgp.alchemy.json
	rsync -av ${DATADIR}/bgp.alchemy.json /var/www/misc/data
