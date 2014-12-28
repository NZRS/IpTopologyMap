#!/bin/bash

DIR=/var/www/ip-topology
rsync -av cyto-test.html cola-test.html $DIR
rsync -av data/test_006/graph.json $DIR/data
