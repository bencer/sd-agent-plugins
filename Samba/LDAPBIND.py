#
# LDAP bind ServerDensity Plugin
# V0.1
#
# (c) Jorge Salamero Sanz <bencer@gmail.com>
#

import sys
import logging
import platform
import json
import ldap
import socket
import time

class LDAPBIND(object):

    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.version = platform.python_version_tuple()
        self.user_dn = "CN=Administrator,CN=Users,DC=demo,DC=zentyal,DC=lan"
        self.user_passwd = ""
        self.hostname = socket.getfqdn()

        if 'user_dn' in raw_config['LDAPBIND']:
            self.user_dn = raw_config['LDAPBIND']['user_dn']

        if 'user_passwd' in raw_config['LDAPBIND']:
            self.user_passwd = raw_config['LDAPBIND']['user_passwd']

        if 'hostname' in raw_config['LDAPBIND']:
            self.hostname = raw_config['LDAPBIND']['hostname']

    def run(self):
        adconn = ldap.initialize("ldap://%s" % self.hostname, trace_level=0)
        adconn.protocol_version = 3
        adconn.set_option(ldap.OPT_REFERRALS,0)
        try:
            start = time.time()
            adconn.bind_s(self.user_dn, self.user_passwd)
            adconn.unbind_s()
            end = time.time()
            t = end - start
            data = {'ldap_bind_time': t }
        except Exception as e:
            self.checks_logger.info('Failed to bind to LDAP' + e.__str__())
            return False

        return data

if __name__ == '__main__':
    """Standalone test"""
    raw_agent_config = {
        'LDAPBIND': {
        }
    }

    main_checks_logger = logging.getLogger('LDAPBIND')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    ldap_bind = LDAPBIND({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(ldap_bind.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
