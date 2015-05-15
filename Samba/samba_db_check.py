#!/usr/bin/python
import ldb, sys
import samba
from samba.credentials import Credentials
from samba.auth import system_session
from samba.samdb import SamDB
from samba.dbchecker import dbcheck

lp = samba.param.LoadParm()
lp.load("/etc/samba/smb.conf")
creds = Credentials()
creds.guess(lp)
session = system_session()

samdb = SamDB("/var/lib/samba/private/sam.ldb",
              session_info=session,
              credentials=creds,
              lp=lp)
samdb_schema = samdb
search_scope = ldb.SCOPE_SUBTREE
controls = ['show_deleted:1']
attrs = ['*']
chk = dbcheck(samdb, samdb_schema=samdb_schema, verbose=False,
              fix=False, yes=False, quiet=True, in_transaction=False,
              reset_well_known_acls=False)
error_count = chk.check_database(DN=None, scope=search_scope,
        controls=controls, attrs=attrs)

print error_count
