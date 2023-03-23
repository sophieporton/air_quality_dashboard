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
from functions import create_connection
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

#%%
functions.add_sqlite_table(db=sqlite_utils.Database("air-sensors.db"),tablename='NO2_hourly',pk=('@MeasurementDateGMT', '@Site'),
    not_null={"@MeasurementDateGMT", "@Value", "@Site"},
    column_order=("@MeasurementDateGMT", "@Value", "@Site"))

functions.add_sqlite_table(db=sqlite_utils.Database("air-sensors.db"),tablename='NO2_annually',pk=('@Year', '@SiteName','@ObjectiveName'),
    not_null={"@Year", "@Value", "@SiteName"},
    column_order=("@Year", "@Value", "@SiteName"))

functions.add_sqlite_table(db=sqlite_utils.Database("air-sensors.db"),tablename='O3_annually',pk=('@Year', '@SiteName','@ObjectiveName'),
    not_null={"@Year", "@Value", "@SiteName"},
    column_order=("@Year", "@Value", "@SiteName"))

functions.add_sqlite_table(db=sqlite_utils.Database("air-sensors.db"),tablename='O3_hourly',pk=('@MeasurementDateGMT', '@Site'),
    not_null={"@MeasurementDateGMT", "@Value", "@Site"},
    column_order=("@MeasurementDateGMT", "@Value", "@Site"))


db = sqlite_utils.Database("air-sensors.db")

#%%

# EXTRACT THE SITES IN TOWER HAMLETS
#api is link between between us and database 
req = requests.get("https://api.erg.ic.ac.uk/AirQuality/Information/MonitoringSiteSpecies/GroupName=towerhamlets/Json") #requests gets the info from the api 
js = req.json() #json is like a python dictionary 
sites = js['Sites']['Site'] #turns dictionary into list 


#%%
conn=create_connection('air-sensors.db')
functions.delete_all_no2hourly(conn)

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


#%%


EndDate = date.today() + timedelta(days = 1)
EndWeekDate = EndDate
StartWeekDate = EndDate - timedelta(weeks = 6)
StartDate = StartWeekDate - timedelta(days = 1)

while StartWeekDate > StartDate :
        for el in sites:
            def convert(list):
                list['@Value'] = float(list['@Value'])
                list['@Site'] = el['@SiteName']
                return list
            url = f'https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/SiteCode={el["@SiteCode"]}/SpeciesCode=O3/StartDate={StartWeekDate.strftime("%d %b %Y")}/EndDate={EndWeekDate.strftime("%d %b %Y")}/Json'
            print(url)
            req = requests.get(url, headers={'Connection':'close'}) #closes connection to the api
            print(req)
            j = req.json()
            # CLEAN SITES WITH NO DATA OR ZERO VALUE OR NOT NO2 (ONLY MEASURE AVAILABLE AT ALL SITES)
            filtered = [a for a in j['RawAQData']['Data'] if a['@Value'] != '' and a['@Value'] != '0' ] #removes zero and missing values 
            if len(filtered) != 0:
                filtered = map(convert, filtered)
                filteredList = list(filtered)
                db['O3_hourly'].upsert_all(filteredList,pk=('@MeasurementDateGMT', '@Site')) #combo of update and insert, updates record if it already exists if not creates it 
        EndWeekDate = StartWeekDate
        StartWeekDate = EndWeekDate - timedelta(weeks = 6)


#%%

cur = conn.cursor() 
last_row = cur.execute('select [@Value] from NO2_hourly').fetchall()[-1]
last_row=float(last_row[0])

if last_row > 40:
    target='above the target limit'
elif last_row < 40:
    target='within the target limit'




#%%
#years=list(range(1994,2024))

#for year in years:    
#   url = f'https://api.erg.ic.ac.uk/AirQuality/Annual/MonitoringObjective/GroupName=towerhamlets/Year={year}/Json'
 #  print(url)
