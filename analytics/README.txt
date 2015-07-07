
analytics.py
	run like so: analytics.py --data data/final_test_1
	it will output all analytics into this folder

deviation-hop-destinations.json
	when a query is being routed overseas, what is the overseas ip address
	it is being routed to? This contains these.

deviation-hops.json
	for each query that gets routed overseas there is a query here which
	tells you the origin/goal of that query, where it came from, and the
	foreign address it was going to.

deviations-paths.json
	if a path goes overseas then it gets an entry in here.

potential-anomalies.json
	checks for ip addresses which may not be reliably geolocatable.
	the criterion for this is:
	    - if it's in the list of known_networks, it's reliable.
            - if the geolocation databases only give one answer for this
              ip address, it's reliable.
        otherwise it's unreliable and gets put in here.
