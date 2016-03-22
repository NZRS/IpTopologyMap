RIR_LIST=afrinic apnic lacnic
DELEGATION_FILES := $(foreach rir,${RIR_LIST},delegated-${rir}-latest)
ARIN_DELEGATION=delegated-arin-extended-latest
RIPE_DELEGATION=delegated-ripencc-latest

fetch: ${DELEGATION_FILES} ${ARIN_DELEGATION} ${RIPE_DELEGATION}

extract: fetch extract-country-data-from-delegation.py
	python2 extract-country-data-from-delegation.py --config ${CONFIG} --outfile ${OUTFILE}

clean:
	rm -rf ${DELEGATION_FILES} ${ARIN_DELEGATION} ${RIPE_DELEGATION}

${ARIN_DELEGATION}:
	wget -q -N http://ftp.apnic.net/stats/arin/$@

${RIPE_DELEGATION}:
	wget -q -N http://ftp.apnic.net/stats/ripe-ncc/$@

define RIR_delegation
delegated-${1}-latest:
	wget -q -N http://ftp.apnic.net/stats/${1}/delegated-${1}-latest
#	wget -q -N http://ftp.apnic.net/stats/${1}/delegated-${1}-latest.md5
#	md5sum -c delegated-${1}-latest.md5
endef

$(foreach rir,${RIR_LIST},$(eval $(call RIR_delegation,${rir})))