#   req = requests.get(url, headers={'Connection':'close'}) #closes connection to the api
#   print(req)
#   j = req.json()
#   l=j['SiteObjectives']['Site']
#   rows=[]
#   for data in l:
#        data_row=data['Objective']
#        n=data['@SiteName']
#
#        for row in data_row:
#            row['@SiteName']= n
#            rows.append(row)
#    
#   filtered_NO2 = [a for a in rows if a['@SpeciesCode']=='NO2']
#   db['NO2_annually'].upsert_all(filtered_NO2,pk=('@Year', '@SiteName', '@ObjectiveName'))
#   
#   filtered_ozone = [a for a in rows if a['@SpeciesCode']=='O3']
#   db['O3_annually'].upsert_all(filtered_ozone,pk=('@Year', '@SiteName', '@ObjectiveName'))
 

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
     
     tab1, tab2, tab3, tab4 = st.tabs(["Hourly", "Annually","Hourly Mean Limit Value", "Capture Rate"])
     with tab1:

            fig = px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command="""SELECT * FROM NO2_hourly; """), x= '@MeasurementDateGMT', y= '@Value', color='@Site',width=1200, height= 700)

            fig.update_layout(title={
            'text': 'Line plot showing hourly NO2 measurements from active sensors in Tower Hamlets','xanchor': 'left',
            'yanchor': 'top','x':0.05,'y':0.98},
                            xaxis_title='Measurement Date',
                            yaxis_title='NO<sub>2</sub> Concentration (µg/m<sup>3</sup>)',
                            #legend=dict(orientation="h", entrywidth=250,
                            #yanchor="bottom", y=1.02, xanchor="right", x=1),
                            legend_title_text= '', font=dict(size= 17)
                            )

            fig.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
            fig.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))

            #print("plotly express hovertemplate:", fig.data[0].hovertemplate)

            fig.update_traces(hovertemplate='<b>Measurement time (GMT) = </b>%{x}<br><b>Value = </b>%{y}<extra></extra>')

            fig.update_layout(hoverlabel = dict(
                font_size = 16))

            fig.add_hline(y=40,line_dash='dot')

            #fig.add_annotation(x=20,y=40, text='Maximum target concentration', showarrow=False,yshift=10)

            fig.show()

            st.plotly_chart(fig, theme=None)    


            st.write(f'''Hourly NO2 measurements fluctuate with local weather and traffic conditions but mainly stay
            below the 40µgm3 target limit. Currently the only active sensor in Tower Hamlets is at Mile End Road, with
            a latest reading of **{last_row}** which is **:green[{target}]**''')




     with tab2:
        
        fig2=px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command=""" SELECT
        *
        FROM
        NO2_annually
        WHERE
        [@ObjectiveName] = '40 ug/m3 as an annual mean'
                                                                                    """),
                        x='@Year', y='@Value', color='@SiteName', width=1200, height=700)

        fig2.update_layout(title={
        'text': 'Line plot showing annual mean NO2 measurements in Tower Hamlets','xanchor': 'left',
        'yanchor': 'top','x':0.05,'y':0.98},
                            xaxis_title='Year',
                            yaxis_title='NO<sub>2</sub> Concentration (µg/m<sup>3</sup>)'
                            ,
                            #legend=dict(orientation="h",
                            # #          entrywidth=250,
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

        fig2.show()

        st.plotly_chart(fig2,theme=None)

        st.write('''Mean annual NO2 measurements have shown a general decline at all sites since monitoring began in 1994. 
        The COVID-19 pandemic lead to a sharper decline in NO2 concentraation due to reduced traffic, and concentrations at
        Mile End Road and Blackwall have not yet increased to pre-COVID levels. This means NO2 concentrations have mostly remained 
        below the 40µgm3 target limit since 2020. 
        ''')


     with tab3:
        fig3=px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command=""" SELECT
        *
        FROM
        NO2_annually
        WHERE
        [@ObjectiveName] = '200 ug/m3 as a 1 hour mean, not to be exceeded more than 18 times a year'
        
                                                                                    """),
                        x='@Year', y='@Value', color='@SiteName', width=1200, height=700)

        fig3.update_layout(title={
        'text': 'Line plot showing the number of times the hourly mean limit value was exceeded each year','xanchor': 'left',
        'yanchor': 'top','x':0.05,'y':0.98},
                            xaxis_title='Year',
                            yaxis_title='Count',
                            #legend=dict(orientation="h", entrywidth=250,
                            #yanchor="bottom", y=1.02, xanchor="right", x=1),
                            legend_title_text= '', font=dict(size= 17)
                            )

        fig3.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
        fig3.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))

        print("plotly express hovertemplate:", fig3.data[0].hovertemplate)

        fig3.update_traces(hovertemplate='<b>Year </b>%{x}<br><b>Value = </b>%{y}<extra></extra>')

        fig3.update_layout(hoverlabel = dict(
                font_size = 16),yaxis=dict(tickmode = 'linear', tick0 = 10,dtick = 10))

        fig3.add_hline(y=18,line_dash='dot')

        fig3.show()

        st.plotly_chart(fig3,theme=None)

        st.write('''Instances of exceeding the hourly mean limit value (concentrations above 200 µg/m3) have decreased since 
        monitoring began in 1994. There have been no recorded instances of exceeding the hourly mean limit value since 2020, 
        and since 2007 no sites in Tower Hamlets have exceeded the target of 18 times per year. 
        ''')

        
     with tab4:
        fig4=px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command=""" SELECT
        *
        FROM
        NO2_annually
        WHERE
        [@ObjectiveName] = 'Capture Rate (%)'
                                                                                    """),
                        x='@Year', y='@Value', color='@SiteName', width=1200, height=700)

        fig4.update_layout(title={
        'text': 'Line plot showing annual capture rate of NO2 for the sensors in Tower Hamlets','xanchor': 'left',
        'yanchor': 'top','x':0.05,'y':0.98},
                            xaxis_title='Year',
                            yaxis_title='Capture Rate (%)',
                            #legend=dict(orientation="h", entrywidth=250,
                            #yanchor="bottom", y=1.02, xanchor="right", x=1),
                            legend_title_text= '', font=dict(size= 17)
                            )
        #fig4.layout.legend.tracegroupgap = 10
        fig4.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
        fig4.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))

        print("plotly express hovertemplate:", fig4.data[0].hovertemplate)

        fig4.update_traces(hovertemplate='<b>Year </b>%{x}<br><b>Value = </b>%{y}<extra></extra>')

        fig4.update_layout(hoverlabel = dict(
                font_size = 16))

        fig4.show()

        st.plotly_chart(fig4,theme=None)

        st.write(''' The capture rate measures the percentage of the year that the sensor was taking readings. Since 2017 the only sites
        in Tower Hamlets to haave sensors collecting readings are Mile End Road, Blackwall and Jubilee Park. 
        ''')

