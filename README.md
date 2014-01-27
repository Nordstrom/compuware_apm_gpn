Compuware GPN - Modular Input for Splunk
=================

Compuware APM Synthetic Modular Input is an app that uses Compuware GPN API (formally Gomez Networks). 
This modular input utilizies suds python library.


Requirements
---------

* This version has been test on 6.x and should work on 5.x.

* App is known ot work on Linux, Windows, and Mac OS X, but has not been
 tested on other operating systems.

* App requires internet access and suds.

* Miminum of 2 GB RAM and 1.8 GHz CPU.

* This currently does not work behind a proxy.


Prerequisites
---------

Splunk version 5.0.1 or Higher

You can download it [Splunk][splunk-download].  And see the [Splunk documentation][] for instructions on installing and more.
[Splunk]:http://www.splunk.com
[Splunk documentation]:http://docs.splunk.com/Documentation/Splunk/latest/User
[splunk-download]:http://www.splunk.com/download

Installation instructions
---------

1) Use the following rule to determine Monitor IDs for your account: http://gsr.webservice.gomez.com/gpnaccountmanagementservice/GpnAccountManagementService.asmx?op=GetAccountMonitors

2) Enter Account User Name and Password. sUsername: sPassword: sMonitorSetDesignator: UTATX sStatusDesignator: ACTIVE

3) Select Monitor ID. mid attributes are Monitors_IDs. example. Monitor mid="5325436"

4) Optional use getmonitorsids.py. usage: getmonitorids.py [-h] --user USER --pw PW

### Example ouput for getmonitorids

    Name: UTA - KeyWord blue
         MonitorID: 11420
         frequency_milsec: 3600
         modified: 11/14/2009 6:38:14 AM
         created: 11/14/2009 6:38:14 AM
    Name: UTA - Home page - 5 mins
        MonitorID: 11822
        frequency_milsec: 300
        modified: 7/8/2008 3:56:06 PM
        created: 7/8/2008 3:56:06 PM


Recommendations
---------

It is recommend that this be installed on an intermedate forwarder.
Interval should be no longer than 3600 depending on number of transactions and data volume from Compuware API.

Future Enhancements
---------

1) Proxy Support

2) Site filters
