DATADIR ?= data
PRIM_COUNTRIES ?= NZ
SEC_COUNTRIES ?= AU
TRACE_SAMPLE_RATE ?= 0.5
SCANDIR=${DATADIR}/scans
PROD_DIR=/usr/share/nginx/ip-map/
PROD_VIS_DIR=/usr/share/nginx/ip-map/
SELECTED_TOPOLOGY_DATA=data/country-aspath-selection.json
DEST_DIR?=ES-20160914
PROD_DEST_DIR=${PROD_VIS_DIR}/${DEST_DIR}

all: ${DATADIR}/bgp.alchemy.json

analytics: ${DATADIR}/expanded-ip-path.json

retry: ${DATADIR}/retry.json

data/known-networks.json: create-known-networks.py
	python2 create-known-networks.py

GeoIPASNum.dat.gz:
	wget -N http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz

data/GeoIPASNum.dat: GeoIPASNum.dat.gz
	gzip -cd $? > $@

${DATADIR}/RIR-resources.json: RIR/extract-country-data-from-delegation.py ${DATADIR}/config.json
	cd RIR && make CONFIG=../${DATADIR}/config.json OUTFILE=../$@ extract && cd ..

config.json: ${DATADIR}/config.json

${DATADIR}/config.json: create-config.py
	mkdir -p ${DATADIR}
	./create-config.py --datadir ${DATADIR} --primary ${PRIM_COUNTRIES} --secondary ${SEC_COUNTRIES}

${DATADIR}/probes.json: list-atlas-probes.py ${DATADIR}/config.json
	./list-atlas-probes.py --datadir ${DATADIR}

${SCANDIR}/downloaded.txt: download-scan-data.py
	mkdir -p ${SCANDIR}
	./download-scan-data.py --datadir ${SCANDIR}
	touch $@

${DATADIR}/dest-addr.json: find-targets-from-scans.py ${SCANDIR}/downloaded.txt ${DATADIR}/RIR-resources.json
	python2 find-targets-from-scans.py --scandir ${SCANDIR} --datadir ${DATADIR}

known-sites.json: ${DATADIR}/known-sites.json

${DATADIR}/known-sites.json: fetch-alexa-top-sites.py ${DATADIR}/config.json
	./fetch-alexa-top-sites.py --datadir ${DATADIR}

msm-config: ${DATADIR}/probes.json ${DATADIR}/dest-addr.json ${DATADIR}/known-sites.json

${DATADIR}/retry.json: ${DATADIR}/failed-msm.json
	./probe-to-probe-traceroute.py --datadir ${DATADIR} --retry

${DATADIR}/measurements.json: ${DATADIR}/probes.json ${DATADIR}/dest-addr.json ${DATADIR}/known-sites.json
	./probe-to-probe-traceroute.py --datadir ${DATADIR} --sample ${TRACE_SAMPLE_RATE}

${DATADIR}/results.json: ${DATADIR}/measurements.json
	python2 fetch-results.py --datadir ${DATADIR}

peeringdb: ${DATADIR}/peeringdb-dump.json

${DATADIR}/peeringdb-dump.json: get-pdb-info.py
	./get-pdb-info.py --datadir ${DATADIR}

${DATADIR}/remapped-addresses.json: map-addresses.py
	python2 map-addresses.py --datadir ${DATADIR}

${DATADIR}/bgp.json ${DATADIR}/ip.json ${DATADIR}/ip-path.json: ${DATADIR}/results.json\
        data/known-networks.json analyze-results.py data/GeoIPASNum.dat\
        ${DATADIR}/peeringdb-dump.json ${DATADIR}/remapped-addresses.json
	python2 analyze-results.py --datadir ${DATADIR} --sample 100

${DATADIR}/vis-bgp-graph.json ${DATADIR}/vis-bgp-graph.js: prepare-for-alchemy.py ${DATADIR}/bgp.json
	python2 prepare-for-alchemy.py --datadir ${DATADIR}

${DATADIR}/node-position.json: run-physics-simulation.py ${DATADIR}/vis-bgp-graph.json
	python2 run-physics-simulation.py --datadir ${DATADIR}

${DATADIR}/full-network.json: merge-network-layout.py ${DATADIR}/node-position.json
	python2 merge-network-layout.py --datadir ${DATADIR}

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
	rsync -a bower_components/vis/dist/vis.map bower_components/vis/dist/vis.min.js bower_components/vis/dist/vis.js /var/www/visjs/scripts/
	rsync -a bower_components/vis/dist/vis.css /var/www/visjs/styles/
	rsync -a ${DATADIR}/ip-network-graph.js /var/www/visjs/misc/data
	rsync -a html/ip-test.html /var/www/visjs

deploy-vis-bgp: ${DATADIR}/full-network.json html/vis-bgp-test.html
	mkdir -p /var/www/visjs/misc/data
	rsync -a ${DATADIR}/full-network.json /var/www/visjs/misc/data
	rsync -a html/vis-bgp-test.html /var/www/visjs

deploy-prod-vis-bgp: ${DATADIR}/full-network.json html/vis-bgp-test.html
	ssh bgp-map "mkdir -p ${PROD_DEST_DIR}/data"
	rsync -a ${DATADIR}/full-network.json bgp-map:${PROD_DEST_DIR}/data/
	rsync -a html/vis-bgp-test.html bgp-map:${PROD_DEST_DIR}/index.html

deploy-prod-poc: ${DATADIR}/ip-network-graph.js html/ip-test.html
	ssh bgp-map "mkdir -p ${PROD_DIR}/misc/data ${PROD_DIR}/scripts ${PROD_DIR}/styles"
	rsync -a bower_components/vis/dist/vis.map bower_components/vis/dist/vis.min.js bower_components/vis/dist/vis.js bgp-map:${PROD_DIR}/scripts/
	rsync -a bower_components/vis/dist/vis.css bgp-map:${PROD_DIR}/styles/
	rsync -a ${DATADIR}/ip-network-graph.js bgp-map:${PROD_DIR}/misc/data/
	rsync -a html/ip-test.html bgp-map:${PROD_DIR}/poc/index.html
