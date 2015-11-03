"""
Server Density plugin
memcached

https://www.serverdensity.com/plugins/memcached/
https://github.com/serverdensity/sd-agent-plugins/

version: 0.2
forked from https://github.com/deplorableword/sd-memcached

for full protocol description see:
https://github.com/memcached/memcached/blob/master/doc/protocol.txt
"""

import sys
import telnetlib
import re
import socket
import logging
import json
import time


class Memcached:
    def __init__(self, agentConfig, checksLogger, rawConfig):
        self.agentConfig = agentConfig
        self.checksLogger = checksLogger
        self.rawConfig = rawConfig
        self.datastore = {}

    def calculate_per_s(self, command, result):
        if (not self.datastore.get(command) and
                self.datastore.get(command) != 0):
            self.checksLogger.debug(
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
        stats = {}

        if hasattr(self.rawConfig['Memcached'], 'host'):
            host = self.rawConfig['Memcached']['host']
        else:
            host = '127.0.0.1'

        if hasattr(self.rawConfig['Memcached'], 'port'):
            port = self.rawConfig['Memcached']['port']
        else:
            port = 11211

        try:
            telnet = telnetlib.Telnet()
            telnet.open(host, port)

            telnet.write('stats\r\n')
            out1 = telnet.read_until("END")

            telnet.write('stats settings\r\n')
            out2 = telnet.read_until("END")

            telnet.write('quit\r\n')
            telnet.close()
        except socket.error, reason:
            sys.stderr.write("%s\n" % reason)
            sys.stderr.write("Is memcached running?\n")
            sys.stderr.write("Host: %s Port: %s\n" % (host, port))
            return stats

        # Uptime
        stats['uptime'] = int(re.search("uptime (\d+)", out1).group(1))

        # Current / Total
        stats['curr_items'] = int(re.search("curr_items (\d+)", out1).group(1))
        stats['total_items'] = int(re.search("total_items (\d+)", out1).group(1))

        # Memory Usgae
        stats['limit_maxbytes'] = int(re.search("limit_maxbytes (\d+)", out1).group(1))
        stats['bytes'] = int(re.search("bytes (\d+)", out1).group(1))
        maxbytes = int(re.search("maxbytes (\d+)", out2).group(1))
        stats['memory_usage_%'] = (100.0 * stats['bytes'] / maxbytes)

        # Network Traffic
        stats['bytes_read'] = int(re.search("bytes_read (\d+)", out1).group(1))
        stats['bytes_read_ps'] =  self.calculate_per_s('bytes_read_ps', stats['bytes_read'])
        stats['bytes_written'] = int(re.search("bytes_written (\d+)", out1).group(1))
        stats['bytes_written_ps'] =  self.calculate_per_s('bytes_written_ps', stats['bytes_written'])

        # Connections
        stats['curr_connections'] = int(re.search("curr_connections (\d+)", out1).group(1))
        maxconns = int(re.search("maxconns (\d+)", out2).group(1))
        stats['connections_usage_%'] = (100.0 * stats['curr_connections'] / maxconns)
        stats['total_connections'] = int(re.search("total_connections (\d+)", out1).group(1))
        stats['connections_ps'] =  self.calculate_per_s('connections_ps', stats['total_connections'])
        stats['connection_structures'] = int(re.search("connection_structures (\d+)", out1).group(1))
        stats['conn_yields'] = int(re.search("conn_yields (\d+)", out1).group(1))
        stats['conn_yields_ps'] =  self.calculate_per_s('conn_yields_ps', stats['conn_yields'])

        # Hits / Misses
        stats['cmd_get'] = int(re.search("cmd_get (\d+)", out1).group(1))
        stats['cmd_get_ps'] =  self.calculate_per_s('cmd_get_ps', stats['cmd_get'])
        stats['cmd_set'] = int(re.search("cmd_set (\d+)", out1).group(1))
        stats['cmd_set_ps'] =  self.calculate_per_s('cmd_set_ps', stats['cmd_set'])
        stats['get_hits'] = int(re.search("get_hits (\d+)", out1).group(1))
        stats['get_hits_ps'] =  self.calculate_per_s('get_hits_ps', stats['get_hits'])
        stats['hits_percent_%'] = (100.0 * stats['get_hits'] / stats['cmd_get'])
        stats['get_misses'] = int(re.search("get_misses (\d+)", out1).group(1))
        stats['get_misses_ps'] =  self.calculate_per_s('get_misses_ps', stats['get_misses'])
        stats['delete_hits'] = int(re.search("delete_hits (\d+)", out1).group(1))
        stats['delete_misses'] = int(re.search("delete_misses (\d+)", out1).group(1))
        stats['incr_hits'] = int(re.search("incr_hits (\d+)", out1).group(1))
        stats['decr_hits'] = int(re.search("decr_hits (\d+)", out1).group(1))
        stats['incr_misses'] = int(re.search("incr_misses (\d+)", out1).group(1))
        stats['decr_misses'] = int(re.search("decr_misses (\d+)", out1).group(1))

        # Evictions
        stats['evictions'] = int(re.search("evictions (\d+)", out1).group(1))
        stats['evictions_ps'] =  self.calculate_per_s('evictions_ps', stats['evictions'])
        stats['reclaimed'] = int(re.search("reclaimed (\d+)", out1).group(1))

        return stats


if __name__ == '__main__':
    """
    Standalone test configuration
    """
    raw_agent_config = {
        'Memcached': {
            'host': '127.0.0.1',
            'port': 11211,
        }
    }

    main_checks_logger = logging.getLogger('Memcached')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    host_check = Memcached({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(host_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
