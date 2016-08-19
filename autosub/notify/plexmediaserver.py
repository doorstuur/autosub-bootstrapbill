import autosub
import logging

import urllib
import urllib2
import base64

from xml.etree import ElementTree as ET

log = logging.getLogger('thelogger')

def test_update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword):
    log.debug("Plex Media Server: Trying to update the TV shows library.")
    plexservertoken = None
    if autosub.PLEXSERVERTOKEN:
        plexservertoken = autosub.PLEXSERVERTOKEN

    return _update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword, plexservertoken)

def send_update_library():
    log.debug("Plex Media Server: Trying to update the TV shows library.")
    plexserverhost = autosub.PLEXSERVERHOST
    plexserverport = int(autosub.PLEXSERVERPORT)
    plexserverusername = autosub.PLEXSERVERUSERNAME
    plexserverpassword = autosub.PLEXSERVERPASSWORD
    plexservertoken = autosub.PLEXSERVERTOKEN
    return _update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword, plexservertoken)

def _update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword, plexservertoken):
    if not plexserverhost:
        plexserverhost = autosub.PLEXSERVERHOST
    
    if not plexserverport:
        plexserverport = int(autosub.PLEXSERVERPORT)

    if not plexserverusername:
        plexserverusername = autosub.PLEXSERVERUSERNAME

    if not plexserverpassword:
        plexserverpassword = autosub.PLEXSERVERPASSWORD

    if not plexservertoken:
        plexservertoken = autosub.PLEXSERVERTOKEN

    #Maintain support for older Plex installations without myPlex
    if not plexservertoken and not plexserverusername and not plexserverpassword:
        url = "http://%s:%s/library/sections" % (plexserverhost, plexserverport)

        try:
            xml_sections = ET.parse(urllib.urlopen(url))
        except IOError, e:
            log.error("Plex Media Server: Error while trying to contact: %s" % e)
            return False
    else:
        #Fetch X-Plex-Token if it doesn't exist but a username/password do
        if not plexservertoken and plexserverusername and plexserverpassword:
            log.debug("Fetching a new X-Plex-Token from plex.tv")
            authheader = "Basic %s" % base64.encodestring('%s:%s' % (plexserverusername, plexserverpassword))[:-1]

            request = urllib2.Request("https://plex.tv/users/sign_in.xml", '');
            request.add_header("Authorization", authheader)
            request.add_header("X-Plex-Product", "AutoSub Notifier")
            request.add_header("X-Plex-Client-Identifier", "b3a6b24dcab2224bdb101fc6aa08ea5e2f3147d6")
            request.add_header("X-Plex-Version", "1.0")
            
            response = urllib2.urlopen(request)

            auth_tree = ET.fromstring(response.read())
            plexservertoken = auth_tree.findall(".//authentication-token")[0].text
            autosub.PLEXSERVERTOKEN = plexservertoken

            if plexservertoken:
                #Add X-Plex-Token header for myPlex support workaround
                response = urllib2.urlopen('%s/%s?X-Plex-Token=%s' % (
                    "%s:%s" % (plexserverhost, plexserverport),
                    'library/sections',
                    plexservertoken
                ))

                xml_sections = ET.fromstring(response.read())

                sections = xml_sections.findall('Directory')

                if not sections:
                    log.debug("Plex Media Server: Server not running on: %s:%s" % (plexserverhost, plexserverport))
                    return False

                for s in sections:
                    if s.get('type') == "show":
                        try:
                            urllib2.urlopen('%s/%s?X-Plex-Token=%s' % (
                                "%s:%s" % (plexserverhost, plexserverport),
                                "library/sections/%s/refresh" % (s.get('key')),
                                plexservertoken
                            ))
                            log.debug("Plex Media Server: TV Shows library (%s) is currently updating." % s.get('title'))
                            return True
                        except Exception, e:
                            log.error("Plex Media Server: Error updating library section: %s" % e)
                            return False

                return True