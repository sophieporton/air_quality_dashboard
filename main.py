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
st.write('''This is a dashboard displaying air quality data in Tower Hamlets.
 This information has been obtained from the Environmental Research Group of Kings College
London (http://www.erg.kcl.ac.uk), using data from the London Air Quality Network
(http://www.londonair.org.uk). This information is licensed under the terms of the Open
Government Licence. 
  ''')

st_autorefresh(interval=30*60*1000, key="api_update")


functions.add_sqlite_table(db=sqlite_utils.Database("air-sensors.db"),tablename='NO2_hourly',pk=('@MeasurementDateGMT', '@Site'),
    not_null={"@MeasurementDateGMT", "@Value", "@Site"},
    column_order=("@MeasurementDateGMT", "@Value", "@Site"))

functions.add_sqlite_table(db=sqlite_utils.Database("air-sensors.db"),tablename='NO2_annually',pk=('@Year', '@SiteName','@ObjectiveName'),
    not_null={"@Year", "@Value", "@SiteName"},
    column_order=("@Year", "@Value", "@SiteName"))

db = sqlite_utils.Database("air-sensors.db")

#%%

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
#years=list(range(1994,2024))

#for year in years:    
#   url = f'https://api.erg.ic.ac.uk/AirQuality/Annual/MonitoringObjective/GroupName=towerhamlets/Year={year}/Json'
#   print(url)
#    req = requests.get(url, headers={'Connection':'close'}) #closes connection to the api
#    print(req)
#    j = req.json()
#    l=j['SiteObjectives']['Site']
#    rows=[]
#    for data in l:
#        data_row=data['Objective']
#        n=data['@SiteName']

#        for row in data_row:
#            row['@SiteName']= n
#            rows.append(row)
    
#    filtered = [a for a in rows if a['@SpeciesCode']=='NO2']
#    db['NO2_annually'].upsert_all(filtered,pk=('@Year', '@SiteName', '@ObjectiveName'))


#%%
image = functions.get_image("logo.png") # path of the file
st.sidebar.image(image, use_column_width=True)
st.sidebar.header("Filter Your Data")

pollutant= st.sidebar.selectbox('Choose a pollutant', options= ('NO2', 'Ozone'))
#site= st.sidebar.multiselect('Choose a site', options= ('Mile End Road', 'Blackwall' ))



if pollutant =='NO2':
     st.subheader('Nitrogen dioxide (NO2)')
     st.write('''Nitrogen dioxide (NO2) is a gas that is mainly produced during the combustion of fossil fuels, along with nitric oxide (NO).
     Short-term exposure to concentrations of NO2 can cause inflammation of the airways and increase susceptibility to respiratory infections and to allergens. 
     NO2 can also exacerbate the symptoms of those already suffering from lung or heart conditions, and cause changes to the environment such as soil chemistry.''')
     
     st.write('''The Air Quality Standards Regulations 2010 require that the annual mean concentration of NO2 must not exceed 40 µg/m3 and that there should be no more than 18
     exceedances of the hourly mean limit value (concentrations above 200 µg/m3) in a single year.''')
     
     tab1, tab2, tab3 = st.tabs(["Hourly", "Annually", "Capture Rate"])
     with tab1:
        st.write('''Live data displaying hourly NO2 measurements in the past 2 weeks for the currently active sensors in Tower Hamlets.
        ''')
     

        fig = px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command="""SELECT * FROM NO2_hourly; """), x= '@MeasurementDateGMT', y= '@Value', color='@Site',width=1200, height= 700)

        fig.update_layout(title='',
                        xaxis_title='Measurement Date',
                        yaxis_title='NO<sub>2</sub> Concentration (µg/m<sup>3</sup>)',
                        #legend=dict(orientation="h", entrywidth=250,
                        #yanchor="bottom", y=1.02, xanchor="right", x=1),
                        legend_title_text= '', font=dict(size= 17)
                        )

        fig.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18),)
        fig.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18), range = [1,75])

        #print("plotly express hovertemplate:", fig.data[0].hovertemplate)

        fig.update_traces(hovertemplate='<b>Measurement time (GMT) = </b>%{x}<br><b>Value = </b>%{y}<extra></extra>')

        fig.update_layout(hoverlabel = dict(
            font_size = 16))

        fig.add_hline(y=40,line_dash='dot')

        #fig.add_annotation(x=20,y=40, text='Maximum target concentration', showarrow=False,yshift=10)

        fig.show()

        st.plotly_chart(fig, theme=None)    
     

     with tab2:
        #st.write('''Live data displaying hourly NO2 measurements in the past 2 weeks for the currently active sensors in Tower Hamlets.''')
        fig2=px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command=""" SELECT
        *
        FROM
        NO2_annually
        WHERE
        [@ObjectiveName] = '40 ug/m3 as an annual mean'
                                                                                    """),
                        x='@Year', y='@Value', color='@SiteName', width=1200, height=700)

        fig2.update_layout(title='Line plot showing hourly NO2 measurements for the past 2 weeks for the currently active NO2 sensors in Tower Hamlets',
                            xaxis_title='Year',
                            yaxis_title='NO<sub>2</sub> Concentration (µg/m<sup>3</sup>)'
                            ,
                            #legend=dict(orientation="h",
                            #           entrywidth=250,
                            #yanchor="bottom", y=1.02, xanchor="right", x=1),
                            legend_title_text= '', font=dict(size= 17)
                            )

        fig2.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
        fig2.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))
        print("plotly express hovertemplate:", fig2.data[0].hovertemplate)
        fig2.update_traces(hovertemplate='<b>Year </b>%{x}<br><b>Average value = </b>%{y}<extra></extra>')
        fig2.update_layout(hoverlabel = dict(
                font_size = 16))

        fig2.add_hline(y=40,line_dash='dot')

            #fig.add_annotation(x=20,y=40, text='Maximum target concentration', showarrow=False,yshift=10)

        fig2.show()

        st.plotly_chart(fig2,theme=None)
    
     with tab3:
        fig4=px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command=""" SELECT
        *
        FROM
        NO2_annually
        WHERE
        [@ObjectiveName] = 'Capture Rate (%)'
        AND
        [@Year]<2023
                                                                                    """),
                        x='@Year', y='@Value', color='@SiteName', width=1200, height=700)

        fig4.update_layout(title='',
                            xaxis_title='Year',
                            yaxis_title='Capture Rate (%)',
                            #legend=dict(orientation="h", entrywidth=250,
                            #yanchor="bottom", y=1.02, xanchor="right", x=1),
                            legend_title_text= '', font=dict(size= 17)
                            )
        fig4.layout.legend.tracegroupgap = 10
        fig4.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
        fig4.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))

        print("plotly express hovertemplate:", fig4.data[0].hovertemplate)

        fig4.update_traces(hovertemplate='<b>Year </b>%{x}<br><b>Value = </b>%{y}<extra></extra>')

        fig4.update_layout(hoverlabel = dict(
                font_size = 16))

        fig4.add_hline(y=18,line_dash='dot')

        #fig.add_annotation(x=20,y=40, text='Maximum target concentration', showarrow=False,yshift=10)

        fig4.show()

        st.plotly_chart(fig4,theme=None)


elif pollutant =='Ozone':
    st.write('to be continued...')

