# Easee Cloud Python Plugin
#
# Author: flopp999
#
"""
<plugin key="EaseeCloud" name="Easee Cloud 0.1" author="flopp999" version="0.1" wikilink="https://github.com/flopp999/EaseeCloud-Domoticz" externallink="https://www.easee.com">
    <description>
        <h2>Support me with a coffee &<a href="https://www.buymeacoffee.com/flopp999">https://www.buymeacoffee.com/flopp999</a></h2><br/>
        <h1>To use this plugin you need to agree to send data to me. I will use the data to develop the plugin so it will fit all NIBE systems</h1>
        <h3>You can see what data I have collect by follow this link. I will onlt collect data once after startup. It will include all your parameters, your SystemID and you categories.</h3>
        <h3>&<a href="https://rhematic-visitors.000webhostapp.com/[your systemid]">https://rhematic-visitors.000webhostapp.com/[your systemid]</a></h3>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>..</li>
        </ul>
        <h3>Categories that will be fetched, if they exist</h3>
        <ul style="list-style-type:square">
            <li>ACTIVE_COOLING_2_PIPE</li>
        </ul>
        <h3>How to get your Identifier, Secret and URL?</h3>
        <h4>&<a href="https://github.com/flopp999/NIBEUplink-Domoticz#identifier-secret-and-callback-url">https://github.com/flopp999/NIBEUplink-Domoticz#identifier-secret-and-callback-url</a></h4>
        <h3>How to get your Access Code?</h3>
        <h4>&<a href="https://github.com/flopp999/NIBEUplink-Domoticz#access-code">https://github.com/flopp999/NIBEUplink-Domoticz#access-code</a></h4>
        <h3>Configuration</h3>
    </description>
    <params>
        <param field="Mode5" label="Agree to send data to developer of this plugin" width="70px" required="true">
            <options>
                <option label="Yes" value=True />
                <option label="No" value=False />
            </options>
        </param>
        <param field="Mode4" label="Phone Number" width="320px" required="true" default="Identifier"/>
        <param field="Mode2" label="Password" width="350px" required="true" default="Secret"/>
        <param field="Mode6" label="Debug to file (Nibe.log)" width="70px">
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
        self.Ident = Parameters["Mode4"]
        self.Secret = Parameters["Mode2"]
        self.Agree = Parameters["Mode5"]
        self.SystemID = ""
        self.NoOfSystems = ""
        self.SystemUnitId = 0
        self.FirstRun = True
        self.AllSettings = True
        self.Categories = []
        self.Connections = {}

        if len(self.Ident) < 10:
            Domoticz.Log("Phone Number too short")
            WriteDebug("Identifier too short")
            self.Ident = CheckFile("Ident")
        else:
            WriteFile("Ident",self.Ident)

        if len(self.Secret) < 4:
            Domoticz.Log("Secret too short")
            WriteDebug("Secret too short")
            self.Secret = CheckFile("Secret")
        else:
            self.Secret = self.Secret.replace("+", "%2B")
            WriteFile("Secret",self.Secret)

        self.GetToken = Domoticz.Connection(Name="Get Token", Transport="TCP/IP", Protocol="HTTPS", Address="api.easee.cloud", Port="443")
        self.GetToken.Connect()
        self.GetData = Domoticz.Connection(Name="Get Data", Transport="TCP/IP", Protocol="HTTPS", Address="api.easee.cloud", Port="443")

    def onDisconnect(self, Connection):
        WriteDebug("onDisconnect called for connection '"+Connection.Name+"'.")
        for x in self.Connections:
            if Connection.Name in self.Connections:
#                if Connection.Connected() == False
                self.Connections[Connection.Name] = Connection.Connected()

    def onConnect(self, Connection, Status, Description):
        WriteDebug("onConnect")
        if CheckInternet() == True and self.AllSettings == True:
            if Connection.Name == ("Get Token"):
                WriteDebug("Get Token")
                headers = { 'accept': 'application/json', 'Host': 'api.easee.cloud', 'Content-Type': 'application/*+json'}
                data = { 'grantType': 'password' , 'username': '+46' , 'password': '' }
                Connection.Send({'Verb':'POST', 'URL': '/api/accounts/token', 'Headers': headers, 'Data': "{\"userName\":\"+46\",\"password\":\"!\"}"})

            if Connection.Name == ("Get Data"):
                WriteDebug("Get Data")
                headers = { 'Host': 'api.easee.cloud', 'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBY2NvdW50SWQiOjk0Mjc2LCJVc2VySWQiOjc2MzE0LCJ1bmlxdWVfbmFtZSI6Ijk0Mjc2Iiwicm9sZSI6IlVzZXIiLCJuYmYiOjE2MjMwOTUwMDIsImV4cCI6MTYyMzE4MTQwMiwiaWF0IjoxNjIzMDk1MDAyfQ.yQfgoMgRzVn3czI7LxcUXKSNK83oanmeL5PGoaclEqw'}
                Connection.Send({'Verb':'GET', 'URL': '/api/chargers/EH29VM7Z/state', 'Headers': headers, 'Data': {} })

    def onMessage(self, Connection, Data):
#        Domoticz.Log(str(Data))
        Status = int(Data["Status"])

        if (Status == 200) and self.Agree == "True":

            if Connection.Name == ("Get Token"):
                Data = Data['Data'].decode('UTF-8')
                Data = json.loads(Data)
                self.token = Data["accessToken"]
#                Domoticz.Log(str(Data))

#                with open(dir+'/EaseeCloud.ini') as jsonfile:
#                    data = json.load(jsonfile)
#                data["Config"][0]["Access"] = Data["accessToken"]
#                with open(dir+'/EaseeCloud.ini', 'w') as outfile:
#                    json.dump(data, outfile, indent=4)
                self.GetToken.Disconnect()
                self.GetData.Connect()

            if Connection.Name == ("Get Data"):
                Data = Data['Data'].decode('UTF-8')
                Data = json.loads(Data)
#                Domoticz.Log(str(Data))
                for name,value in Data.items():
#                    Domoticz.Log(para)
#                    Domoticz.Log(name+" "+str(value))
                    UpdateDevice(name, 0, value)

                self.GetData.Disconnect()


        elif self.Agree == "False":
            Domoticz.Log("You must agree")
        else:
            WriteDebug("Status = "+str(Status))
            Domoticz.Error(str("Status "+str(Status)))
            Domoticz.Error(str(Data))
            if _plugin.GetToken.Connected():
                _plugin.GetToken.Disconnect()
            if _plugin.GetData.Connected():
                _plugin.GetData.Disconnect()

    def onHeartbeat(self):
        self.GetData.Connect()

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def UpdateDevice(name, nValue, sValue):

    if name == "smartCharging":
        ID = 1
    if name == "cableLocked":
        ID = 2
    if name == "chargerOpMode":
        ID = 3
    if name == "totalPower":
        ID = 4
    if name == "sessionEnergy":
        ID = 5
    if name == "energyPerHour":
        ID = 6
    if name == "wiFiRSSI":
        ID = 7
    if name == "cellRSSI":
        ID = 8
    if name == "localRSSI":
        ID = 9
    if name == "outputPhase":
        ID = 10
    if name == "dynamicCircuitCurrentP1":
        ID = 11
    if name == "dynamicCircuitCurrentP2":
        ID = 12
    if name == "dynamicCircuitCurrentP3":
        ID = 13
    if name == "latestPulse":
        Domoticz.Log(sValue)
        sValue = str(sValue)
        ID = 14
    if name == "chargerFirmware":
        ID = 15
    if name == "latestFirmware":
        ID = 16
    if name == "voltage":
        ID = 17
    if name == "chargerRAT":
        ID = 18
    if name == "lockCablePermanently":
        ID = 19
    if name == "inCurrentT2":
        ID = 20
    if name == "inCurrentT3":
        ID = 21
    if name == "inCurrentT4":
        ID = 22
    if name == "inCurrentT5":
        ID = 23
    if name == "outputCurrent":
        ID = 24
    if name == "isOnline":
        ID = 25
    if name == "inVoltageT1T2":
        ID = 26
    if name == "inVoltageT1T3":
        ID = 27
    if name == "inVoltageT1T4":
        ID = 28
    if name == "inVoltageT1T5":
        ID = 29
    if name == "inVoltageT2T3":
        ID = 30
    if name == "inVoltageT2T4":
        ID = 31
    if name == "inVoltageT2T5":
        ID = 32
    if name == "inVoltageT3T4":
        ID = 33
    if name == "inVoltageT3T5":
        ID = 34
    if name == "inVoltageT4T5":
        ID = 35
    if name == "ledMode":
        ID = 36
    if name == "cableRating":
        ID = 37
    if name == "dynamicChargerCurrent":
        ID = 38
    if name == "circuitTotalAllocatedPhaseConductorCurrentL1":
        ID = 39
    if name == "circuitTotalAllocatedPhaseConductorCurrentL2":
        ID = 40
    if name == "circuitTotalAllocatedPhaseConductorCurrentL3":
        ID = 41
    if name == "circuitTotalPhaseConductorCurrentL1":
        ID = 42
    if name == "circuitTotalPhaseConductorCurrentL2":
        ID = 43
    if name == "circuitTotalPhaseConductorCurrentL3":
        ID = 44
    if name == "reasonForNoCurrent":
        ID = 45
    if name == "wiFiAPEnabled":
        ID = 46
    if name == "lifetimeEnergy":
        ID = 47
    if name == "offlineMaxCircuitCurrentP1":
        ID = 48
    if name == "offlineMaxCircuitCurrentP2":
        ID = 49
    if name == "offlineMaxCircuitCurrentP3":
        ID = 50
    if name == "errorCode":
        ID = 51
    if name == "fatalErrorCode":
        ID = 52
    if name == "errors":
        ID = 53

    if (ID in Devices):
        if (Devices[ID].nValue != nValue) or (Devices[ID].sValue != sValue):
            Devices[ID].Update(nValue, str(sValue))

    if (ID not in Devices):
        if sValue == "-32768":
            Used = 0
        else:
            Used = 1
        Domoticz.Device(Name=name, Unit=ID, TypeName="Custom", Options={"Custom": "0;"}, Used=Used, Description="ParameterID=\nDesignation=").Create()

"""        if Unit == "bar":
            Domoticz.Device(Name=Name, Unit=ID, TypeName="Pressure", Used=1, Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)+"\nSystem="+str(SystemUnitId)).Create()
        if Unit == "l/m":
            Domoticz.Device(Name=Name, Unit=ID, TypeName="Waterflow", Used=1, Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)+"\nSystem="+str(SystemUnitId)).Create()
        elif Unit == "°C" or ID == 30 and ID !=24:
            Domoticz.Device(Name=Name, Unit=ID, TypeName="Temperature", Used=Used, Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)+"\nSystem="+str(SystemUnitId)).Create()
        elif Unit == "A":
            if ID == 15:
                Domoticz.Device(Name=Name+" 1", Unit=ID, TypeName="Custom", Used=1, Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)+"\nSystem="+str(SystemUnitId)).Create()
            if ID == 16:
                Domoticz.Device(Name=Name+" 2", Unit=ID, TypeName="Custom", Used=1, Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)+"\nSystem="+str(SystemUnitId)).Create()
            if ID == 17:
                Domoticz.Device(Name=Name+" 3", Unit=ID, TypeName="Custom", Used=1, Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)+"\nSystem="+str(SystemUnitId)).Create()
            if ID == 53:
                Domoticz.Device(Name=Name, Unit=ID, TypeName="Current (Single)", Used=1, Description="ParameterID="+str(PID)+"\nSystem="+str(SystemUnitId)).Create()
        elif Name == "compressor starts":
            Domoticz.Device(Name=Name, Unit=ID, TypeName="Custom", Options={"Custom": "0;times"}, Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)).Create()
        elif Name == "blocked":
            if ID == 21:
                Domoticz.Device(Name="compressor "+Name, Unit=ID, TypeName="Custom", Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)).Create()
            if ID == 51:
                Domoticz.Device(Name="addition "+Name, Unit=ID, TypeName="Custom", Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)).Create()
        elif ID == 24:
            Domoticz.Device(Name="compressor "+Name, Unit=ID, TypeName="Temperature", Used=1, Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)).Create()
        elif ID == 41 or ID == 81:
            Domoticz.Device(Name=Name, Unit=ID, TypeName="Custom", Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)+"\nDesignation="+str(Design)).Create()
        elif ID == 61:
            Domoticz.Device(Name="comfort mode "+Name, Unit=ID, TypeName="Custom", Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)).Create()
        elif ID == 62:
            Domoticz.Device(Name="comfort mode "+Name, Unit=ID, TypeName="Custom", Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)).Create()
        elif ID == 63:
            Domoticz.Device(Name="smart price adaption "+Name, Unit=ID, TypeName="Custom", Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)).Create()
        elif ID == 71:
            Domoticz.Device(Name=Name, Unit=ID, TypeName="Text", Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)).Create()
        elif ID == 72 or ID == 73:
            Domoticz.Device(Name=Name, Unit=ID, TypeName="Text", Used=1, Image=(_plugin.ImageID)).Create()
        elif ID == 74:
            Domoticz.Device(Name="software "+Name, Unit=ID, TypeName="Text", Used=1, Image=(_plugin.ImageID)).Create()
        else:
            if Design == "":
                Domoticz.Device(Name=Name, Unit=ID, TypeName="Custom", Options={"Custom": "0;"+Unit}, Used=1, Image=(_plugin.ImageID), Description="ParameterID="+str(PID)).Create()
"""

def CreateFile():
    if not os.path.isfile(dir+'/EaseeCloud.ini'):
        data = {}
        data["Config"] = []
        data["Config"].append({
             "Access": "",
             "Ident": "",
             "Refresh": "",
             "Secret": "",
             "SystemID": "",
             "URL": ""
             })
        with open(dir+'/EaseeCloud.ini', 'w') as outfile:
            json.dump(data, outfile, indent=4)

def CheckFile(Parameter):
    if os.path.isfile(dir+'/EaseeCloud.ini'):
        with open(dir+'/EaseeCloud.ini') as jsonfile:
            data = json.load(jsonfile)
            data = data["Config"][0][Parameter]
            if data == "":
                _plugin.AllSettings = False
            else:
                return data

def WriteFile(Parameter,text):
    CreateFile()
    with open(dir+'/EaseeCloud.ini') as jsonfile:
        data = json.load(jsonfile)
    data["Config"][0][Parameter] = text
    with open(dir+'/EaseeCloud.ini', 'w') as outfile:
        json.dump(data, outfile, indent=4)

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
        if _plugin.GetData.Connected():
            _plugin.GetData.Disconnect()


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
