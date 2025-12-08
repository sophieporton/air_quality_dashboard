# %% IMPORTS
import pandas as pd
import streamlit as st
import numpy as np
import requests
from datetime import date, timedelta
import sqlite_utils
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import functions
from functions import create_connection
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from PIL import Image


# %% CREATE SQLITE TABLES
db = sqlite_utils.Database("air-sensors.db")


functions.add_sqlite_table(
    db=db,
    tablename='NO2_annually',
    pk=('@Year', '@SiteName', '@ObjectiveName'),
    not_null={"@Year", "@Value", "@SiteName"},
    column_order=("@Year", "@Value", "@SiteName")
)

functions.add_sqlite_table(
    db=db,
    tablename='O3_annually',
    pk=('@Year', '@SiteName', '@ObjectiveName'),
    not_null={"@Year", "@Value", "@SiteName"},
    column_order=("@Year", "@Value", "@SiteName")
)




# %% EXTRACT THE SITES IN TOWER HAMLETS
try:
    req = requests.get(
        "https://api.erg.ic.ac.uk/AirQuality/Information/MonitoringSiteSpecies/GroupName=towerhamlets/Json",
        timeout=10
    )
    js = req.json()
    sites = js['Sites']['Site']
except Exception as e:
    st.error(f"Failed to fetch site list: {e}")
    sites = []




# %% STREAMLIT PAGE CONFIG
st.set_page_config(layout="wide")

st.title("Air quality dashboard")
st.write("""
This is a dashboard displaying air quality data in Tower Hamlets.
This information has been obtained from the Environmental Research Group of Kings College London,
using data from the London Air Quality Network.  
Licensed under the Open Government Licence.
""")

st_autorefresh(interval=30*60*1000, key="api_update")  # refresh every 30 minutes

image = functions.get_image("logo.png")
if image:
    st.sidebar.image(image)

st.sidebar.header(":black[Filter your data]")

pollutant = st.sidebar.selectbox(
    'Choose a pollutant',
    options=('NO2', 'Ozone')
)

# ============================================================
# NO2 PAGE
# ============================================================

if pollutant == 'NO2':
    st.subheader('Nitrogen dioxide (NO2)')
    st.write("""
Nitrogen dioxide (NO2) is mainly produced during fossil fuel combustion.
Short-term exposure can cause airway inflammation and worsen respiratory conditions.
""")

    st.write("""
UK regulations require the annual mean NO2 concentration to stay below 40 µg/m³,
and no more than 18 exceedances of 200 µg/m³ per hour per year.
""")

    tab2, tab3, tab4 = st.tabs([ "Annually", "Hourly Mean Limit Value", "Capture Rate"])

    

    # ------------------------- TAB 2 -------------------------
    with tab2:
        df = functions.sql_to_pandas(
            'air-sensors.db',
            """
            SELECT * FROM NO2_annually
            WHERE [@ObjectiveName] = '40 ug/m3 as an annual mean';
            """
        )

        fig = px.line(
            df, x='@Year', y='@Value', color='@SiteName',
            width=1200, height=700
        )
        fig.update_layout(
            title='Annual mean NO2 concentrations in Tower Hamlets',
            xaxis_title='Year',
            yaxis_title='NO₂ Concentration (µg/m³)',
            font=dict(size=17),
            legend_title_text=''
        )
        fig.add_hline(y=40, line_dash='dot')

        st.plotly_chart(fig, theme=None)

        st.write("""
Annual mean NO2 levels have declined since 1994, with a sharper drop during COVID,
and remain mostly below the 40 µg/m³ target since 2020.
""")

    # ------------------------- TAB 3 -------------------------
    with tab3:
        df = functions.sql_to_pandas(
            'air-sensors.db',
            """
            SELECT * FROM NO2_annually
            WHERE [@ObjectiveName] = '200 ug/m3 as a 1 hour mean, not to be exceeded more than 18 times a year';
            """
        )

        fig = px.line(
            df, x='@Year', y='@Value', color='@SiteName',
            width=1200, height=700
        )
        fig.update_layout(
            title='Exceedances of the hourly NO2 limit value (200 µg/m³)',
            xaxis_title='Year',
            yaxis_title='Count',
            font=dict(size=17),
            legend_title_text=''
        )
        fig.add_hline(y=18, line_dash='dot')

        st.plotly_chart(fig, theme=None)

        st.write("""
Exceedances have dropped dramatically, with none recorded since 2020.
""")

    # ------------------------- TAB 4 -------------------------
    with tab4:
        df = functions.sql_to_pandas(
            'air-sensors.db',
            """
            SELECT * FROM NO2_annually
            WHERE [@ObjectiveName] = 'Capture Rate (%)';
            """
        )

        fig = px.line(
            df, x='@Year', y='@Value', color='@SiteName',
            width=1200, height=700
        )
        fig.update_layout(
            title='Annual NO2 capture rate',
            xaxis_title='Year',
            yaxis_title='Capture Rate (%)',
            font=dict(size=17),
            legend_title_text=''
        )

        st.plotly_chart(fig, theme=None)

        st.write("""
Capture rate shows how often sensors recorded valid data throughout the year.
""")


# ============================================================
# OZONE PAGE
# ============================================================

if pollutant == 'Ozone':
    st.subheader('Ozone (O₃)')
    st.write("""
Ozone is harmful to respiratory health and vegetation,
and is monitored under UK air quality regulations.
""")

    st.write("""
The target is that 8-hour mean O₃ concentrations should not exceed 100 µg/m³
more than 10 times per year.
""")

    tab2, tab3 = st.tabs(["8 Hour Mean Limit Value", "Capture Rate"])


    # ------------------------- TAB 2 -------------------------
    with tab2:
        df = functions.sql_to_pandas(
            'air-sensors.db',
            """
            SELECT * FROM O3_annually
            WHERE [@ObjectiveName] = '100 ug/m3 as an 8 hour mean, not to be exceeded more than 10 times a year';
            """
        )

        fig = px.line(
            df, x='@Year', y='@Value', color='@SiteName',
            width=1200, height=700
        )
        fig.update_layout(
            title='Exceedances of the 8-hour O₃ limit value',
            xaxis_title='Year',
            yaxis_title='Count',
            font=dict(size=17),
            legend_title_text=''
        )
        fig.add_hline(y=10, line_dash='dot')

        st.plotly_chart(fig, theme=None)

        st.write("""
Poplar exceeded the limit repeatedly (1994–2013), while Blackwall stayed within limits.
""")

    # ------------------------- TAB 3 -------------------------
    with tab3:
        df = functions.sql_to_pandas(
            'air-sensors.db',
            """
            SELECT * FROM O3_annually
            WHERE [@ObjectiveName] = 'Capture Rate (%)';
            """
        )

        fig = px.line(
            df, x='@Year', y='@Value', color='@SiteName',
            width=1200, height=700
        )
        fig.update_layout(
            title='Annual O₃ capture rate',
            xaxis_title='Year',
            yaxis_title='Capture Rate (%)',
            font=dict(size=17),
            legend_title_text=''
        )

        st.plotly_chart(fig, theme=None)

        st.write("""
Only Blackwall has provided O₃ data since 2016.
""")
