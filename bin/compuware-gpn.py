import sys
import logging
import xml.sax.saxutils
import xml.dom.minidom
import re
import time
import json
import os

from time import sleep, mktime, strptime
from Queue import Queue
from threading import Thread,  Lock
from gpn import export
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
lock = Lock()

SCHEME = '''<scheme>
    <title>Compuware GPN</title>
    <description>Collect and index  Compuware GPN API data.</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>simple</streaming_mode>
    <use_single_instance>false</use_single_instance>
    <endpoint>
        <args>
            <arg name="name">
                <title>Name</title>
                <description>Choose an ID or nickname for this configuration</description>
            </arg>

            <arg name="username">
                <title>Username</title>
                <description>GPN user account</description>
                <required_on_create>true</required_on_create>
            </arg>
            <arg name="password">
                <title>Password</title>
                <description>Password for GPN user account</description>
                <required_on_create>true</required_on_create>
            </arg>
            <arg name="monitor_id">
                <title>Montior ID</title>
                <description>Monitor ID as Defined in GPN.</description>
                <required_on_create>true</required_on_create>
            </arg>
            <arg name="monitor_class">
                <title>Monitor Class</title>
                <description>Monitor Class to collect.  Defaults to UTATX</description>
                <required_on_create>false</required_on_create>
            </arg>
        </args>
    </endpoint>
</scheme>
'''


class Worker(Thread):
    """
    Thread executing tasks from a given tasks queue
    """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception, e:
                print e
            self.tasks.task_done()


class ThreadPool:
    """
    Pool of threads consuming tasks from a queue
    """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()


def do_scheme():
    print SCHEME


# prints XML error data to be consumed by Splunk
def print_error(s):
    print '<error><message>%s</message></error>' % xml.sax.saxutils.escape(s)


def validate_conf(config, key):
    if key not in config:
        raise NameError('Invalid configuration received from Splunk: key \'%s\' is missing.' % key)


# read XML configuration passed from splunkd
def get_config():
    """
    Reads .conf file for modular input
    """
    config = {}

    try:
        # read everything from stdin
        config_str = sys.stdin.read()
        # parse the config XML
        doc = xml.dom.minidom.parseString(config_str)
        root = doc.documentElement
        conf_node = root.getElementsByTagName('configuration')[0]
        if conf_node:
            logging.debug('XML: found configuration')
            stanza = conf_node.getElementsByTagName('stanza')[0]
            if stanza:
                stanza_name = stanza.getAttribute('name')
                if stanza_name:
                    logging.debug('XML: found stanza %s', stanza_name)
                    config['name'] = stanza_name
                    params = stanza.getElementsByTagName('param')
                    for param in params:
                        param_name = param.getAttribute('name')
                        logging.debug('XML: found param %s', param_name)
                        if param_name and param.firstChild and \
                           param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                            data = param.firstChild.data
                            config[param_name] = data
                            logging.debug('XML: %s -> %s', param_name,data)

        if not config:
            raise NameError('Invalid configuration received from Splunk.')

        # just some validation: make sure these keys are present (required)
        validate_conf(config, 'username')
        validate_conf(config, 'password')
        validate_conf(config, 'monitor_id')
        validate_conf(config, 'interval')

    except Exception, e:
        e = sys.exc_info()[1]
        raise Exception, 'Error getting Splunk configuration via STDIN: %s' % str(e)

    return config


def validate_arguments():
    # we can check keys etc here, but for now:
    pass


def interval_time(polltime):
    """
    Creates start and end time from interval
    """
    polltime = int(polltime)
    current_time = (int(time.mktime(time.localtime()))-60)
    end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(current_time))
    start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(current_time-polltime))

    return {'end_time': end_time,
            'start_time': start_time
            }


def make_list(item):
    """
    Turns single returned results into list
    """
    if not isinstance(item, list):
        items = []
        items.append(item)
    else:
        items = item
    return items


def make_json(attributes):
    """
    Converts dictionary object to json with formatting
    """
    return json.dumps(json.loads(json.JSONEncoder().encode(attributes)), indent=4, sort_keys=True, ensure_ascii=True)


