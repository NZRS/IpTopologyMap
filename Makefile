REL_DAY=20150201
DATADIR ?= data
SCANDIR=${DATADIR}/scans
PROD_DIR=/usr/share/nginx/ip-map/
PROD_VIS_DIR=/usr/share/nginx/ip-map/vis/
SELECTED_TOPOLOGY_DATA=data/country-aspath-selection.json

all: ${DATADIR}/bgp.alchemy.json

analytics: ${DATADIR}/expanded-ip-path.json

data/$(REL_DAY).as-rel.txt:
	wget -O - http://data.caida.org/datasets/as-relationships/serial-1/$(REL_DAY).as-rel.txt.bz2 | bzip2 -cd > $@_
	mv $@_ $@

data/known-networks.json: create-known-networks.py
	python2 create-known-networks.py

data/GeoIPASNum.dat:
	wget -O - http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz | gzip -cd > $@

${DATADIR}/probes.json: atlas-nz-probes.py
	! test -d ${DATADIR} || mkdir -p ${DATADIR}
	./atlas-nz-probes.py --datadir ${DATADIR}

${SCANDIR}/downloaded.txt: download-scan-data.py
	mkdir -p ${SCANDIR}
	./download-scan-data.py --datadir ${SCANDIR}
	touch $@


${DATADIR}/dest-addr.json: find-targets-from-scans.py ${SCANDIR}/downloaded.txt ${SELECTED_TOPOLOGY_DATA}
	python2 find-targets-from-scans.py --scandir ${SCANDIR} --datadir ${DATADIR} --topology-data ${SELECTED_TOPOLOGY_DATA}

${DATADIR}/measurements.json: ${DATADIR}/probes.json ${DATADIR}/dest-addr.json data/known-sites.txt
	./probe-to-probe-traceroute.py --datadir ${DATADIR} --sample 0.5

${DATADIR}/results.json: ${DATADIR}/measurements.json
	python2 fetch-results.py --datadir ${DATADIR}

${DATADIR}/bgp.json ${DATADIR}/ip.json ${DATADIR}/ip-path.json: ${DATADIR}/results.json\
        data/known-networks.json analyze-results.py data/GeoIPASNum.dat
	python2 analyze-results.py --datadir ${DATADIR} --sample 100

${DATADIR}/bgp.alchemy.json ${DATADIR}/vis-bgp-graph.js: prepare-for-alchemy.py ${DATADIR}/bgp.json
	python2 prepare-for-alchemy.py --datadir ${DATADIR} --relfile data/$(REL_DAY).as-rel.txt

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

deploy-vis-bgp: ${DATADIR}/vis-bgp-graph.js html/vis-bgp-test.html
	mkdir -p /var/www/visjs/misc/data
	rsync -a bower_components/vis/dist/vis.map bower_components/vis/dist/vis.min.js bower_components/vis/dist/vis.js /var/www/visjs/scripts/
	rsync -a bower_components/vis/dist/vis.css /var/www/visjs/styles/
	rsync -a ${DATADIR}/vis-bgp-graph.js /var/www/visjs/misc/data
	rsync -a html/vis-bgp-test.html /var/www/visjs

deploy-prod-vis-bgp: ${DATADIR}/vis-bgp-graph.js html/vis-bgp-test.html
	ssh bgp-map-ext "mkdir -p ${PROD_VIS_DIR}/misc/data ${PROD_VIS_DIR}/scripts ${PROD_VIS_DIR}/styles"
	rsync -a bower_components/vis/dist/vis.map bower_components/vis/dist/vis.min.js bower_components/vis/dist/vis.js bgp-map-ext:${PROD_VIS_DIR}/scripts
	rsync -a bower_components/vis/dist/vis.css bgp-map-ext:${PROD_VIS_DIR}/styles/
	rsync -a ${DATADIR}/vis-bgp-graph.js bgp-map-ext:${PROD_DIR}/misc/data/
	rsync -a html/vis-bgp-test.html bgp-map-ext:${PROD_VIS_DIR}/index.html

deploy-prod-poc: ${DATADIR}/ip-network-graph.js html/ip-test.html
	ssh bgp-map-ext "mkdir -p ${PROD_DIR}/misc/data ${PROD_DIR}/scripts ${PROD_DIR}/styles"
	rsync -a bower_components/vis/dist/vis.map bower_components/vis/dist/vis.min.js bower_components/vis/dist/vis.js bgp-map-ext:${PROD_DIR}/scripts/
	rsync -a bower_components/vis/dist/vis.css bgp-map-ext:${PROD_DIR}/styles/
	rsync -a ${DATADIR}/ip-network-graph.js bgp-map-ext:${PROD_DIR}/misc/data/
	rsync -a html/ip-test.html bgp-map-ext:${PROD_DIR}/poc/index.html
