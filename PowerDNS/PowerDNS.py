# PowerDNS ServerDensity Plugin
# 
# add to /etc/sudoers.d/sd-agent
# # allow sd-agent user /etc/init.d/pdns-server command
# sd-agent ALL=(ALL) NOPASSWD: /etc/init.d/pdns-server
#
# and also disable this on /etc/sudoers
# #Defaults    requiretty
#
# (c) Jorge Salamero Sanz <bencer@gmail.com>
#

from subprocess import PIPE,Popen
import sys
import time
import json
import logging

class PowerDNS:
    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.pdns_path = self.raw_config['PowerDNS'].get('pdns_path', '/etc/init.d/pdns-server')

        self.counter_metrics = ['udp-queries', 'udp-answers',
                               'packetcache-hit', 'packetcache-miss',
                               'recursing-questions', 'recursing-answers']

        self.previous_run = {}
        for metric in self.counter_metrics:
            self.previous_run[metric] = 0

        self.gauge_metrics = ['latency']

    def query(self, metric):
        try:
            proc = Popen(['/usr/bin/sudo', self.pdns_path, 'mrtg', metric], stdout=PIPE)
            output = proc.communicate()[0].strip('\n')
            if metric in self.counter_metrics:
                self.previous_run[metric] = int(output[0]) - self.previous_run[metric]
                return self.previous_run[metric]
            else:
                return int(output[0])
            
        except Exception as e:
            command_output = '-1'
            self.checks_logger.info('Failed to run script %s: %s' % (self.pdns_path, e))

    def run(self):
        data = {}

        for metric in self.counter_metrics:
            data[metric] = self.query(metric)

        for metric in self.gauge_metrics:
            data[metric] = self.query(metric)

        return data

if __name__ == '__main__':
    """Standalone test"""
    raw_agent_config = {
        'PowerDNS': {
        }
    }

    main_checks_logger = logging.getLogger('PowerDNS')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    pdns_check = PowerDNS({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(pdns_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
