REL_DAY=20150201
DATADIR ?= data

all: ${DATADIR}/bgp.alchemy.json

analytics: ${DATADIR}/expanded-ip-path.json

data/$(REL_DAY).as-rel.txt:
	wget -O - http://data.caida.org/datasets/as-relationships/serial-1/$(REL_DAY).as-rel.txt.bz2 | bzip2 -cd > $@_
	mv $@_ $@

data/known-networks.json: create-known-networks.py
	python create-known-networks.py

${DATADIR}/measurements.json: data/probes.json data/nz-dest-addr.json data/known-sites.txt
	! test -d ${DATADIR} && mkdir -p ${DATADIR} && python probe-to-probe-traceroute.py --datadir ${DATADIR}

${DATADIR}/results.json: ${DATADIR}/measurements.json
	python fetch-results.py --datadir ${DATADIR}

${DATADIR}/bgp.json ${DATADIR}/ip.json ${DATADIR}/ip-path.json: ${DATADIR}/results.json data/known-networks.json analyze-results.py
	python analyze-results.py --datadir ${DATADIR} --sample

${DATADIR}/bgp.alchemy.json: prepare-for-alchemy.py ${DATADIR}/bgp.json
	python prepare-for-alchemy.py --datadir ${DATADIR} --relfile data/$(REL_DAY).as-rel.txt

${DATADIR}/ip-network-graph.js: ${DATADIR}/ip.json alchemy2vis.py
	python alchemy2vis.py --datadir ${DATADIR}

${DATADIR}/expanded-ip-path.json: path-analytics.py data/known-networks.json ${DATADIR}/ip-path.json
	python path-analytics.py --datadir ${DATADIR}

deploy-data: ${DATADIR}/bgp.alchemy.json
	rsync -a ${DATADIR}/bgp.alchemy.json /var/www/misc/data/nz-ip-map.json
	rsync -a scripts/map-config.js /var/www/scripts
	rsync -a html/credits.html /var/www/

deploy-test: ${DATADIR}/ip-network-graph.js html/ip-test.html
	mkdir -p /var/www/visjs/misc/data
	rsync -a bower_components/vis/dist/vis.map bower_components/vis/dist/vis.min.js /var/www/visjs/scripts/
	rsync -a bower_components/vis/dist/vis.css /var/www/visjs/styles/
	rsync -a ${DATADIR}/ip-network-graph.js /var/www/visjs/misc/data
	rsync -a html/ip-test.html /var/www/visjs