if pollutant =='Ozone':
     st.subheader('Ozone (O3)')
     st.write('''Ozone (O3) is a gas which is damaging to human health and can trigger inflammation of the 
     respiratory tract, eyes, nose and throat as well as asthma attacks. In addition, 
     ozone can have adverse effects on the environment through oxidative damage to vegetation including crops. 
     ''')
     
     st.write('''The Air Quality Standards Regulations 2010 set the target that the 8-hour mean 
     concentrations of O3 should not exceed 100 µg/m3 more than 10 times per year.
     ''')
     
     tab1, tab2, tab3= st.tabs(["Hourly","8 Hour Mean Limit Value", "Capture Rate"])
     with tab1:
            fig = px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command="""SELECT * FROM O3_hourly; """), x= '@MeasurementDateGMT', y= '@Value', color='@Site',width=1200, height= 700)

            fig.update_layout(title={
            'text': 'Line plot showing hourly NO2 measurements from active sensors in Tower Hamlets','xanchor': 'left',
            'yanchor': 'top','x':0.05,'y':0.98},
                            xaxis_title='Measurement Date',
                            yaxis_title='NO<sub>2</sub> Concentration (µg/m<sup>3</sup>)',
                            #legend=dict(orientation="h", entrywidth=250,
                            #yanchor="bottom", y=1.02, xanchor="right", x=1),
                            legend_title_text= '', font=dict(size= 17)
                            )

            fig.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
            fig.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))

            #print("plotly express hovertemplate:", fig.data[0].hovertemplate)

            fig.update_traces(hovertemplate='<b>Measurement time (GMT) = </b>%{x}<br><b>Value = </b>%{y}<extra></extra>')

            fig.update_layout(hoverlabel = dict(
                font_size = 16))

            fig.add_hline(y=40,line_dash='dot')

            #fig.add_annotation(x=20,y=40, text='Maximum target concentration', showarrow=False,yshift=10)

            fig.show()

            st.plotly_chart(fig, theme=None)    
     with tab2:


        fig5=px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command=""" SELECT
                *
                FROM
                O3_annually
                WHERE
                [@ObjectiveName] = '100 ug/m3 as an 8 hour mean, not to be exceeded more than 10 times a year'
                
                                                                                            """),
                                x='@Year', y='@Value', color='@SiteName', width=1200, height=700)

        fig5.update_layout(title={'text': 'Line plot showing the number of times the 8 hour mean limit value was exceeded annually','xanchor': 'left',
                'yanchor': 'top','x':0.05,'y':0.98},
                                    xaxis_title='Year',
                                    yaxis_title='Count'
                                    ,
                                    #legend=dict(orientation="h",
                                    # #          entrywidth=250,
                                    #yanchor="bottom", y=1.02, xanchor="right", x=1),
                                    legend_title_text= '', font=dict(size= 17)
                                    )

        fig5.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
        fig5.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))
        #print("plotly express hovertemplate:", fig2.data[0].hovertemplate)
        fig5.update_traces(hovertemplate='<b>Year </b>%{x}<br><b>Average value = </b>%{y}<extra></extra>')
        fig5.update_layout(hoverlabel = dict(
                        font_size = 16))

        fig5.show()

        st.plotly_chart(fig5,theme=None)

     with tab3:



        fig6=px.line(functions.sql_to_pandas(db='air-sensors.db', sql_command=""" SELECT
                *
                FROM
                O3_annually
                WHERE
                [@ObjectiveName] = 'Capture Rate (%)'
                
                                                                                            """),
                                x='@Year', y='@Value', color='@SiteName', width=1200, height=700)

        fig6.update_layout(title={'text': 'Line plot showing annual capture rate of O3 by sensors in Tower Hamlets','xanchor': 'left',
                'yanchor': 'top','x':0.05,'y':0.98},
                                    xaxis_title='Year',
                                    yaxis_title='Capture Rate (%)'
                                    ,
                                    #legend=dict(orientation="h",
                                    # #          entrywidth=250,
                                    #yanchor="bottom", y=1.02, xanchor="right", x=1),
                                    legend_title_text= '', font=dict(size= 17)
                                    )

        fig6.update_xaxes(title_font=dict(size=22), tickfont=dict(size=18))
        fig6.update_yaxes(title_font=dict(size=22), tickfont=dict(size=18))

        #print("plotly express hovertemplate:", fig2.data[0].hovertemplate)

        fig6.update_traces(hovertemplate='<b>Year </b>%{x}<br><b>Average value = </b>%{y}<extra></extra>')
        fig6.update_layout(hoverlabel = dict(
                        font_size = 16))

        fig6.show()

        st.plotly_chart(fig6,theme=None)
