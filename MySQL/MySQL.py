"""
Server Density plugin
MySQL

https://www.serverdensity.com/plugins/mysql/
https://github.com/serverdensity/sd-agent-plugins/

version: 0.1
"""
import traceback
import re

try:
    import MySQLdb
except ImportError:
    pass

# com commands.
COMMANDS = [
    'Com_select',
    'Com_delete',
    'Com_update',
    'Com_commit',
    'Questions',
    'Com_rollback',
    'Handler_commit',
    'Handler_delete',
    'Handler_update',
    'Handler_write',
    'Handler_rollback',
    'Handler_read_first',
    'Handler_read_rnd',
]


class MySQL(object):

    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.connection = None
        self.datastore = {}

    def version_is_above_5(self, status):
        if (int(status['version'][0]) >= 5 and
                int(status['version'][2]) >= 2):
            return True
        else:
            return False

    def get_db_results(self, db, query):
        cursor = db.cursor()
        try:
            cursor.execute(query)
            results = float(cursor.fetchone()[1])
        except ValueError:
            cursor.execute(query)
            results = cursor.fetchone()[1]
        return results

    def run_query(self, db, query):
        """Run a query and returns a dictionary with results"""
        try:
            cursor = db.cursor()
            cursor.execute(query)
            metric = {}
            for entry in cursor:
                try:
                    metric[entry[0]] = float(entry[1])
                except ValueError as e:
                    metric[entry[0]] = entry[1]

            return metric
        except MySQLdb.OperationalError as message:
            self.checks_logger.debug(
                'mysql: MySQL query error when getting metrics = '.format(
                    message)
                )

    def calculate_per_s(self, command, result):
        if (not self.datastore.get(command) and
                self.datastore.get(command) != 0):
            self.checks_logger.debug(
                'mysql: Datastore unset for '
                '{0}, storing for first time'.format(command))
            self.datastore[command] = result
            com_per_s = 0
        else:
            com_per_s = (result - self.datastore[command]) / 60
            if com_per_s < 0:
                com_per_s = 0
            self.datastore[command] = result
        return com_per_s

    def preliminaries(self):
        if ('MySQLServer' not in self.raw_config and
                'mysql_server' not in self.raw_config['MySQLServer'] or
                self.raw_config['MySQLServer']['mysql_server'] == '' or
                self.raw_config['MySQLServer']['mysql_user'] == '' or
                self.raw_config['MySQLServer']['mysql_pass'] == ''):
            self.checks_logger.debug('mysql: config not set')
            return False

        if not self.raw_config['MySQLServer'].get('mysql_port'):
            self.raw_config['MySQLServer']['mysql_port'] = "3306"

        self.checks_logger.debug('mysql: config set')

        try:
            import MySQLdb
        except ImportError:
            self.checks_logger.error('mysql: unable to import MySQLdb')
            return False

        # Note, code here doesn't really make sense. See what I copied.
        if self.raw_config['MySQLServer'].get('mysql_server'):
            # Connect
            try:
                MySQLdb.connect(
                    host=self.raw_config['MySQLServer']['mysql_server'],
                    user=self.raw_config['MySQLServer']['mysql_user'],
                    passwd=self.raw_config['MySQLServer']['mysql_pass'],
                    port=int(self.raw_config['MySQLServer']['mysql_port'])
                    )
            except MySQLdb.OperationalError as message:
                self.checks_logger.error(
                    "mysql: MySQL connection error: {0}".format(message))
                return False
        elif (self.raw_config['MySQLServer'].get('mysql_ssl_cert') and
                self.raw_config['MySQLServer'].get('mysql_ssl_key')):
            ssl = {
                'cert': self.raw_config['MySQLServer']['mysql_ssl_cert'],
                'key': self.raw_config['MySQLServer']['mysql_ssl_key']
            }
            MySQLdb.connect(
                host=self.raw_config['MySQLServer']['mysql_server'],
                user=self.raw_config['MySQLServer']['mysql_user'],
                passwd=self.raw_config['MySQLServer']['mysql_pass'],
                port=int(self.raw_config['MySQLServer']['mysql_port']),
                ssl=ssl
            )
        else:
            # Connect
            try:
                MySQLdb.connect(
                    host='localhost',
                    user=self.raw_config['MySQLServer']['mysql_user'],
                    passwd=self.raw_config['MySQLServer']['mysql_pass'],
                    port=int(self.raw_config['MySQLServer']['mysql_port']))
            except MySQLdb.OperationalError as message:
                self.checks_logger.error(
                    'mysql: MySQL connection error: {0}'.format(message)
                    )
                return False
        return True

    def get_connection(self):
        try:
            # connection
            if (self.raw_config['MySQLServer'].get('mysql_ssl_cert') and
                    self.raw_config['MySQLServer'].get('mysql_ssl_key')):
                self.checks_logger.debug('mysql: Trying to connect via SSL')
                ssl = {
                    'cert': self.raw_config['MySQLServer']['mysql_ssl_cert'],
                    'key': self.raw_config['MySQLServer']['mysql_ssl_key']
                }
                db = MySQLdb.connect(
                    host=self.raw_config['MySQLServer']['mysql_server'],
                    user=self.raw_config['MySQLServer']['mysql_user'],
                    passwd=self.raw_config['MySQLServer']['mysql_pass'],
                    port=int(self.raw_config['MySQLServer']['mysql_port']),
                    ssl=ssl
                )
                self.connection = db
                self.checks_logger.error('mysql: Connected to DB via SSL')
            else:
                self.checks_logger.debug(
                    'mysql: Trying to connect via password')
                db = MySQLdb.connect(
                    host=self.raw_config['MySQLServer']['mysql_server'],
                    user=self.raw_config['MySQLServer']['mysql_user'],
                    passwd=self.raw_config['MySQLServer']['mysql_pass'],
                    port=int(self.raw_config['MySQLServer']['mysql_port'])
                    )
                self.connection = db
                self.checks_logger.debug(
                    'mysql: Connected to DB with password')
            # note, how do I take into account the socket?
        except Exception:
            self.checks_logger.error(
                'Unable to connect to MySQL server {0}'
                ' - Exception: {1}'.format(
                    self.raw_config['MySQLServer']['mysql_server'],
                    traceback.format_exc())
                )
            return False
        return True

    def run(self):
        self.checks_logger.debug('mysql: started gathering data')
        if not self.preliminaries():
            return False

        if not self.get_connection():
            return False

        try:
            db = self.connection

            # setup
            status = {}

            # Get MySQL version
            try:
                self.checks_logger.debug('mysql: getting mysqlversion')

                cursor = db.cursor()
                cursor.execute('SELECT VERSION()')
                result = cursor.fetchone()

                version = result[0].split('-')
                # Case 31237. Might include a description e.g. 4.1.26-log.
                # See http://dev.mysql.com/doc/refman/4.1/en/
                # information-functions.html#function_version
                version = version[0].split('.')

                status['version'] = []

                for version_item in version:
                    number = re.match('([0-9]+)', version_item)
                    number = number.group(0)
                    status['version'].append(number)

            except MySQLdb.OperationalError as message:
                self.checks_logger.error(
                    (
                        'mysql: MySQL query error when getting version: '
                        '{0}'
                    ).format(
                        message)
                    )
                return False

            # get show status metrics
            status_metrics = self.run_query(db, 'SHOW GLOBAL STATUS')
            status_variables = self.run_query(db, 'SHOW VARIABLES')

            # get Uptime
            status['Uptime'] = status_metrics['Uptime']
            self.checks_logger.debug('mysql: getting Uptime - done')

            # Slow queries
            # Determine query depending on version. For 5.02 and above we
            # need the GLOBAL keyword (case 31015)
            # note, update with slow queries store. making it per second?
            # ask jordi about that.
            status['Slow queries'] = status_metrics['Slow_queries']
            self.checks_logger.debug('mysql: getting Slow_queries - done')

            # Note, check for which version of mysql?
            # try:
            #     if self.version_is_above_5(status):
            #         query = 'SHOW GLOBAL STATUS LIKE "Slow_queries"'
            #     else:
            #         query = 'SHOW STATUS LIKE "Slow_queries'

            # QPS - Queries per second
            status['Queries/s'] = self.calculate_per_s(
                'qps', status_metrics['Queries']
            )
            # Note check for which version of mysql
            self.checks_logger.debug('mysql: getting QPS - done')

            # Connection pool
            status['threads connected'] = status_metrics['Threads_connected']
            status['threads running'] = status_metrics['Threads_running']
            status['max connections'] = status_variables['max_connections']
            status['max used connections'] = status_metrics[
                'Max_used_connections']
            status['Connection usage %'] = (
                (status['threads running'] /
                    status['max connections'])*100
            )
            self.checks_logger.debug('mysql: getting connections - done')

            # Buffer pool
            status['buffer pool pages total'] = status_metrics[
                'Innodb_buffer_pool_pages_total']
            status['buffer pool pages free'] = status_metrics[
                'Innodb_buffer_pool_pages_free']
            status['buffer pool pages dirty'] = status_metrics[
                'Innodb_buffer_pool_pages_dirty']
            status['buffer pool pages data'] = status_metrics[
                'Innodb_buffer_pool_pages_data']

            self.checks_logger.debug('mysql: getting buffer pool - done')

            # Query cache items
            status['qcache hits'] = status_metrics['Qcache_hits']
            status['qcache hits/s'] = self.calculate_per_s(
                'qcache_ps', status['qcache hits'])
            status['qcache free memory'] = status_metrics['Qcache_free_memory']
            status['qcache not cached'] = status_metrics['Qcache_not_cached']
            status['qcache in cache'] = status_metrics[
                'Qcache_queries_in_cache']

            self.checks_logger.debug('mysql: getting Qcache data - done')

            # writes, reads, transactions
            writes = (status_metrics['Com_insert'] +
                      status_metrics['Com_replace'] +
                      status_metrics['Com_update'] +
                      status_metrics['Com_delete'])
            status['Writes/s'] = self.calculate_per_s('writes', writes)

            # reads
            reads = status_metrics['Com_select'] + status['qcache hits']
            status['Reads/s'] = self.calculate_per_s('reads', reads)

            try:
                status['RW ratio'] = reads/writes
            except ZeroDivisionError:
                status['RW ratio'] = 0

            # transactions
            transactions = (status_metrics['Com_commit'] +
                            status_metrics['Com_rollback'])
            status['Transactions/s'] = self.calculate_per_s(
                'transactions', transactions)

            self.checks_logger.debug(
                'mysql: getting transactions, reads and writes - done')

            # Aborted connections and clients
            status['aborted clients'] = status_metrics['Aborted_clients']
            status['aborted connects'] = status_metrics['Aborted_connects']

            self.checks_logger.debug(
                'mysql: getting aborted connections - done')

            # Replication - Seconds Behind Master
            secondsBehindMaster = None
            try:
                cursor = db.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SHOW SLAVE STATUS')
                result = cursor.fetchone()

            except MySQLdb.OperationalError as message:

                self.checks_logger.error(
                    'getMySQLStatus: MySQL query error when '
                    'getting SHOW SLAVE STATUS = %s', message)
                result = None

            if result is not None:
                try:
                    # Handle the case when Seconds_Behind_Master is NULL
                    if result['Seconds_Behind_Master'] is None:
                        secondsBehindMaster = -1
                    else:
                        secondsBehindMaster = result['Seconds_Behind_Master']

                    self.checks_logger.debug(
                        'getMySQLStatus: '
                        'secondsBehindMaster = %s', secondsBehindMaster
                    )

                except IndexError as e:
                    self.checks_logger.debug(
                        'getMySQLStatus: secondsBehindMaster empty. %s', e
                    )

            else:
                self.checks_logger.debug(
                    'getMySQLStatus: secondsBehindMaster empty. Result = None.'
                )

            # Created temporary tables in memory and on disk
            status['created tmp tables'] = status_metrics['Created_tmp_tables']
            status['created tmp tables on disk'] = status_metrics[
                'Created_tmp_disk_tables']
            # Note check mysql version?
            self.checks_logger.debug(
                'mysql: getting temporary tables data - done')

            # select_full_join
            status['select full join'] = status_metrics['Select_full_join']
            # note check for mysql version?
            self.checks_logger.debug('mysql: getting select_full_join - done')

            # slave_running
            result = status_metrics['Slave_running']
            if result == 'OFF':
                result = 0
            else:
                result = 1
            status['slave running'] = result
            self.checks_logger.debug(
                'mysql: getting slave_running - done')

            # open files
            status['open files'] = status_metrics['Open_files']
            status['open files limit'] = status_variables['open_files_limit']
            status['Open files usage %'] = (
                (status['open files'] /
                    status['open files limit'])*100
            )
            self.checks_logger.debug('mysql: getting open_files - done')

            # table_locks_waited
            status['table locks waited'] = status_metrics['Table_locks_waited']
            self.checks_logger.debug(
                'mysql: getting table_locks_waited - done')

            # checkpoint age
            # note this needs to be changed.
            try:
                cursor = db.cursor()
                cursor.execute('SHOW ENGINE INNODB STATUS')
                results = cursor.fetchone()[2]

                log_loci = results.find('Log sequence number')
                checkpoint_loci = results.find('Last checkpoint at')

                log_nr = int(re.search(r'\d+', results[log_loci:]).group(0))
                cp_nr = int(re.search(
                    r'\d+', results[checkpoint_loci:]).group(0))

                cp_age = cp_nr - log_nr
                status['Checkpoint age'] = cp_age

            except MySQLdb.OperationalError as message:
                self.checks_logger.error(
                    'mysql: MySQL query error when '
                    'getting checkpoint age = {0}'.format(
                        message)
                )
                return False
            self.checks_logger.debug(
                'mysql: getting checkpoint age - done')

            # note remove this.
            try:
                # Key cache hit ratio
                # http://www.percona.com/blog/2010/02/28/why-you-should-ignore-mysqls-key-cache-hit-ratio/
                key_read = self.get_db_results(
                    db, 'SHOW STATUS LIKE "Key_reads"')

                key_requests = self.get_db_results(
                    db, 'SHOW STATUS LIKE "Key_read_requests"')

                # status['Key cache hit ratio'] = (
                #     100 - ((key_read * 100) / key_requests))

                status['Key reads/s'] = self.calculate_per_s(
                    "Key_reads", key_read)

            except MySQLdb.OperationalError as message:
                self.checks_logger.error(
                    'mysql: MySQL query error when '
                    'getting key cache = {0}'.format(
                        message)
                )
                return False
            self.checks_logger.debug(
                'mysql: getting key cache hit ratio - done')

            # com commands per second

            com = self.raw_config['MySQLServer'].get('mysql_include_per_s')
            if com:
                user_com_ps = com
                user_com_ps = user_com_ps.split(',')
                user_com_ps = [command.strip() for command in user_com_ps]
                user_com_ps = user_com_ps + COMMANDS
            else:
                user_com_ps = COMMANDS

            for command in user_com_ps:
                try:
                    com_per_s = self.calculate_per_s(
                        command, status_metrics[command])
                    status[command.replace('_', ' ')+'/s'] = com_per_s
                except KeyError, e:
                    self.checks_logger.exception(e)

            if self.raw_config['MySQLServer'].get('mysql_include'):
                user_com = self.raw_config['MySQLServer']['mysql_include']
                user_com = user_com.split(',')
                user_com = [command.strip() for command in user_com]
                user_com = user_com + COMMANDS
            else:
                user_com = COMMANDS

                for command in user_com:
                    status[command.replace('_', ' ')] = status_metrics[
                        command]
            self.checks_logger.debug(
                'mysql: getting com_commands - done')

        except Exception:
            self.checks_logger.error(
                'mysql: unable to get data from MySQL - '
                'Exception: {0}'.format(traceback.format_exc())
                )

        self.checks_logger.debug('mysql: completed, returning')
        return status

if __name__ == "__main__":
    """Standalone test"""

    import logging
    import sys
    import json
    import time
    host = 'localhost'
    port = '3306'

    raw_agent_config = {
        'MySQLServer': {
            'mysql_server': host,
            'mysql_port': port,
            'mysql_user': 'jonathan',
            'mysql_pass': 'password',
            'mysql_include_per_s': 'Com_check, Com_checksum, Com_begin',
            # 'mysql_ssl_cert': '/etc/mysql-ssl/client-cert.pem',
            # 'mysql_ssl_key': '/etc/mysql-ssl/client-key.pem'
        }
    }

    main_checks_logger = logging.getLogger('MySQLplugin')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    mysql_check = MySQL({}, main_checks_logger, raw_agent_config)
    while True:
        try:
            result = mysql_check.run()
            print(json.dumps(result, indent=4, sort_keys=True))
        except:
            main_checks_logger.exception("Unhandled Exception")
        finally:
            time.sleep(60)
