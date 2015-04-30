#
# PHPFPM ServerDensity Plugin
# V1.1
#
# (c) Tom Arnfeld [tarnfeld@me.com][tarnfeld.com]
# (c) Jorge Salamero Sanz <bencer@gmail.com>
#

import sys
import urllib
import json
import simplejson
import logging
import platform
import time

class PHPFPM(object):

    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.version = platform.python_version_tuple()
        self.status_url = "http://localhost/status?json"

        if 'fpm_status_url' in raw_config['PHPFPM']:
            self.status_url = raw_config['PHPFPM']['fpm_status_url'] + "?json"

        self.checks_logger.debug('Setup FPM URL: ' + self.status_url)

    def run(self):
        try:
            status = urllib.urlopen(self.status_url).read()
            status_json = simplejson.loads(status)
            self.checks_logger.debug('Parsed JSON: ' + str(status_json))
        except Exception as e:
            self.checks_logger.info('Failed to get FPM status ' + e.__str__())
            return False

        return status_json

if __name__ == '__main__':
    """Standalone test"""
    raw_agent_config = {
        'PHPFPM': {
        }
    }

    main_checks_logger = logging.getLogger('PHPFPM')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    phpfpm_check = PHPFPM({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(phpfpm_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
