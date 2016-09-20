import subprocess
import threading
import SimpleHTTPServer
import SocketServer
import bottle
import json
from collections import defaultdict
import os
import jinja2
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

""" run-physics-simulation.py
    Two child processes are run, one to implemente a simple HTTP Server to
    serve files, and one REST API backend to capture the state calculated by
    the physics simulation.

    To run the simulation, which calculates a stable layout for the network,
    it uses PhantomJS to emulate a browser and let the JavaScript framework
    to run.
"""

parser = argparse.ArgumentParser("Prepare graph layout for visualization")
parser.add_argument('--datadir', required=True,
                    help="directory to read input and save output")
args = parser.parse_args()


# Load the page template with the generic code for simulation and generate an
#  specific version for the map we are generating

templateLoader = jinja2.FileSystemLoader(searchpath="templates/")
templateEnv = jinja2.Environment(loader=templateLoader)
physics_page = "physics.html"
with open(physics_page, 'wb') as f:
    f.write(templateEnv.get_template("physics.phtml").render(
        map_data_file=os.path.join(args.datadir, 'vis-bgp-graph.json')))

http_port = '8001'
w = subprocess.Popen(['/usr/bin/env', 'python2', '-m', 'SimpleHTTPServer',
                      http_port])
r = subprocess.Popen(['/usr/bin/env', 'python2', 'backend.py',
                      '--datadir', args.datadir])

driver = webdriver.PhantomJS()  # or add to your PATH
driver.set_window_size(1024, 768)  # optional

# Load the page with the script to run the simulation

driver.get('http://localhost:%s/%s' % (http_port, physics_page))

# TODO: Wait for an event to happen
try:
    stabilized = WebDriverWait(driver, 600).until(
        EC.presence_of_element_located((By.ID, 'stabilized'))
    )
    # print(stabilized.text)
finally:
    driver.save_screenshot('simulation.png')  # save a screenshot to disk
    driver.quit()
    print("Finished with browser")
    # w.exit()
    # r.exit()
    w.terminate()
    r.terminate()
