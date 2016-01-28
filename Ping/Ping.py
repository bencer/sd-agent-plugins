#
# Ping Server Density Plugin
# pings a list of IPv4 hosts or IP addresses
# inspired in
#  http://blog.boa.nu/2012/10/python-threading-example-creating-pingerpy.html
#
# (c) Jorge Salamero Sanz <bencer@gmail.com>
#

import subprocess
import threading
import re
import sys
import json
import logging
import platform
import time


class Pinger(object):

    hosts = []  # List of all hosts/ips in our input queue
    stats = {}  # Populated while we are running

    # How many ping process at the time.
    thread_count = 4

    # Lock object to keep track the threads in loops, where it can potentially
    # be race conditions.
    lock = threading.Lock()

    def __init__(self, checks_logger):
        self.checks_logger = checks_logger

    def ping(self, ip):
        try:
            # Use the system ping command with count of 5.
            ping = subprocess.Popen(['ping', '-c', '5', ip],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

            out, error = ping.communicate()

            if ping.returncode == 0:
                matcher = re.search("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)", out)
                result = matcher.groups()
            else:
                result = ['-1', '-1', '-1']

            matcher = re.search("(\d+) packets transmitted, (\d+) received, (\d+)% packet loss, time (\d+)ms", out)
            if matcher is not None:
                lossResult = matcher.groups()
            else:
                lossResult = [5, 0, 100, 0]

            data = {'min': result[0], 'avg': result[1], 'max': result[2],
                    'loss': lossResult[2]}
            return data
        except Exception, e:
            import traceback
            self.checks_logger.error('Ping plugin - Exception = %s',
                                     traceback.format_exc())
            data = {'min': '-2', 'avg': '-2', 'max': '-2', 'loss': '-2'}
            return data

    def pop_queue(self):
        ip = None

        self.lock.acquire()  # Grab or wait+grab the lock

        if self.hosts:
            ip = self.hosts.pop()

        self.lock.release()  # Release the lock

        return ip

    def dequeue(self):
        while True:
            ip = self.pop_queue()

            if not ip:
                return None

            result = self.ping(ip)
            self.stats[ip+'_min'] = result['min']
            self.stats[ip+'_avg'] = result['avg']
            self.stats[ip+'_max'] = result['max']
            self.stats[ip+'_loss'] = result['loss']

    def start(self):
        threads = []

        for i in range(self.thread_count):
            # Create self.thread_count number of threads that together will
            # cooperate removing every ip in the list. Each thread will do the
            # job as fast as it can.
            t = threading.Thread(target=self.dequeue)
            t.start()
            threads.append(t)

        # Wait until all the threads are done. .join() is blocking.
        [t.join() for t in threads]

        return self.stats


class Ping(object):

    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.version = platform.python_version_tuple()

        config_ipv4_hosts = self.raw_config['Ping'].get('ipv4_hosts', '')
        self.ipv4_hosts = config_ipv4_hosts.split(',')

    def run(self):
        ping = Pinger(self.checks_logger)
        ping.hosts = self.ipv4_hosts
        return ping.start()

if __name__ == '__main__':

    main_checks_logger = logging.getLogger('Ping')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))

    raw_agent_config = {
        'Ping': {
            'ipv4_hosts': 'google.com,microsoft.com,8.8.8.8,8.8.4.4,nonexistent'
        }
    }

    ping = Ping({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(ping.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
