# Easee Cloud Python Plugin
#
# Author: flopp999
#
"""
<plugin key="EaseeCloud" name="Easee Cloud 0.2" author="flopp999" version="0.2" wikilink="https://github.com/flopp999/EaseeCloud-Domoticz" externallink="https://www.easee.com">
    <description>
        <h2>Support me with a coffee &<a href="https://www.buymeacoffee.com/flopp999">https://www.buymeacoffee.com/flopp999</a></h2><br/>
        <h2>or use my Tibber link &<a href="https://tibber.com/se/invite/8af85f51">https://tibber.com/se/invite/8af85f51</a></h2><br/>
        <h3>Categories that will be fetched</h3>
        <ul style="list-style-type:square">
            <li>Charger State</li>
            <li>Charger Config</li>
        </ul>
        <h3>Configuration</h3>
        <h2>Phone Number must start with your country code e.g. +47 then your phone number without the 0</h2>
    </description>
    <params>
        <param field="Mode4" label="Phone Number" width="320px" required="true" default="+46123123123"/>
        <param field="Mode2" label="Password" width="350px" required="true" default="Secret"/>
        <param field="Mode6" label="Debug to file (Easee.log)" width="70px">
            <options>
                <option label="Yes" value="Yes" />
                <option label="No" value="No" />
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz

Package = True

try:
    import requests, json, os, logging
except ImportError as e:
    Package = False

try:
    from logging.handlers import RotatingFileHandler
except ImportError as e:
    Package = False

try:
    from datetime import datetime
except ImportError as e:
    Package = False

dir = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger("EaseeCloud")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(dir+'/EaseeCloud.log', maxBytes=1000000, backupCount=5)
logger.addHandler(handler)

class BasePlugin:
    enabled = False

    def __init__(self):
        self.token = ''
        self.loop = 0
        self.Count = 5
        return

    def onStart(self):
        WriteDebug("===onStart===")
        self.PhoneNumber = Parameters["Mode4"]
        self.Password = Parameters["Mode2"]
        self.Agree = Parameters["Mode5"]
        self.Charger = 0
        self.NoOfSystems = ""
        self.FirstRun = True

        if len(self.PhoneNumber) < 10:
            Domoticz.Log("Phone Number too short")
            WriteDebug("Identifier too short")

        if len(self.Password) < 4:
            Domoticz.Log("Password too short")
            WriteDebug("Password too short")

        self.GetToken = Domoticz.Connection(Name="Get Token", Transport="TCP/IP", Protocol="HTTPS", Address="api.easee.cloud", Port="443")
        self.GetRefreshToken = Domoticz.Connection(Name="Get Refrsh Token", Transport="TCP/IP", Protocol="HTTPS", Address="api.easee.cloud", Port="443")
        self.GetState = Domoticz.Connection(Name="Get State", Transport="TCP/IP", Protocol="HTTPS", Address="api.easee.cloud", Port="443")
        self.GetCharger = Domoticz.Connection(Name="Get Charger", Transport="TCP/IP", Protocol="HTTPS", Address="api.easee.cloud", Port="443")
        self.GetConfig = Domoticz.Connection(Name="Get Config", Transport="TCP/IP", Protocol="HTTPS", Address="api.easee.cloud", Port="443")
        self.GetToken.Connect()

    def onDisconnect(self, Connection):
        WriteDebug("onDisconnect called for connection '"+Connection.Name+"'.")

    def onConnect(self, Connection, Status, Description):
        WriteDebug("onConnect")
        if CheckInternet() == True:
            if Connection.Name == ("Get Token"):
                WriteDebug("Get Token")
                data = "{\"userName\":\""+self.PhoneNumber+"\",\"password\":\""+self.Password+"\"}"
                headers = { 'accept': 'application/json', 'Host': 'api.easee.cloud', 'Content-Type': 'application/*+json'}
                Connection.Send({'Verb':'POST', 'URL': '/api/accounts/token', 'Headers': headers, 'Data': data})

            if Connection.Name == ("Get Refresh Token"):
                WriteDebug("Get Refresh Token")
                data = "{\"accessToken\":\""+self.Token+"\",\"refreshToken\":\""+self.RefreshToken+"\"}"
                headers = { 'accept': 'application/json', 'Host': 'api.easee.cloud', 'Content-Type': 'application/*+json'}
                Connection.Send({'Verb':'POST', 'URL': '/api/accounts/refresh_token', 'Headers': headers, 'Data': data})

            if Connection.Name == ("Get Charger"):
                WriteDebug("Get Charger")
                headers = { 'Host': 'api.easee.cloud', 'Authorization': 'Bearer '+self.token}
                Connection.Send({'Verb':'GET', 'URL': '/api/chargers', 'Headers': headers, 'Data': {} })

            if Connection.Name == ("Get State"):
                WriteDebug("Get State")
                headers = { 'Host': 'api.easee.cloud', 'Authorization': 'Bearer '+self.token}
                Connection.Send({'Verb':'GET', 'URL': '/api/chargers/'+self.Charger+'/state', 'Headers': headers, 'Data': {} })

            if Connection.Name == ("Get Config"):
                WriteDebug("Get Config")
                headers = { 'Host': 'api.easee.cloud', 'Authorization': 'Bearer '+self.token}
                Connection.Send({'Verb':'GET', 'URL': '/api/chargers/'+self.Charger+'/config', 'Headers': headers, 'Data': {} })

    def onMessage(self, Connection, Data):
        Status = int(Data["Status"])

        if Status == 200:

            if Connection.Name == ("Get Token"):
                Data = Data['Data'].decode('UTF-8')
                Data = json.loads(Data)
                self.token = Data["accessToken"]
                self.refreshtoken = Data["refreshToken"]
#                self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBY2NvdW50SWQiOjk0Mjc2LCJVc2VySWQiOjc2MzE0LCJ1bmlxdWVfbmFtZSI6Ijk0Mjc2Iiwicm9sZSI6IlVzZXIiLCJuYmYiOjE2MjMwOTUwMDIsImV4cCI6MTYyMzE4MTQwMiwiaWF0IjoxNjIzMDk1MDAyfQ.yQfgoMgRzVn3czI7LxcUXKSNK83oanmeL5PGoaclEqw"
#                Domoticz.Log(str(Data["refreshToken"]))
#                Domoticz.Log(str(self.token))
                self.GetToken.Disconnect()
                self.GetCharger.Connect()

            if Connection.Name == ("Get Refresh Token"):
                Data = Data['Data'].decode('UTF-8')
                Data = json.loads(Data)
                self.token = Data["accessToken"]
                self.refreshtoken = Data["refreshToken"]
#                self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBY2NvdW50SWQiOjk0Mjc2LCJVc2VySWQiOjc2MzE0LCJ1bmlxdWVfbmFtZSI6Ijk0Mjc2Iiwicm9sZSI6IlVzZXIiLCJuYmYiOjE2MjMwOTUwMDIsImV4cCI6MTYyMzE4MTQwMiwiaWF0IjoxNjIzMDk1MDAyfQ.yQfgoMgRzVn3czI7LxcUXKSNK83oanmeL5PGoaclEqw"
#                Domoticz.Log(str(Data["refreshToken"]))
#                Domoticz.Log(str(self.token))
                self.GetState.Connect()

            if Connection.Name == ("Get Charger"):
                Data = Data['Data'].decode('UTF-8')
                Data = json.loads(Data)
#                Domoticz.Log(str(Data))
                self.Charger = Data[0]["id"]
#                Domoticz.Log("Ch)
#                    UpdateDevice(name, 0, str(value))
                self.GetCharger.Disconnect()
                self.GetState.Connect()

            if Connection.Name == ("Get State"):
                Data = Data['Data'].decode('UTF-8')
                Data = json.loads(Data)
                Domoticz.Log("State updated")
                for name,value in Data.items():
                    UpdateDevice(name, 0, str(value))
                self.GetState.Disconnect()
                self.GetConfig.Connect()

            if Connection.Name == ("Get Config"):
                Data = Data['Data'].decode('UTF-8')
                Data = json.loads(Data)
                Domoticz.Log("Config updated")
                for name,value in Data.items():
                    UpdateDevice(name, 0, str(value))
                self.GetConfig.Disconnect()

        elif Status == 401:
            Data = Data['Data'].decode('UTF-8')
            Data = json.loads(Data)
            Domoticz.Log(str(Data))
            self.GetRefreshToken.Connect()



        elif self.Agree == "False":
            Domoticz.Log("You must agree")
        else:
            WriteDebug("Status = "+str(Status))
            Domoticz.Error(str("Status "+str(Status)))
            Domoticz.Error(str(Data))
            if _plugin.GetToken.Connected():
                _plugin.GetToken.Disconnect()
            if _plugin.GetState.Connected():
                _plugin.GetState.Disconnect()

    def onHeartbeat(self):
        self.Count += 1
        if self.Count == 12:
            self.GetState.Connect()
            self.Count = 0

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def UpdateDevice(name, nValue, sValue):

    if name == "smartCharging":
        ID = 1
        unit = ""
    if name == "cableLocked":
        ID = 2
        unit = ""
    if name == "chargerOpMode":
        ID = 3
        unit = ""
    if name == "totalPower":
        ID = 4
        unit = ""
    if name == "sessionEnergy":
        ID = 5
        unit = ""
    if name == "energyPerHour":
        ID = 6
        unit = ""
    if name == "wiFiRSSI":
        ID = 7
        unit = ""
    if name == "cellRSSI":
        ID = 8
        unit = "dB"
    if name == "localRSSI":
        unit = ""
        ID = 9
    if name == "outputPhase":
        ID = 10
        unit = ""
    if name == "dynamicCircuitCurrentP1":
        ID = 11
        unit = ""
    if name == "dynamicCircuitCurrentP2":
        ID = 12
        unit = ""
    if name == "dynamicCircuitCurrentP3":
        ID = 13
        unit = ""
    if name == "latestPulse":
        ID = 14
        sValue = sValue.replace('Z', '')
        sValue = sValue.replace('T', ' ')
        sValue = sValue + " UTC"
        unit = ""
    if name == "chargerFirmware":
        ID = 15
        unit = ""
    if name == "latestFirmware":
        ID = 16
        unit = ""
    if name == "voltage":
        ID = 17
        unit = "Volt"
    if name == "chargerRAT":
        ID = 18
        unit = ""
    if name == "lockCablePermanently":
        ID = 19
        unit = ""
    if name == "inCurrentT2":
        ID = 20
        unit = ""
    if name == "inCurrentT3":
        ID = 21
        unit = ""
    if name == "inCurrentT4":
        ID = 22
        unit = ""
    if name == "inCurrentT5":
        ID = 23
        unit = ""
    if name == "outputCurrent":
        ID = 24
        unit = ""
    if name == "isOnline":
        ID = 25
        unit = ""
    if name == "inVoltageT1T2":
        ID = 26
        unit = "Volt"
    if name == "inVoltageT1T3":
        ID = 27
        unit = "Volt"
    if name == "inVoltageT1T4":
        ID = 28
        unit = "Volt"
    if name == "inVoltageT1T5":
        ID = 29
        unit = "Volt"
    if name == "inVoltageT2T3":
        ID = 30
        unit = "Volt"
    if name == "inVoltageT2T4":
        ID = 31
        unit = "Volt"
    if name == "inVoltageT2T5":
        ID = 32
        unit = "Volt"
    if name == "inVoltageT3T4":
        ID = 33
        unit = "Volt"
    if name == "inVoltageT3T5":
        ID = 34
        unit = "Volt"
    if name == "inVoltageT4T5":
        ID = 35
        unit = "Volt"
    if name == "ledMode":
        ID = 36
        unit = ""
    if name == "cableRating":
        ID = 37
        unit = ""
    if name == "dynamicChargerCurrent":
        ID = 38
        unit = ""
    if name == "circuitTotalAllocatedPhaseConductorCurrentL1":
        ID = 39
        unit = ""
    if name == "circuitTotalAllocatedPhaseConductorCurrentL2":
        ID = 40
        unit = ""
    if name == "circuitTotalAllocatedPhaseConductorCurrentL3":
        ID = 41
        unit = ""
    if name == "circuitTotalPhaseConductorCurrentL1":
        ID = 42
        unit = ""
    if name == "circuitTotalPhaseConductorCurrentL2":
        ID = 43
        unit = ""
    if name == "circuitTotalPhaseConductorCurrentL3":
        ID = 44
        unit = ""
    if name == "reasonForNoCurrent":
        ID = 45
        unit = ""
    if name == "wiFiAPEnabled":
        ID = 46
        unit = ""
    if name == "lifetimeEnergy":
        ID = 47
        unit = ""
    if name == "offlineMaxCircuitCurrentP1":
        ID = 48
        unit = ""
    if name == "offlineMaxCircuitCurrentP2":
        ID = 49
        unit = ""
    if name == "offlineMaxCircuitCurrentP3":
        ID = 50
        unit = ""
    if name == "errorCode":
        ID = 51
        unit = ""
    if name == "fatalErrorCode":
        ID = 52
        unit = ""
    if name == "errors":
        ID = 53
        unit = ""
    if name == "isEnabled":
        ID = 54
        unit = ""
    if name == "lockCablePermanently":
        ID = 55
        unit = ""
    if name == "authorizationRequired":
        ID = 56
        unit = ""
    if name == "remoteStartRequired":
        ID = 57
        unit = ""
    if name == "smartButtonEnabled":
        ID = 58
        unit = ""
    if name == "wiFiSSID":
        ID = 59
        unit = ""
    if name == "detectedPowerGridType":
        ID = 60
        unit = ""
    if name == "offlineChargingMode":
        ID = 61
        unit = ""
    if name == "circuitMaxCurrentP1":
        ID = 62
        unit = ""
    if name == "circuitMaxCurrentP2":
        ID = 63
        unit = ""
    if name == "circuitMaxCurrentP3":
        ID = 64
        unit = ""
    if name == "enableIdleCurrent":
        ID = 65
        unit = ""
    if name == "limitToSinglePhaseCharging":
        ID = 66
        unit = ""
    if name == "phaseMode":
        ID = 67
        unit = ""
    if name == "localNodeType":
        ID = 68
        unit = ""
    if name == "localAuthorizationRequired":
        ID = 69
        unit = ""
    if name == "localRadioChannel":
        ID = 70
        unit = ""
    if name == "localShortAddress":
        ID = 71
        unit = ""
    if name == "localParentAddrOrNumOfNodes":
        ID = 72
        unit = ""
    if name == "localPreAuthorizeEnabled":
        ID = 73
        unit = ""
    if name == "localAuthorizeOfflineEnabled":
        ID = 74
        unit = ""
    if name == "allowOfflineTxForUnknownId":
        ID = 75
        unit = ""
    if name == "maxChargerCurrent":
        ID = 76
        unit = ""
    if name == "ledStripBrightness":
        ID = 77
        unit = ""
    if name == "chargingSchedule":
        ID = 78
        unit = ""

    if (ID in Devices):
        if (Devices[ID].sValue != sValue):
            Devices[ID].Update(nValue, str(sValue))

    if (ID not in Devices):
        if sValue == "-32768":
            Used = 0
        else:
            Used = 1
        if ID == 14:
            Domoticz.Device(Name=name, Unit=ID, TypeName="Text", Used=1).Create()

        else:
            Domoticz.Device(Name=name, Unit=ID, TypeName="Custom", Options={"Custom": "0;"+unit}, Used=Used, Description="ParameterID=\nDesignation=").Create()


def CheckInternet():
    WriteDebug("Entered CheckInternet")
    try:
        WriteDebug("Ping")
        requests.get(url='https://api.easee.cloud/', timeout=2)
        WriteDebug("Internet is OK")
        return True
    except:
        if _plugin.GetToken.Connected():
            _plugin.GetToken.Disconnect()
        if _plugin.GetState.Connected():
            _plugin.GetState.Disconnect()
        if _plugin.GetConfig.Connected():
            _plugin.GetConfig.Disconnect()
        WriteDebug("Internet is not available")
        return False

def WriteDebug(text):
    if Parameters["Mode6"] == "Yes":
        timenow = (datetime.now())
        logger.info(str(timenow)+" "+text)

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onMessage(Connection, Data):
    _plugin.onMessage(Connection, Data)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
