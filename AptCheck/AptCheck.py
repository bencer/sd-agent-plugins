#
# AptCheck Server Density plugin
# checks for security and standard updates on Ubuntu
# requires update-notifier-common package
#
# (c) Jorge Salamero Sanz <bencer@gmail.com>
#

import subprocess
import sys
import json
import logging
import time


class AptCheck(object):

    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.cmd_path = '/usr/lib/update-notifier/apt_check.py'

    def run(self):
        security = total = -1
        try:
            data = subprocess.check_output([self.cmd_path, ],
                                           stderr=subprocess.STDOUT)
            (security, total) = data.split(';')
        except Exception as e:
            self.checks_logger.error('Failed to run script %s: %s' %
                                     (self.cmd_path, e))

        return_data = {'security_updates': security, 'total_updates': total}
        return return_data

if __name__ == '__main__':

    main_checks_logger = logging.getLogger('AptCheck')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))

    check = AptCheck({}, main_checks_logger, {})

    while True:
        try:
            print json.dumps(check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
