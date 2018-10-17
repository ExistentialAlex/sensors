#!/usr/bin/python

"""LearnSensorthingsClient.

Author: Karthik Chepudira
Date Created:** 4/24/2018
Python version:** 3.6

This is a client library for communicating with a sensorthings api compliant server as per
https://github.com/opengeospatial/sensorthings

"""
import json
import uuid
from datetime import datetime, timedelta
import re

import requests
import pandas as pd


# from IPython.core.debugger import set_trace
# from pdb import set_trace

DEFAULT_ENCODING = 'windows-1252'

class LearnSTAClient:

    def __init__(self, baseurl, authurl, authID, authkey,VERIFY_SSL=False):
        self.baseurl = baseurl
        self.authurl = authurl
        self.authID = authID
        self.authkey = authkey
        self.authtoken = None
        self.authtokents = None
        self.VERIFY_SSL = VERIFY_SSL
        
    def jwt_authenticate(self):
        #traceback.print_stack()
        JWT_ID=self.authID
        JWT_KEY=self.authkey
        URL_AUTH =self.authurl
        VERIFY_SSL=self.VERIFY_SSL
        AUTH_TTL=timedelta(minutes=5)
        AUTH_TEMPLATE = '''{{"id":"{id}","key":"{key}"}}'''
        token = (self.authtoken, self.authtokents)
        session = requests.session()
        
        new_token = token
        auth_required = False
        
        # Figure out if authentication is required, that is: (1) if we have never authenticated (token_timestamp is None);
        #   or (2) token_timestamp is later than or equal to the current time + AUTH_TTL
        token_timestamp = token[1]
        if token_timestamp is None:
            print ("Transmitter: Auth token is null, authenticating ...")
            auth_required = True
        else:
            token_expired_after = token_timestamp + AUTH_TTL
            if datetime.datetime.utcnow() >= token_expired_after:
                print ("Transmitter: Auth token expired, re-authenticating ...")
                auth_required = True

        if auth_required:
            json = AUTH_TEMPLATE.format(id=JWT_ID, key=JWT_KEY)
            headers = {'Content-Type': 'application/json'}
            try:
                r = session.post(URL_AUTH, headers=headers, data=json, verify=VERIFY_SSL)
            except ConnectionError as e:
                print ("Unable to authenticate to {0} due to error: {1}".format(URL_AUTH, str(e)))
                #raise AuthenticationException("Unable to authenticate to {0} due to error: {1}".format(URL_AUTH, str(e)))
            print (("Transmitter: Auth status code was {0}".format(r.status_code)))
            if r.status_code != 200:
                print ("Authentication failed with status code {0}".format(str(r.status_code)))
                #raise AuthenticationException("Authentication failed with status code {0}".format(str(r.status_code)))
            else:
                new_token = (r.json()["token"], datetime.utcnow())

        return new_token
         
    def createlocation(self,name,description,latitude,longitude):
        geometry= {}
        geometry['type']= "Point"
        geometry['coordinates']=[float(longitude),float(latitude)]
        location = {}
        location['type']="Feature"
        location['geometry']=geometry
        stalocation={}
        stalocation['name']=name
        stalocation['description']=description
        stalocation['encodingType']="application/vnd.geo+json"
        stalocation['location']=location
        return stalocation

    ## Create Thing
    def createThing(self,locationid,name,description,networkid,deploymenttime):
        location = {}
        location['@iot.id']=locationid.replace("'", "")
        properties={}
        properties['network_id']=networkid
        properties['deployment_time']=deploymenttime
        stathing={}
        stathing['Locations']=[location]
        stathing['name']=name
        stathing['description']=description.replace('"', '')
        stathing['properties']=properties
        print (stathing)
        return stathing

    ## Create FeaturesOfInterest
    def createFeaturesOfInterest(self,name,description,latitude,longitude):
        geometry= {}
        geometry['type']= "Point"
        geometry['coordinates']=[float(longitude),float(latitude)]
        location = {}
        location['type']="Feature"
        location['geometry']=geometry
        stafeature={}
        stafeature['name']=name
        stafeature['description']=description
        stafeature['encodingType']="application/vnd.geo+json"
        stafeature['feature']=location
        #print (stafeature)
        return stafeature

    ## Create Sensor
    def createSensor(self,name,description,metadata):
        stasensor={}
        stasensor['name']=name
        stasensor['description']=description
        stasensor['encodingType']="application/pdf"
        stasensor['metadata']=metadata
        return stasensor

    ## Create DataStream
    def createDatastream(self,thingid,sensorid,observedpropertyid,name,description,
                         measurementunit,measurementsymbol,measurementdefinition
                         ,observationtype):

        thing = {}
        thing["@iot.id"]=thingid.replace("'", "")
        sensor = {}
        sensor["@iot.id"]=sensorid.replace("'", "")
        obproperty = {}
        obproperty["@iot.id"]=observedpropertyid.replace("'", "")
        unitOfMeasurement={}
        unitOfMeasurement["name"]=measurementunit
        unitOfMeasurement["symbol"]=measurementsymbol
        unitOfMeasurement["definition"]=measurementdefinition
        stadatastream={}
        stadatastream["Thing"]=thing
        stadatastream["Sensor"]=sensor
        stadatastream["ObservedProperty"]=obproperty
        stadatastream["name"]=name
        stadatastream["description"]=description
        stadatastream["unitOfMeasurement"]=unitOfMeasurement
        stadatastream["observationType"]=observationtype
        print (stadatastream)
        return stadatastream

    def create_unit_of_measurement(self, meas_unit, meas_symbol, meas_def):
        unit_of_meas = {}
        unit_of_meas["name"] = meas_unit
        unit_of_meas["symbol"] = meas_symbol
        if meas_unit == 'degree Celsius':
            # Hack to get around Pandas's seeming inability to properly decode the degree symbol from a windows-1252-
            # encoded file
            unit_of_meas["symbol"] = '\u00B0C'
        unit_of_meas["definition"] = meas_def
        return unit_of_meas

    def create_multi_datastream(self, thing_id, sensor_id, obs_prop_ids,
                                name, description,
                                obs_data_types,
                                units_of_meas):
        thing = {}
        thing["@iot.id"] = thing_id.replace("'", "")
        sensor = {}
        sensor["@iot.id"] = sensor_id.replace("'", "")

        multi_ds = {}
        multi_ds["Thing"] = thing
        multi_ds["Sensor"] = sensor
        op = []
        for o in obs_prop_ids:
            op.append({"@iot.id": o})
        multi_ds["ObservedProperties"] = op
        multi_ds["name"] = name
        multi_ds["description"] = description
        multi_ds["observationType"] = 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_ComplexObservation'
        multi_ds["multiObservationDataTypes"] = obs_data_types
        multi_ds["unitOfMeasurements"] = units_of_meas
        # print(multi_ds)
        return multi_ds

    def createsensor(self,name,description,encodingtype,metadata):
        session = requests.session()
        sensor={}
        sensor['name']=name
        sensor['encodingType']=encodingtype
        sensor['description']=description
        sensor['metadata']=metadata
        sensorjson=json.dumps(sensor, ensure_ascii=False).encode('utf8')
        jwt_token = self.jwt_authenticate()
        print (sensorjson)
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}
        r = session.post(self.baseurl+"/Sensors", headers=headers, data=sensorjson, verify=self.VERIFY_SSL)
        print (r)
    
    def createobservedproperty(self,name,definition,description):
        session = requests.session()
        obsprop={}
        obsprop['name']=name
        obsprop['definition']=definition
        obsprop['description']=description
        obspropjson=json.dumps(obsprop, ensure_ascii=False).encode('utf8')
        jwt_token = self.jwt_authenticate()
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}
        r = session.post(self.baseurl+"/ObservedProperties", headers=headers, data=obspropjson, verify=self.VERIFY_SSL)
        print (r)
    
    def createlocationrec(self,name,description,latitude,longitude):
        session = requests.session()
        obsloc=self.createlocation(name,description,latitude,longitude)
        obslocjson=json.dumps(obsloc, ensure_ascii=False).encode('utf8')
        jwt_token = self.jwt_authenticate()
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}
        r = session.post(self.baseurl+"/Locations", headers=headers, data=obslocjson, verify=self.VERIFY_SSL)
        print (r)
    
    def createsensorthing(self,row):
        session = requests.session()
        try:
            # Get Token
            jwt_token = self.jwt_authenticate()
            print (jwt_token)
            headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}

            # Create Thing
            print ("Creating Things")
            thingjson =json.dumps(self.createThing(row['locationid'],row['thname'],row['thdesc'],row['thnetid'],
                                                   row['thdeploytime']), ensure_ascii=False).encode('utf8')
            r = session.post(self.baseurl+"/Things", headers=headers, data=thingjson, verify=self.VERIFY_SSL)
            print(r.status_code)
            print(r.text)
            print (" Printing thing headers ")
            print (r.headers)
            thstr=r.headers["Location"]
            thingid=thstr[thstr.find("(")+1:thstr.find(")")]
            #print (thstr)
            #print (thingid)
            return thingid
        except:
            raise
            print ("error")
            return 'Error'
        
    def createdatastream(self,row):
        session = requests.session()
        try:
            # Get Token
            jwt_token = self.jwt_authenticate()
            print (jwt_token)
            headers = {'Content-Type': 'application/json; charset=utf-8','Authorization': "Bearer {token}".format(token=jwt_token[0])}

            # Create Datastream
            print ("Creating Datastreams")
            symbol = row['dsmsymbol']
            if row['dsmunit'] == 'degree Celsius':
                # Hack to get around Pandas's seeming inability to properly decode the degree symbol from a windows-1252-
                # encoded file
                symbol = '\u00B0C'
            dsjson =json.dumps(self.createDatastream(row['stathingid'],row['dssensorid'],row['dsobspropertyid'],row['dsname'],
                                                     row['dsdesc'],row['dsmunit'], symbol,
                                                     row['dsmdefinition'],row['dsobstype']), ensure_ascii=False).encode('utf8')
            r = session.post(self.baseurl+"/Datastreams", headers=headers, data=dsjson, verify=self.VERIFY_SSL)
            print(r.status_code)
            print(r.text)
            dsstr=r.headers["Location"]
            dsstrid=dsstr[dsstr.find("(")+1:dsstr.find(")")]
            print (dsstr,dsstrid)
            return dsstrid

        except:
            return 'Error'

    def do_create_multidatastream(self, row, df_multidatastreams_datastreams):
        # TODO: Update to actually create multidatastreams instead of datastreams
        session = requests.session()
        try:
            # Get Token
            jwt_token = self.jwt_authenticate()
            print(jwt_token)
            headers = {'Content-Type': 'application/json; charset=utf-8',
                       'Authorization': "Bearer {token}".format(token=jwt_token[0])}

            obs_props = []
            obs_data_types = []
            units_of_meas = []
            # Select component Datastreams
            comp = df_multidatastreams_datastreams[df_multidatastreams_datastreams['multidatastreamnum'] == row['multidatastreamnum']]
            for idx, c in comp.iterrows():
                # Collect ObservedProperty ID
                obs_props.append(c['dsobspropertyid'])
                # Collect ObservationType
                obs_data_types.append(c['dsobstype'])
                # Create unit of measurement
                units_of_meas.append(self.create_unit_of_measurement(c['dsmunit'], c['dsmsymbol'], c['dsmdefinition']))

            # Create MultiDatastream
            mdsjson = json.dumps(
                self.create_multi_datastream(row['stathingid'], row['mdssensorid'], obs_props,
                                             row['mdsname'], row['mdsdesc'],
                                             obs_data_types, units_of_meas), ensure_ascii=False).encode('utf8')
            url = self.baseurl + "/MultiDatastreams"
            print("POST: {0}: {1}".format(url, mdsjson))
            r = session.post(url, headers=headers, data=mdsjson, verify=self.VERIFY_SSL)
            print(r.status_code)
            print(r.text)
            mdsstr = r.headers["Location"]
            mdsstrid = mdsstr[mdsstr.find("(") + 1:mdsstr.find(")")]
            print(mdsstr, mdsstrid)
            return mdsstrid

        except:
            return 'Error'

    def createdatastreamQAQC(self,row):
        session = requests.session()
        if row['sensorname'] not in ('ozone', 'particulate_matter'):
            return ''
        jwt_token = self.jwt_authenticate()
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}

        # Create Datastream
        print ("Creating Datastreams QAQC")
        symbol = row['dsmsymbol']
        if row['dsmunit'] == 'degree Celsius':
            # Hack to get around Pandas's seeming inability to properly decode the degree symbol from a windows-1252-
            # encoded file
            symbol = '\u00B0C'
        dsjson =json.dumps(self.createDatastream(row['stathingid'],row['dssensorid'],row['dsobspropertyid'],row['QAQC_dsname'],
                                                 row['QAQC_dsdesc'],row['dsmunit'],symbol,
                                                 row['dsmdefinition'],row['dsobstype']), ensure_ascii=False).encode('utf8')
        url = self.baseurl+"/Datastreams"
        print("POST to {0}; Content: {1}".format(url, dsjson))
        r = session.post(url, headers=headers, data=dsjson, verify=self.VERIFY_SSL)
        print(r.status_code)
        print(r.text)
        dsstr=r.headers["Location"]
        dsstrid=dsstr[dsstr.find("(")+1:dsstr.find(")")]
        print (dsstr,dsstrid)
        return dsstrid

    
    def createdatastreamAQI(self,row):
        session = requests.session()
        if row['sensorname'] not in ('ozone', 'particulate_matter'):
            return ''
        jwt_token = self.jwt_authenticate()
        headers = {'Content-Type': 'application/json','Authorization': "Bearer {token}".format(token=jwt_token[0])}

        # Create Datastream
        print ("Creating Datastreams AQI")
        dsjson =json.dumps(self.createDatastream(row['stathingid'],row['dssensorid'],row['AQI_dsobspropertyid'],row['AQI_dsname'],
                                                 row['AQI_dsdesc'],row['AQI_dsmunit'],None,
                                                 row['AQI_dsmdefinition'],row['AQI_dsobstype']), ensure_ascii=False).encode('utf8')
        url = self.baseurl+"/Datastreams"
        print("POST to {0}; Content: {1}".format(url, dsjson))
        r = session.post(url, headers=headers, data=dsjson, verify=self.VERIFY_SSL)
        print(r.status_code)
        print(r.text)
        dsstr=r.headers["Location"]
        dsstrid=dsstr[dsstr.find("(")+1:dsstr.find(")")]
        print (dsstr,dsstrid)
        return dsstrid

    def do_patch_thing_name_and_desc(self, row):
        session = requests.session()
        headers = self.do_jwt_auth()
        things_json = json.dumps({"name": row['thname'].strip("'"), "description": row['thdesc'].strip("'")})
        url = self.baseurl+"/Things('{0}')".format(row['stathingid'].strip("'"))
        r = session.patch(url, headers=headers, data=things_json, verify=self.VERIFY_SSL)
        if r.status_code != 200 and r.status_code != 204:
            raise Exception("PATCH {0} failed, response was {1}.  Body was: {2}".format(url, r.status_code, things_json))

    def do_jwt_auth(self):
        jwt_token = self.jwt_authenticate()
        headers = {'Content-Type': 'application/json', 'Authorization': "Bearer {token}".format(token=jwt_token[0])}
        return headers

    def patch_thing_name_and_desc(self, outputthingsfilepath):
        dfthings = pd.read_csv(outputthingsfilepath)
        dfthings.apply(self.do_patch_thing_name_and_desc, axis=1)

    def Getuuid(self,row):
        return uuid.uuid4()
        
    def createthings(self,inputthingsfilepath,outputthingsfilepath):
        dfthings=pd.read_csv(inputthingsfilepath)
        dfthings['stathingid'] =dfthings.apply(self.createsensorthing, axis=1)
        dfthings['jwt_id'] = dfthings.apply(self.Getuuid, axis=1)
        dfthings['jwt_key'] = dfthings.apply(self.Getuuid, axis=1)
