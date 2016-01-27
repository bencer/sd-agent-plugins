"""
Server Density plugin
openvpn

https://www.serverdensity.com/plugins/openvpn/
https://github.com/serverdensity/sd-agent-plugins/

version: 0.1
"""

import sys
import telnetlib
import re
import socket
import logging
import json
import time


class OpenVPN:
    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.datastore = {}

        self.host = self.raw_config['OpenVPN'].get('host', '127.0.0.1')
        self.port = self.raw_config['OpenVPN'].get('port', '7505')
        self.password = self.raw_config['OpenVPN'].get('password', '')

    def calculate_per_s(self, command, result):
        if (not self.datastore.get(command) and
                self.datastore.get(command) != 0):
            self.checks_logger.debug(
                '{0}: datastore unset for '
                '{1}, storing for first time'.format(type(self).__name__,
                                                     command))
            self.datastore[command] = result
            com_per_s = 0
        else:
            com_per_s = (result - self.datastore[command]) / 60
            if com_per_s < 0:
                com_per_s = 0
            self.datastore[command] = result
        return com_per_s

    def run(self):
        data = ''
        stats = {}

        try:
            telnet = telnetlib.Telnet()
            telnet.open(self.host, self.port)
            line = telnet.read_until("ENTER PASSWORD:", 2)
            if line != []:
                telnet.write(self.password + '\r\n')
                line = telnet.read_some()
                if line[:7] != "SUCCESS":
                    self.checks_logger.error(
                        'Failed to authenticate to OpenVPN')
                    return stats
                else:
                    telnet.read_very_eager()
                    telnet.write('load-stats\r\n')
                    telnet.write('exit\r\n')
                    data = telnet.read_all()
                telnet.close()
            else:
                self.checks_logger.error(
                    'Unexpected error connecting to OpenVPN')
                return stats
        except socket.error, reason:
            self.checks_logger.error(
                'Unexpected error connecting to OpenVPN: %s' % reason)
            return stats

        # Clients
        stats['clients'] = int(re.search("nclients=(\d+)", data).group(1))

        # Usage
        stats['bytes_in_total'] = int(re.search("bytesin=(\d+)", data).group(1))
        stats['bytes_in'] =  self.calculate_per_s('bytes_in', stats['bytes_in_total'])
        stats['bytes_out_total'] = int(re.search("bytesout=(\d+)", data).group(1))
        stats['bytes_out'] =  self.calculate_per_s('bytes_out', stats['bytes_out_total'])

        return stats


if __name__ == '__main__':
    """
    Standalone test configuration
    """
    raw_agent_config = {
        'OpenVPN': {
            'host': '127.0.0.1',
            'port': 7505,
            'password': '',
        }
    }

    main_checks_logger = logging.getLogger('OpenVPN')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    host_check = OpenVPN({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(host_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
