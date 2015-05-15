#
# Samba4 DB check ServerDensity Plugin
# V0.1
# add to /etc/sudoers.d/sd-agent
# # allow sd-agent user samba_db_check command
# sd-agent ALL=(ALL) NOPASSWD: /usr/local/share/sd-plugins/samba_db_check.py
#
# (c) Jorge Salamero Sanz <bencer@gmail.com>
#

import subprocess

class SambaDBcheck:
    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.dbcheck_path = '/usr/local/share/sd-plugins/samba_db_check.py'

    def run(self):
        if self.raw_config.has_key('plugin_sambadbcheck_path'):
	    self.dbcheck_path = self.raw_config['plugin_sambadbcheck_path'] 

        try:
	    command_output = subprocess.check_output(['/usr/bin/sudo', self.dbcheck_path]).strip()
        except Exception as e:
            command_output = '-1'
            self.checks_logger.info('Failed to run script %s: %s' % (self.dbcheck_path, e))

	return_data = {'SambaDBcheck': command_output}
        return return_data