#         dfthings['stalocationid'] = dfthings.apply(self.Getuuid, axis=1)
        dfthings.to_csv(outputthingsfilepath,index=False)
        
    def createdatastreams(self,inputdatastreamsfilepath,outputdatastreamsfilepath,inputthingsfilepath):
        dfthings=pd.read_csv(inputthingsfilepath)
        dfdatastreams=pd.read_csv(inputdatastreamsfilepath, encoding=DEFAULT_ENCODING)
        dfdatastreams=dfdatastreams.merge(dfthings,on='devicenum', how='left')
        dfdatastreams['stadatastreamid'] = dfdatastreams.apply(self.createdatastream, axis=1)
        dfdatastreams['QAQC_stadatastreamid'] = dfdatastreams.apply(self.createdatastreamQAQC, axis=1)
        dfdatastreams['AQI_stadatastreamid'] = dfdatastreams.apply(self.createdatastreamAQI, axis=1)
        dfdatastreams.to_csv(outputdatastreamsfilepath, index=False, encoding=DEFAULT_ENCODING)

    def create_multidatastreams(self, input_mds_filepath, output_mds_filepath,
                                input_mds_datastreams_filepath,
                                input_things_filepath):
        df_things = pd.read_csv(input_things_filepath, encoding=DEFAULT_ENCODING)
        df_multidatastreams = pd.read_csv(input_mds_filepath, encoding=DEFAULT_ENCODING)
        df_multidatastreams_datastreams = pd.read_csv(input_mds_datastreams_filepath, encoding=DEFAULT_ENCODING)
        df_multidatastreams = df_multidatastreams.merge(df_things, on='devicenum', how='left')
        df_multidatastreams['stamultidatastreamid'] = df_multidatastreams.apply(self.do_create_multidatastream, axis=1,
                                                                                args=(df_multidatastreams_datastreams,))
        df_multidatastreams.to_csv(output_mds_filepath, index=False, encoding=DEFAULT_ENCODING)

    # custom function to add the QAQC, AQI datastreams.
    def patchdatastreams(self, outputdatastreamsfilepath):
        dfdatastreams=pd.read_csv(outputdatastreamsfilepath, encoding=DEFAULT_ENCODING)
        dfdatastreams['QAQC_stadatastreamid'] = dfdatastreams.apply(self.createdatastreamQAQC, axis=1)
        dfdatastreams['AQI_stadatastreamid'] = dfdatastreams.apply(self.createdatastreamAQI, axis=1)
        dfdatastreams.to_csv(outputdatastreamsfilepath, index=False, encoding=DEFAULT_ENCODING)
    
    def createagentssql(self, inputthingsfilepath, agentsfilepath):
        dfthings=pd.read_csv(inputthingsfilepath)
        filepath = agentsfilepath + "/agents-append-" + datetime.now().isoformat().replace(':','_') + ".sql"
        with open(filepath, 'w') as cfile:
            for idx, row in dfthings.iterrows():
                cfile.write("--{0}\n".format(row['thname']))
                cfile.write("insert into agents(id, key) values ('{jwt_id}', '{jwt_key}');\n".format(jwt_id=row['jwt_id'],
                                                                                                     jwt_key=row['jwt_key']))
                
    def createthingsyml_orig(self,inputthingsfilepath,inputdatastreamsfilepath,ymlfilepath):
        dfthings=pd.read_csv(inputthingsfilepath)
        dfdatastreams=pd.read_csv(inputdatastreamsfilepath, encoding=DEFAULT_ENCODING)
        dfsta=dfdatastreams.merge(dfthings,on='devicenum', how='left')
        devices = list(dfsta['devicenum'].unique())
        for i, devicenum in enumerate(devices):
            filepath = ymlfilepath+"/"+str(devicenum)+".yml"
            with open(filepath, 'w') as cfile:
                #stathingid=str(dfdevice[dfdevice['devicenum']==devnum].iloc[0]['stathingid'])
                stathingid=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['stathingid'])
                locationid=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['locationid'])
                thing_name = str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['thname'])
                jwt_key=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['jwt_key'])
                jwt_id=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['jwt_id'])
                stadatastreamslist=list(dfdatastreams[dfdatastreams['devicenum']==devicenum]['stadatastreamid'].unique())
                stasensortypeslist=list(dfdatastreams[dfdatastreams['devicenum']==devicenum]['sensortype'].unique())
                cfile.write("# Thing name: {0}\n".format(thing_name))
                cfile.write("logging:"+'\n')
                cfile.write("  logger_path: /var/log/sensor.log"+'\n')
                cfile.write("  level_file: WARNING"+'\n')
                cfile.write("  level_console: WARNING"+'\n')
                cfile.write("spooler:"+'\n')
                cfile.write("  db_path: /var/spool/sensor.sqlite"+'\n')
                cfile.write("thing:"+'\n')
                cfile.write("  id: "+stathingid.replace("'", "")+'\n')
                cfile.write("  location_id: "+locationid.replace("'", "")+'\n')
                cfile.write("sensors:"+'\n')
                # loop through sensortypes
                for stype in stasensortypeslist:
                    stasensorlist=list(dfdatastreams[(dfdatastreams['devicenum']==devicenum) & (dfdatastreams['sensortype']==stype)]['sensorname'].unique())
                    cfile.write("  - type: "+stype+'\n')
                    cfile.write("    observed_properties:"+'\n')
                    for sname in stasensorlist:
                     # loop through observed properties
                        cfile.write("      - name: "+sname+'\n')
                        stadsid=list(dfdatastreams[(dfdatastreams['devicenum']==devicenum) & (dfdatastreams['sensortype']==stype) & (dfdatastreams['sensorname']==sname)]['stadatastreamid'].unique())
                        cfile.write("        datastream_id: "+stadsid[0].replace("'", "")+'\n')
                    if stype == 'mq131' and dfthings['large_thing'].iloc[i]:
                        # Configure non-default ADC for large sensor boxes
                        cfile.write("    properties:\n")
                        cfile.write("      - Ro: 2.501\n")
                        cfile.write("      - adc: ads1015\n")
                cfile.write("transports:"+'\n')
                cfile.write("  - type: https"+'\n')
                cfile.write("    properties:"+'\n')
                cfile.write("      auth_url: https://test1-sta-api.learnlafayette.com/SensorThingsService/auth/login"+'\n')
                cfile.write("      url: https://test1-sta-api.learnlafayette.com/SensorThingsService/v1.0/"+'\n')
                cfile.write("      jwt_id: "+jwt_id+'\n')
                cfile.write("      jwt_key: "+jwt_key+'\n')
                cfile.write("      jwt_token_ttl_minutes: 15"+'\n')
                cfile.write("      transmit_interval_seconds: 15"+'\n')
                cfile.write("      verify_ssl: true"+'\n')


    def createthings_yml(self, input_things_filepath, input_datastreams_filepath,
                         input_mds_filepath, input_msd_datastreams_filepath,
                         yml_filepath):
        dfthings = pd.read_csv(input_things_filepath, encoding=DEFAULT_ENCODING)
        dfdatastreams = pd.read_csv(input_datastreams_filepath, encoding=DEFAULT_ENCODING)
        df_ds = dfdatastreams.merge(dfthings,on='devicenum', how='left')

        dfmultidatastreams = pd.read_csv(input_mds_filepath, encoding=DEFAULT_ENCODING)
        dfmultidatastreams_datastreams = pd.read_csv(input_msd_datastreams_filepath, encoding=DEFAULT_ENCODING)
        df_mds = dfmultidatastreams_datastreams.merge(dfmultidatastreams, on=['devicenum', 'multidatastreamnum'], how='left')

        devices = list(df_ds['devicenum'].unique())
        for i, devicenum in enumerate(devices):
            filepath = yml_filepath+"/"+str(devicenum)+".yml"
            with open(filepath, 'w') as cfile:
                stathingid=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['stathingid'])
                locationid=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['locationid'])
                thing_name = str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['thname'])
                jwt_key=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['jwt_key'])
                jwt_id=str(dfthings[dfthings['devicenum']==devicenum].iloc[0]['jwt_id'])
                stasensortypeslist=list(dfdatastreams[dfdatastreams['devicenum']==devicenum]['sensortype'].unique())
                cfile.write("# Thing name: {0}\n".format(thing_name))
                cfile.write("logging:"+'\n')
                cfile.write("  logger_path: /var/log/sensor.log"+'\n')
                cfile.write("  level_file: WARNING"+'\n')
                cfile.write("  level_console: WARNING"+'\n')
                cfile.write("spooler:"+'\n')
                cfile.write("  db_path: /var/spool/sensor.sqlite"+'\n')
                cfile.write("thing:"+'\n')
                cfile.write("  id: "+stathingid.replace("'", "")+'\n')
                cfile.write("  location_id: "+locationid.replace("'", "")+'\n')
                cfile.write("sensors:"+'\n')
                # Handle regular Datastreams
                for stype in stasensortypeslist:
                    stasensorlist=list(dfdatastreams[(dfdatastreams['devicenum']==devicenum) & (dfdatastreams['sensortype']==stype)]['sensorname'].unique())
                    cfile.write("  - type: "+stype+'\n')
                    cfile.write("    observed_properties:"+'\n')
                    for sname in stasensorlist:
                     # loop through observed properties
                        cfile.write("      - name: "+sname+'\n')
                        stadsid=list(dfdatastreams[(dfdatastreams['devicenum']==devicenum) & (dfdatastreams['sensortype']==stype) & (dfdatastreams['sensorname']==sname)]['stadatastreamid'].unique())
                        cfile.write("        datastream_id: "+stadsid[0].replace("'", "")+'\n')
                    if stype == 'mq131':
                        cfile.write("    properties:\n")
                        cfile.write("      - Ro: 2.501\n")
                        if dfthings['large_thing'].iloc[i]:
                            # Configure non-default ADC for large sensor boxes
                            cfile.write("      - adc: ads1015\n")

                # Handle MultiDatastreams
                mds = df_mds[df_mds['devicenum'] == devicenum]
                mds_num_list = list(mds['multidatastreamnum'].unique())
                for m_num in mds_num_list:
                    m = mds[mds['multidatastreamnum'] == m_num]
                    cfile.write("  - type: " + str(m['sensortype'].iloc[0]) + '\n')
                    mds_id = m['stamultidatastreamid'].unique()[0].strip("'")
                    cfile.write("    multidatastream_id: " + mds_id + '\n')
                    cfile.write("    observed_properties:" + '\n')
                    # import pdb;
                    # pdb.set_trace()
                    for o in m['dsobsproperty'].unique():
                        cfile.write("      - " + o + "\n");

                cfile.write("transports:"+'\n')
                cfile.write("  - type: https"+'\n')
                cfile.write("    properties:"+'\n')
                cfile.write("      auth_url: https://test1-sta-api.learnlafayette.com/SensorThingsService/auth/login"+'\n')
                cfile.write("      url: https://test1-sta-api.learnlafayette.com/SensorThingsService/v1.0/"+'\n')
                cfile.write("      jwt_id: "+jwt_id+'\n')
                cfile.write("      jwt_key: "+jwt_key+'\n')
                cfile.write("      jwt_token_ttl_minutes: 15"+'\n')
                cfile.write("      transmit_interval_seconds: 15"+'\n')
                cfile.write("      verify_ssl: true"+'\n')
