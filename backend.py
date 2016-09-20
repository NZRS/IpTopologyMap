import bottle
import json
from collections import defaultdict
import argparse
import os

bottle.app().catchall = False
bottle.debug(True)


# @bottle.hook('after_request')
# def enable_cors():
#     bottle.response.headers['Access-Control-Allow-Origin'] = '*'
#     bottle.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'


@bottle.route('/savepos', method=['POST', 'OPTIONS'])
def savepos():
    # Add this header to any response
    bottle.response.headers['Access-Control-Allow-Origin'] = '*'
    if bottle.request.method == 'OPTIONS':
        bottle.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return {'result': 'OK'}
    elif bottle.request.method == 'POST':
        # Count the list of items in the data
        if bottle.request.params is not None:
            data = defaultdict(dict)
            for p, v in bottle.request.params.items():
                # print("%s -> %s" % (p, v))
                node_id, coord = p.split('.')
                data[int(node_id)][coord] = int(v)

            with open(os.path.join(args.datadir, 'node-position.json'), 'wb') as f:
                json.dump(data, f)
            return {'result': 'OK'}
        else:
            return {'result': 'ERROR'}


parser = argparse.ArgumentParser("Receive calculated position from emulated "
                                 "browser")
parser.add_argument('--datadir', required=True,
                    help="directory to save output")
args = parser.parse_args()

bottle.run(host='localhost', port=8080)