def make_event(data):
    '''
    Breaks transaction from GPN xmldocument into json events
    taking attributes from the parnet to build links
    '''
    root_attributes, children = parse_elem(data)
    root_link = {k: root_attributes[k] for k in ('ttime', 'sid', 'mid')}
    root_link['epoch'] = int(mktime(strptime(root_link.pop('ttime').split('.')[0], '%Y-%m-%d %H:%M:%S')))
    root_attributes['type'] = 'txtest'
    root_attributes = dict(root_attributes.items() + root_link.items())
    logging.info('%s', root_attributes)
    print_discrete_event(make_json(root_attributes))
    for child_name, child_elements in children.iteritems():
        child_elements = make_list(child_elements)
        for element in child_elements:
            child_attributes, subchildren = parse_elem(element)
            child_link = {k: child_attributes[k] for k in ('hid', 'pseq') if k in child_attributes}
            child_attributes['type'] = child_name.lower()
            child_attributes = dict(child_attributes.items() + root_link.items())
            print_discrete_event(make_json(child_attributes))
            for subchild_name, subchild_elements in subchildren.iteritems():
                subchild_elements = make_list(subchild_elements)
                for element in subchild_elements:
                    subchild_attributes, _ = parse_elem(element)
                    subchild_attributes['type'] = subchild_name.lower()
                    subchild_attributes = dict(subchild_attributes.items() + root_link.items() + child_link.items())
                    print_discrete_event(make_json(subchild_attributes))


def parse_elem(root):
    """
    converts suds object to dictionary.
    Returns Tuple: (dict(attributes), dict(instances))
    """
    children = {}
    attributes = {k.replace('_', ''): v for k, v in root}
    for k in attributes.keys():
        if not isinstance(attributes[k], Text):
            children[k] = attributes.pop(k)
    return attributes, children


def print_discrete_event(data):
    """
    Print events to be consumed by Splunk process
    """
    with lock:
        logging.debug('%s', data)
        print data
        sys.stdout.flush()


def run():

    config = get_config()
    input_name = config['name']
    monitor_id = config['monitor_id']
    username = config['username']
    password = config['password']
    interval = config['interval']
    pool = ThreadPool(20)

    if ',' in monitor_id:
        logging.info('Mutiple monitor ids found.')
        mids = monitor_id.split(',')
        logging.debug('monitor_ids %s', mids)
        monitor_id = []
        for mid in mids:
            monitor_id.append({'int': mid})

    if not 'monitor_class' in config:
        monitor_class = 'UTATX'
    else:
        monitor_class = config['monitor_class']

    time_range = interval_time(interval)
    logging.info('Retrieving data for %s, From: %s To:%s', monitor_id, time_range['start_time'], time_range['end_time'])
    gpn_data = export(username, password)

    logging.debug('CompuWare API Prams OpenDataFeed2: monitorIds=%s' +
                  'monitorClassDesignator=%s dstartTime=%s endTime=%s',
                  monitor_id, monitor_class,
                  time_range['start_time'],
                  time_range['end_time'])
    try:
        gpn_data.OpenDataFeed2(monitorIds={'int': monitor_id},
                               siteIds=None,
                               monitorClassDesignator=monitor_class,
                               dataDesignator='ALL',
                               startTime=time_range['start_time'],
                               endTime=time_range['end_time'])
    except Exception as e:
        logging.error('Error: %s', e)

    logging.info('Gomez Session Token: %s', gpn_data.sessiontoken)
    logging.info('parsing data')
    xmldoc = gpn_data.getResponseData()
    logging.info('Data recieved')
    gpn_data.closeDataFeed()

    if xmldoc.Status.eStatus != 'STATUS_SUCCESS':
        logging.error('%s', xmldoc.Status.sErrorMessage)
        exit()
    elif 'MESSAGE' in xmldoc.XmlDocument.GpnResponseData.__dict__:
        logging.warn('%s', xmldoc.XmlDocument.GpnResponseData.MESSAGE._Msg)
        exit()

    logging.info('Number of Records %s returned', xmldoc.NumRecords)
    xmldoc = make_list(xmldoc.XmlDocument.GpnResponseData.TXTEST)

    for root in xmldoc:
        pool.add_task(make_event, root)
    pool.wait_completion()
    logging.info('Data complete for %s', input_name)


def usage():
    print 'usage: %s [--scheme|--validate-arguments]'
    sys.exit(2)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--scheme':
            do_scheme()
        elif sys.argv[1] == '--validate-arguments':
            validate_arguments()
        #else:
        #    usage()
    else:
        # just do it
        run()

    sys.exit(0)