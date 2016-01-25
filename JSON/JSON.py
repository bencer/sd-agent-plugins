"""
Server Density plugin
JSON - loads JSON files and forward them in the Server Density agent payload

https://github.com/bencer/sd-agent-plugins/

version: 0.1
"""

import os
import sys
import glob
import logging
import json
import time


class JSON:
    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config

    def run(self):
        if hasattr(self.raw_config['JSON'], 'path'):
            path = self.raw_config['JSON']['path']
        else:
            path = '/tmp/'

        data = {}
        path_pattern = os.path.join(path, '*.json')
        for f in glob.glob(path_pattern):
            try:
                with open(f, 'r') as json_file:
                    file_data = json_file.read()
                json_file.close()
            except Exception as exception:
                self.checks_logger.error(
                    'Failed to open JSON file: {0}'.format(
                    exception.message))
            try:
                json_part = json.loads(file_data)
                data = dict(data.items() + json_part.items())
            except Exception as exception:
                self.checks_logger.error(
                    'Failed to load JSON')

        return data


if __name__ == '__main__':
    """
    Standalone test configuration
    """
    raw_agent_config = {
        'JSON': {
            'host': '/tmp',
        }
    }

    main_checks_logger = logging.getLogger('JSON')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    json_check = JSON({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(json_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
