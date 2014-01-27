#!/usr/bin/env python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
# written by: Bernardo Macias ( httpstergeek@httpstergeek.com )

from time import sleep
import os
import sys

SPLUNK_HOME = os.environ.get("SPLUNK_HOME")

try:
    from suds.client import Client
    from suds import WebFault
except Exception:
    egg_dir = SPLUNK_HOME + "/etc/apps/compuware_apm_gpn/bin/"
    for filename in os.listdir(egg_dir):
        if filename.endswith(".egg"):
            sys.path.append(egg_dir + filename)
    from suds.client import Client
    from suds import WebFault


class gpn(Client):

    def __int__(self, username, password, url=None):
        """
        @param username: The username for the service.
        @type username: str
        @param password: The password for the service.
        @type password: str
        @param password: The password for the service.
        @type password: str
        @param url: The WSDL url for the service.
        @type url: str
        """
        self.username = username
        self.password = password
        self.url = url

    def __str__(self):
        return '[user: %s\tpassword: %s\twsdl: %s]' % (self.username,
                                                       self.password,
                                                       self.url)

    def service(self, transport=None):
        """
        The B{service} selector is used to select a web service.
        In most cases, the wsdl only defines (1) service in which access
        by subscript is passed through to a L{PortSelector}.  This is also the
        behavior when a I{default} service has been specified.  In cases
        where multiple services have been defined and no default has been
        specified, the service is found by name (or index) and a L{PortSelector}
        for the service is returned.  In all cases, attribute access is
        forwarded to the L{PortSelector} for either the I{first} service or the
        I{default} service (when specified).
        @ivar __client: A suds client.
        @type __client: L{Client}
        @ivar __services: A list of I{wsdl} services.
        @type __services: list
        """
        self.soapclient = Client(self.url)
        if transport:
            self.soapclient = Client(self.url, transport=None)
        return self.soapclient.service

    def last_sent(self):
        """
        Get last sent I{soap} message.
        @return: The last sent I{soap} message.
        @rtype: L{Document}
        """
        return self.soapclient.last_sent()

    def last_received(self):
        """
        Get last received I{soap} message.
        @return: The last received I{soap} message.
        @rtype: L{Document}
        """
        return self.soapclient.last_received()


class account(gpn):
    def __init__(self, username, password,
                 url='http://gsr.webservice.gomez.com/gpnaccountmanagementservice/GpnAccountManagementService.asmx?WSDL'):
        """
        @param username: The username for the service.
        @type username: str
        @param password: The password for the service.
        @type password: str
        @param url: The WSDL url for the service.
        @type url: str
        """
        gpn.__int__(self, username, password, url)

    def getAccountInfo(self):
        return self.service().GetAccountSummary(sUsername=self.username,
                                                sPassword=self.password)

    def getAccountSites(self):
        return self.service().GetAccountSites(sUsername=self.username,
                                              sPassword=self.password)

    def getAccountBackbones(self):
        return self.service().GetAccountBackbones(sUsername=self.username,
                                                  sPassword=self.password)

    def getAccountConfigPackage(self):
        return self.service().GetAccountConfigPackage(sUsername=self.username,
                                                      sPassword=self.password)

    def getAccountMonitors(self, monitorSetDesignator='ALL', statusDesignator='ACTIVE'):
        return self.service().GetAccountMonitors(sUsername=self.username,
                                                 sPassword=self.password,
                                                 sMonitorSetDesignator=monitorSetDesignator,
                                                 sStatusDesignator=statusDesignator)


class export(gpn):
    def __init__(self, username, password, retry=5,
                 url='http://gpn.webservice.gomez.com/DataExportService40/GpnDataExportService.asmx?WSDL'):
        """
        @param username: The username for the service.
        @type username: str
        @param password: The password for the service.
        @type password: str
        @param url: The WSDL url for the service.
        @type url: str
        @param sessiontoken: The sessiontoken for services request.
        @type sessiontoken: str
        @param retry: Number of attempt to connect to API
        @type retry: int
        """
        url = 'http://gpn.webservice.gomez.com/' + \
              'DataExportService40/' + \
              'GpnDataExportService.asmx?WSDL'
        gpn.__int__(self, username, password, url)
        self.sessiontoken = None
        self.retry = retry

    def __str__(self):
        return '[user: %s\tpassword: %s\twsdl: %s\ttoken: %s]' % (self.username,
                                                                  self.password,
                                                                  self.url,
                                                                  self.sessiontoken)

    def getOpenDataFeed(self, ):
        '''Future Enchancement for Live Stream'''
        pass

    def OpenDataFeed2(self,
                      monitorIds=None,
                      siteIds=None,
                      monitorClassDesignator=None,
                      dataDesignator=None,
                      startTime=None,
                      endTime=None,
                      orderDesignator='TIME'):
        """
        Makes response request.  response retreived by GetResponseData. Needs work to handle multiple Monitor Ids.
        @param monitorIds: The Monitor Ids for the service.
        @type monitorSiteIds: dict {'int', int}
        @param siteIds: The Site Ids for the service.
        @type siteIds: dict {'int', int} or None.
        @param monitorClassDesignator: The class type of monitor(s).
        @type monitorClassDesignator: str
        @param dataDesignator: The data Designator for services request.
        @type dataDesignator: str
        @param startTime: The start time of monitor(s).
        @type startTime: str, '2013-11-12 00:45:00'
        @param endTime: The end time of monitor(s).
        @type endTime: str, '2013-11-12 00:45:00'
        @param sOrderDesignator: Order of data returned.
        @type sOrderDesignator: str, 'TIME'
        """
        attempt = 0
        while attempt < self.retry:
            try:
                response = self.service().OpenDataFeed2(sUsername=self.username,
                                                        sPassword=self.password,
                                                        iMonitorIdSet=monitorIds,
                                                        iSiteIdSet=siteIds,
                                                        sMonitorClassDesignator=monitorClassDesignator,
                                                        sDataDesignator=dataDesignator,
                                                        sStartTime=startTime,
                                                        sEndTime=endTime,
                                                        sOrderDesignator=orderDesignator)
            except Exception, e:
                print '%s' % (e)
                exit(1)
            if response.Status.eStatus == "STATUS_SUCCESS":
                self.sessiontoken = response.SessionToken
            return response
            sleep(15)
            attempt += 1

    def getOpenDataFeed3(self, ):
        '''Future Enhancement'''
        pass

    def closeDataFeed(self):
        """Closes Gomez Feed once results are returned"""

        try:
            return self.service().CloseDataFeed(sSessionToken=self.sessiontoken)
        except Exception, e:
            print '%s' % (details)
            exit(1)

    def getResponseData(self):
        """Retreives response data from Gomez Networks"""
        status = 'STATUS_DATA_NOT_READY'
        try:
            while status == 'STATUS_DATA_NOT_READY':
                response = self.service().GetResponseData(sSessionToken=self.sessiontoken)
                status = response.Status.eStatus
                if status == 'STATUS_DATA_NOT_READY':
                    sleep(10)
                return response
        except Exception, e:
            self.closeDataFeed()
            print '%s' % (e)
            exit(1)

    def getErrorCodes(self):
        try:
            return self.service().GetErrorCodes()
        except Exception,  e:
            print '%s' % (e)
            exit(1)


