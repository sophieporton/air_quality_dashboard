# %%
#import required packages

import pandas as pd
import streamlit as st 
import numpy as np
import requests
from datetime import date, datetime, timedelta
import sqlite_utils
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import functions
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from PIL import Image



# %%
#set up streamlit page 

st.set_page_config(layout = "wide")
st.title("Air quality dashboard")
st.text('This is a dashboard displaying air quality data in Tower Hamlets. Data is provided by the Environmental Research Group (ERG) part of the School of Biomedical Science at King’s College London ')

st_autorefresh(interval=10*60*1000, key="api_update")

db = sqlite_utils.Database("air-sensors.db")


#%%
image = functions.get_image("logo.png") # path of the file
st.sidebar.image(image, use_column_width=True)
st.sidebar.header("Filter Your Data")

pollutant= st.sidebar.selectbox('Choose a pollutant',options= 'NO2')

if pollutant == 'NO2':
    site= st.sidebar.multiselect('Choose a site', options= ('Mile End Road', 'Blackwall' ))

#%%

functions.add_sqlite_table(db=sqlite_utils.Database("air-sensors.db"),tablename='NO2_hourly',pk=('@MeasurementDateGMT', '@Site'),
    not_null={"@MeasurementDateGMT", "@Value", "@Site"},
    column_order=("@MeasurementDateGMT", "@Value", "@Site"))

functions.add_sqlite_table(db=sqlite_utils.Database("air-sensors.db"),tablename='NO2_annually',pk=('@Year', '@SiteName','@ObjectiveName'),
    not_null={"@Year", "@Value", "@SiteName"},
    column_order=("@Year", "@Value", "@SiteName"))

#%%

# %%

# EXTRACT THE SITES IN TOWER HAMLETS
#api is link between between us and database 
req = requests.get("https://api.erg.ic.ac.uk/AirQuality/Information/MonitoringSiteSpecies/GroupName=towerhamlets/Json") #requests gets the info from the api 
js = req.json() #json is like a python dictionary 
sites = js['Sites']['Site'] #turns dictionary into list 

# %%

EndDate = date.today() + timedelta(days = 1)
EndWeekDate = EndDate
StartWeekDate = EndDate - timedelta(weeks = 2)
StartDate = StartWeekDate - timedelta(days = 1)

while StartWeekDate > StartDate :
        for el in sites:
            def convert(list):
                list['@Value'] = float(list['@Value'])
                list['@Site'] = el['@SiteName']
                return list
            url = f'https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/SiteCode={el["@SiteCode"]}/SpeciesCode=NO2/StartDate={StartWeekDate.strftime("%d %b %Y")}/EndDate={EndWeekDate.strftime("%d %b %Y")}/Json'
            print(url)
            req = requests.get(url, headers={'Connection':'close'}) #closes connection to the api
            print(req)
            j = req.json()
            # CLEAN SITES WITH NO DATA OR ZERO VALUE OR NOT NO2 (ONLY MEASURE AVAILABLE AT ALL SITES)
            filtered = [a for a in j['RawAQData']['Data'] if a['@Value'] != '' and a['@Value'] != '0' ] #removes zero and missing values 
            if len(filtered) != 0:
                filtered = map(convert, filtered)
                filteredList = list(filtered)
                db['NO2_hourly'].upsert_all(filteredList,pk=('@MeasurementDateGMT', '@Site')) #combo of update and insert, updates record if it already exists if not creates it 
        EndWeekDate = StartWeekDate
        StartWeekDate = EndWeekDate - timedelta(weeks = 2)

# %%
years=list(range(1994,2024))

for year in years:    
    url = f'https://api.erg.ic.ac.uk/AirQuality/Annual/MonitoringObjective/GroupName=towerhamlets/Year={year}/Json'
    print(url)
    req = requests.get(url, headers={'Connection':'close'}) #closes connection to the api
    print(req)
    j = req.json()
    l=j['SiteObjectives']['Site']
    rows=[]
    for data in l:
        data_row=data['Objective']
        n=data['@SiteName']

        for row in data_row:
            row['@SiteName']= n
            rows.append(row)
    
    filtered = [a for a in rows if a['@SpeciesCode']=='NO2']
    db['NO2_annually'].upsert_all(filtered,pk=('@Year', '@SiteName', '@ObjectiveName'))
