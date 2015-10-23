#
# AM2302 sensor Server Density plugin
# V0.1
# add to /etc/sudoers.d/sd-agent
# # allow sd-agent user am2302 command
# sd-agent ALL=(ALL) NOPASSWD: /usr/local/share/sd-plugins/am2302.py
#
# and also disable this on /etc/sudoers
# #Defaults    requiretty
#
# (c) Jorge Salamero Sanz <bencer@gmail.com>
#

import subprocess

class AM2302sensor:
    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.amcmd_path = '/usr/local/share/sd-plugins/am2302.py'

    def run(self):
        try:
	    temperature = subprocess.check_output(['/usr/bin/sudo', self.amcmd_path, '-t']).strip()
        except Exception as e:
            temperature = '-1'
            self.checks_logger.info('Failed to run script %s: %s' % (self.amcmd_path, e))

        try:
	    humidity = subprocess.check_output(['/usr/bin/sudo', self.amcmd_path, '-h']).strip()
        except Exception as e:
            humidity = '-1'
            self.checks_logger.info('Failed to run script %s: %s' % (self.amcmd_path, e))

	return_data = {'temperature': temperature, 'humidity': humidity}
        return return_data
