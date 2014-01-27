import sys
import logging
import xml.sax.saxutils
import xml.dom.minidom
import re
import time
import json
import os
import argparse

from time import sleep, mktime, strptime
from Queue import Queue
from gpn import account
#from memory_profiler import profile

SPLUNK_HOME = os.environ.get('SPLUNK_HOME')

try:
    from suds.sax.text import Text
except Exception:
    egg_dir = SPLUNK_HOME + '/etc/apps/compuware_apm_gpn/bin/'
    for filename in os.listdir(egg_dir):
        if filename.endswith('.egg'):
            sys.path.append(egg_dir + filename)
    from suds.sax.text import Text

logging.root
logging.root.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.root.addHandler(handler)


def options():
    """Display for command line options"""
    parser = argparse.ArgumentParser(description='Fetches witter feeds')
    parser.add_argument('--user',
                        required=True,
                        help='Gomez User')
    parser.add_argument('--pw',
                        required=True,
                        help='Gomez Network password')
    return parser.parse_args()


def parse_elem(root):
    '''
        converts suds object to dictionary.
        Returns Tuple: (dict(attributes), dict(instances))
        '''
    children = {}
    attributes = {k.replace('_', ''): v for k, v in root}
    for k in attributes.keys():
        if not isinstance(attributes[k], Text):
            children[k] = attributes.pop(k)
    return attributes, children


def make_list(item):
    '''
        Turns single returned results into list
        '''
    if not isinstance(item, list):
        items = []
        items.append(item)
    else:
        items = item
    return items


def run(user, password):
    gpn_account = account(user,password)

    try:
        gpn_account = gpn_account.getAccountMonitors()
        if gpn_account.Status.eStatus != 'STATUS_SUCCESS':
            logging.info('%s', gpn_account.Status.sErrorMessage)
            exit(2)
    except Exception as e:
        logging.error('Error: %s', e)

    gpn_account = make_list(gpn_account.MonitorSet.Monitor)
    for monitor in gpn_account:
        monitor, _ = parse_elem(monitor)
        if monitor['status'] == 'ACTIVE' and monitor['cls'] == 'TRANSACTION':
            print 'Name: %s\n\tMonitorID: %s\n\tfrequency_milsec: %s\n\tmodified: %s\n\tcreated: %s\n' % (monitor['desc'],
                                                                            monitor['mid'],
                                                                            monitor['frequencyinms'],
                                                                            monitor['modified'],
                                                                            monitor['created'])


if __name__ == '__main__':

    args = options()
    run(args.user,arg.pw)