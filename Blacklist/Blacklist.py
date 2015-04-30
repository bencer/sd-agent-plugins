"""
Blacklist Plugin for Server Density to monitor Email BlackList Listing
Author: Andre Freitas
Twitter: http://twitter.com/cantodoandre
Linkedin: http://pt.linkedin.com/in/andrefreitas1/

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import re
import copy
import socket

""" 
Black lists 
"""
blacklists = [
 'b.barracudacentral.org',
 'bl.deadbeef.com',
 'bl.emailbasura.org',
 'bl.spamcannibal.org',
 'bl.spamcop.net',
 'blackholes.five-ten-sg.com',
 'blacklist.woody.ch',
 'bogons.cymru.com',
 'cbl.abuseat.org',
 'cdl.anti-spam.org.cn',
 'combined.abuse.ch',
 'combined.rbl.msrbl.net',
 'db.wpbl.info',
 'dnsbl-1.uceprotect.net',
 'dnsbl-2.uceprotect.net',
 'dnsbl-3.uceprotect.net',
# 'dnsbl.ahbl.org',
 'dnsbl.cyberlogic.net',
 'dnsbl.inps.de',
 'dnsbl.njabl.org',
 'dnsbl.sorbs.net',
 'drone.abuse.ch',
 'drone.abuse.ch',
 'duinv.aupads.org',
 'dul.dnsbl.sorbs.net',
 'dul.ru',
 'dyna.spamrats.com',
 'dynip.rothen.com',
 'http.dnsbl.sorbs.net',
 'images.rbl.msrbl.net',
 'ips.backscatterer.org',
 'ix.dnsbl.manitu.net',
 'korea.services.net',
 'misc.dnsbl.sorbs.net',
 'noptr.spamrats.com',
 'ohps.dnsbl.net.au',
 'omrs.dnsbl.net.au',
 'orvedb.aupads.org',
 'osps.dnsbl.net.au',
 'osrs.dnsbl.net.au',
 'owfs.dnsbl.net.au',
 'owps.dnsbl.net.au',
 'pbl.spamhaus.org',
 'phishing.rbl.msrbl.net',
 'probes.dnsbl.net.au',
 'proxy.bl.gweep.ca',
 'proxy.block.transip.nl',
 'psbl.surriel.com',
 'rbl.interserver.net',
 'rbl.megarbl.net',
 'rdts.dnsbl.net.au',
 'relays.bl.gweep.ca',
 'relays.bl.kundenserver.de',
 'relays.nether.net',
 'residential.block.transip.nl',
 'ricn.dnsbl.net.au',
 'rmst.dnsbl.net.au',
 'sbl.spamhaus.org',
 'short.rbl.jp',
 'smtp.dnsbl.sorbs.net',
 'socks.dnsbl.sorbs.net',
 'spam.abuse.ch',
 'spam.dnsbl.sorbs.net',
 'spam.rbl.msrbl.net',
 'spam.spamrats.com',
 'spamlist.or.kr',
 'spamrbl.imp.ch',
 't3direct.dnsbl.net.au',
# 'tor.ahbl.org',
 'tor.dnsbl.sectoor.de',
 'torserver.tor.dnsbl.sectoor.de',
 'ubl.lashback.com',
 'ubl.unsubscore.com',
 'virbl.bit.nl',
 'virus.rbl.jp',
 'virus.rbl.msrbl.net',
 'web.dnsbl.sorbs.net',
 'wormrbl.imp.ch',
 'xbl.spamhaus.org',
 'zen.spamhaus.org',
 'zombie.dnsbl.sorbs.net']


class Blacklist (object):
    def __init__(self, agentConfig, checksLogger, rawConfig):
        self.agentConfig = agentConfig
        self.checksLogger = checksLogger
        self.rawConfig = rawConfig
        self.blacklists = blacklists
        self.ips = self.get_system_public_ips()
 
    def get_system_public_ips(self):
        ips_text = os.popen("ifconfig | grep -E \'inet (addr|end)\'").read().strip()
        ips_lines_list = ips_text.split("\n")
        ips_set = set([])
        for ip_line in ips_lines_list:
            ip = ""
            if(re.search("inet end", ip_line)):
                ip = ip_line.split(":")[1].split(" ")[1]
            elif(re.search("inet addr", ip_line)):
                ip = ip_line.split(":")[1].split(" ")[0]
            if(not self.ip_is_private(ip)):
                ips_set.add(ip)
        return ips_set

    def ip_is_private(self, ip):
        regex = "127\.0\.0\.1"
        regex += "|10\."
        regex += "|172\.1[6-9]\.|172\.2[0-9]\.|172\.3[0-1]"
        regex += "|192\.168\."
        return bool(re.match(regex, ip))

    def ip_is_listed(self, ip, dnsbl):
        ip = reverse_ip(ip)
        try:
            socket.gethostbyname(ip + "." + dnsbl)
            return True
        except:
            return False

    def run(self):
        data = {'blacklists': 0}
        for blacklist in self.blacklists:
            data[blacklist] = 0
            for ip in self.ips:
                if (self.ip_is_listed(ip, blacklist)):
                    data[blacklist] += 1
                    data['blacklists'] += 1
        return data


"""
A function to reverse an IP to prepare it to test in the DNSBL
"""
def reverse_ip(ip):
    octects = ip.split(".")
    octects = list(reversed(octects))
    reversed_ip = ".".join(octects)
    return reversed_ip
