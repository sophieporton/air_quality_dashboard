# app_refactor.py
"""
Refactored Air Quality Dashboard
- Modular structure
- Caching
- Robust API handling
- Streamlit UX improvements (KPIs, download, filters)
"""

from datetime import date, datetime, timedelta
import time
import sqlite3
import sqlite_utils
import requests
import pandas as pd
import numpy as np

import streamlit as st
import plotly.express as px

# -------------------------
# Configuration / constants
# -------------------------
DB_PATH = "air-sensors.db"
SITE_GROUP = "towerhamlets"
API_BASE = "https://api.erg.ic.ac.uk/AirQuality"
DEFAULT_CACHE_TTL = 30 * 60  # 30 minutes

POLLUTANT_CONFIG = {
    "NO2": {
        "species_code": "NO2",
        "annual_objectives": {
            "annual_mean": "40 ug/m3 as an annual mean",
            "hourly_exceedances": "200 ug/m3 as a 1 hour mean, not to be exceeded more than 18 times a year",
            "capture_rate": "Capture Rate (%)"
        },
        "thresholds": {"annual_mean": 40, "hourly_limit": 200, "allowed_exceedances": 18}
    },
    "Ozone": {  # label in sidebar uses 'Ozone' but species_code 'O3'
        "species_code": "O3",
        "annual_objectives": {
            "8hr_exceedances": "100 ug/m3 as an 8 hour mean, not to be exceeded more than 10 times a year",
            "capture_rate": "Capture Rate (%)"
        },
        "thresholds": {"8hr_limit": 100, "allowed_exceedances": 10}
    }
}

# -------------------------
# Helper utilities
# -------------------------

def get_db(db_path=DB_PATH):
    """
    Return sqlite_utils.Database instance stored in session_state to avoid reopening.
    """
    if "db" not in st.session_state:
        st.session_state.db = sqlite_utils.Database(db_path)
    return st.session_state.db

def create_sqlite_tables_if_missing(db):
    """
    Create tables if they do not exist using sqlite_utils (light-touch).
    This function is idempotent.
    """
    # NO2_hourly
    if "NO2_hourly" not in db.table_names():
        db.create_table(
            "NO2_hourly",
            columns={"@MeasurementDateGMT": str, "@Value": float, "@Site": str},
            pk=("@MeasurementDateGMT", "@Site"),
        )
    if "NO2_annually" not in db.table_names():
        db.create_table(
            "NO2_annually",
            columns={"@Year": int, "@Value": float, "@SiteName": str, "@ObjectiveName": str},
            pk=("@Year", "@SiteName", "@ObjectiveName"),
        )
    # O3
    if "O3_hourly" not in db.table_names():
        db.create_table(
            "O3_hourly",
            columns={"@MeasurementDateGMT": str, "@Value": float, "@Site": str},
            pk=("@MeasurementDateGMT", "@Site"),
        )
    if "O3_annually" not in db.table_names():
        db.create_table(
            "O3_annually",
            columns={"@Year": int, "@Value": float, "@SiteName": str, "@ObjectiveName": str},
            pk=("@Year", "@SiteName", "@ObjectiveName"),
        )

@st.cache_data(ttl=DEFAULT_CACHE_TTL)
def fetch_sites(group=SITE_GROUP):
    """
    Fetch monitoring sites for a group (Tower Hamlets).
    Cached for DEFAULT_CACHE_TTL.
    """
    url = f"{API_BASE}/Information/MonitoringSiteSpecies/GroupName={group}/Json"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        j = r.json()
        sites = j.get("Sites", {}).get("Site", [])
        return sites
    except Exception as e:
        st.warning(f"Failed to fetch sites from API: {e}")
        return []

def safe_float(v):
    try:
        return float(v)
    except Exception:
        return np.nan

def normalize_raw_data(data_list, site_name):
    """
    Convert @Value to float and add @Site field
    """
    normalized = []
    for item in data_list:
        val = item.get("@Value", "")
        if val == "" or val == "0":  # replicate original filtering
            continue
        fval = safe_float(val)
        if np.isnan(fval):
            continue
        item["@Value"] = fval
        item["@Site"] = site_name
        normalized.append(item)
    return normalized

def fetch_and_store_hourly(db, site, species_code, start_date, end_date):
    """
    Fetch hourly data for a single site and store into sqlite_utils table.
    Quietly handles errors.
    """
    start_str = start_date.strftime("%d %b %Y")
    end_str = end_date.strftime("%d %b %Y")
    site_code = site.get("@SiteCode")
    site_name = site.get("@SiteName")
    url = f'{API_BASE}/Data/SiteSpecies/SiteCode={site_code}/SpeciesCode={species_code}/StartDate={start_str}/EndDate={end_str}/Json'
    try:
        r = requests.get(url, timeout=15, headers={"Connection": "close"})
        r.raise_for_status()
        j = r.json()
        raw = j.get("RawAQData", {}).get("Data", [])
        filtered = normalize_raw_data(raw, site_name)
        if filtered:
            table_name = f"{species_code}_hourly" if species_code in ["NO2", "O3"] else None
            if table_name:
                db[table_name].upsert_all(filtered, pk=("@MeasurementDateGMT", "@Site"))
            return len(filtered)
        return 0
    except Exception as e:
        # do not crash the whole update; log minimal info
        st.sidebar.error(f"API error for {site_name} ({species_code}): {e}")
        return 0

@st.cache_data(ttl=DEFAULT_CACHE_TTL)
def load_table_as_df(db_path, sql_command):
    """
    Read SQL into pandas DataFrame using sqlite3 (cached).
    """
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql_command, conn)
        return df
    finally:
        conn.close()

# --------------
# App UI helpers
# --------------

def plot_time_series(df, x_col, y_col, color_col, title, y_label, range_slider=True, hlines=None, rolling=None):
    """
    Returns a Plotly figure with nicer defaults.
    - rolling: integer window for rolling mean (in observations) or None
    - hlines: list of dicts {y: value, text: "label", dash: "dot"}
    """
    if df.empty:
        fig = px.line(title="No data to display")
        return fig

    # parse datetime if needed
    if not np.issubdtype(df[x_col].dtype, np.datetime64):
        try:
            df[x_col] = pd.to_datetime(df[x_col])
        except Exception:
            pass

    if rolling:
        df = df.sort_values(x_col)
        df[y_col + f"_roll_{rolling}"] = df.groupby(color_col)[y_col].transform(lambda s: s.rolling(window=rolling, min_periods=1).mean())
        y_plot = y_col + f"_roll_{rolling}"
        hover_template = "<b>%{x}</b><br><b>value</b>: %{y:.2f}"
    else:
        y_plot = y_col
        hover_template = "<b>%{x}</b><br><b>value</b>: %{y:.2f}"

    fig = px.line(df, x=x_col, y=y_plot, color=color_col, title=title, width=1100, height=650)
    fig.update_layout(margin=dict(l=40, r=20, t=80, b=40), legend_title_text="", font=dict(size=14))
    fig.update_xaxes(title_text="", tickfont=dict(size=12))
    fig.update_yaxes(title_text=y_label, tickfont=dict(size=12))
    fig.update_traces(hovertemplate=hover_template)
    if range_slider:
        fig.update_xaxes(rangeslider_visible=True)

    if hlines:
        for hl in hlines:
            fig.add_hline(y=hl.get("y"), line_dash=hl.get("dash", "dot"))
            if hl.get("text"):
                fig.add_annotation(xref="paper", x=0.99, xanchor="right", y=hl.get("y"), text=hl.get("text"), showarrow=False, bgcolor="rgba(255,255,255,0.6)")
    return fig

# -------------------------
# Data ingestion routines
# -------------------------

def update_hourly_data(db, sites, species_code, weeks_back=2, chunk_weeks=2, verbose=False):
    """
    Fetch hourly data for sites over the last `weeks_back` weeks, in chunks of `chunk_weeks`.
    Use caching at a higher level (wrap caller in st.cache_data if desired).
    This function writes into db and returns total number of inserted rows (approx).
    """
    # Compute date windows
    end_date = date.today() + timedelta(days=1)
    start_date = end_date - timedelta(weeks=weeks_back)
    total_inserted = 0
    window_end = end_date
    window_start = end_date - timedelta(weeks=chunk_weeks)

    # Iterate backward in chunks
    while window_start >= start_date:
        for site in sites:
            inserted = fetch_and_store_hourly(db, site, species_code, window_start, window_end)
            total_inserted += inserted
            if verbose and inserted:
                st.sidebar.write(f"Inserted {inserted} rows for {site.get('@SiteName')} ({species_code})")
        window_end = window_start
        window_start = window_end - timedelta(weeks=chunk_weeks)
    return total_inserted

# -------------------------
# Streamlit App Layout
# -------------------------
def main():
    st.set_page_config(page_title="Tower Hamlets Air Quality", layout="wide")
    st.title("Tower Hamlets — Air Quality Dashboard")

    st.markdown(
        """
        Data from the Environmental Research Group, King's College London (ERG) via the London Air Quality Network.
        Source API: `api.erg.ic.ac.uk`. Data licensed under Open Government Licence.
        """
    )

    # Sidebar: logo + controls
    with st.sidebar:
        st.image("logo.png", use_column_width=True) if (Path := "logo.png") else None
        pollutant = st.selectbox("Choose pollutant", options=["NO2", "Ozone"], index=0)
        # Date range control
        max_end = date.today()
        default_start = max_end - timedelta(weeks=12)
        date_range = st.date_input("Date range", value=(default_start, max_end))
        # Rolling window
        rolling = st.selectbox("Rolling average (observations)", options=[None, 3, 6, 24], index=0)
        # Site filter will be filled after fetching sites
        st.markdown("---")
        st.write("Auto-refresh interval: 30 minutes")
        st.button("Force refresh cache", on_click=st.cache_data.clear)
        st.markdown("---")
        st.caption("App improvements: caching, KPIs, download and range filters.")

    # Load DB and create minimal tables if missing
    db = get_db()
    create_sqlite_tables_if_missing(db)

    # Fetch sites (cached)
    sites = fetch_sites(SITE_GROUP)
    site_names = [s.get("@SiteName") for s in sites] if sites else []
    selected_sites = st.sidebar.multiselect("Select sites (optional)", options=site_names, default=site_names[:3] if site_names else [])

    # Data ingestion controls (collapsed)
    with st.expander("Update data from API (manual)"):
        st.write("This will fetch recent hourly data and update the local database.")
        weeks_back = st.number_input("Weeks to fetch", min_value=1, max_value=52, value=12)
        if st.button("Update hourly data now"):
            with st.spinner("Fetching hourly data..."):
                # Use shorter chunks for reliability
                species_code = POLLUTANT_CONFIG["NO2"]["species_code"] if pollutant == "NO2" else POLLUTANT_CONFIG["Ozone"]["species_code"]
                inserted = update_hourly_data(db, sites, species_code, weeks_back=weeks_back, chunk_weeks=2, verbose=False)
                st.success(f"Finished update — approx {inserted} records processed.")
                # clear read cache so UI will re-read DB
                st.cache_data.clear()

    # Choose table names based on pollutant
    species_code = POLLUTANT_CONFIG["NO2"]["species_code"] if pollutant == "NO2" else POLLUTANT_CONFIG["Ozone"]["species_code"]
    hourly_table = f"{species_code}_hourly"
    annually_table = f"{species_code}_annually"

    # Build SQL query for hourly
    start_date, end_date = date_range
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())  # inclusive

    sql_hourly = f"SELECT * FROM {hourly_table} WHERE 1=1"
    if selected_sites:
        safe_sites = "', '".join(selected_sites).replace("'", "''")
        sql_hourly += f" AND [@Site] IN ('{safe_sites}')"
    sql_hourly += f" AND datetime([@MeasurementDateGMT]) BETWEEN '{start_dt.isoformat()}' AND '{end_dt.isoformat()}' ORDER BY datetime([@MeasurementDateGMT])"

    # Load hourly data (cached)
    try:
        df_hourly = load_table_as_df(DB_PATH, sql_hourly)
    except Exception as e:
        st.error(f"Error reading hourly data: {e}")
        df_hourly = pd.DataFrame()

    # Convert time column if present
    if not df_hourly.empty and "@MeasurementDateGMT" in df_hourly.columns:
        try:
            df_hourly["@MeasurementDateGMT"] = pd.to_datetime(df_hourly["@MeasurementDateGMT"])
        except Exception:
            pass

    # Top KPI cards
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    if not df_hourly.empty:
        latest = df_hourly.sort_values("@MeasurementDateGMT").iloc[-1]
        latest_val = latest["@Value"]
        latest_site = latest.get("@Site", "Unknown")
        last_ts = latest["@MeasurementDateGMT"]
        kpi_col1.metric("Latest reading", f"{latest_val:.2f} µg/m³", delta=None)
        kpi_col2.metric("Sensor", latest_site)
        kpi_col3.metric("Last updated (GMT)", str(last_ts))
    else:
        kpi_col1.metric("Latest reading", "—")
        kpi_col2.metric("Sensor", "—")
        kpi_col3.metric("Last updated (GMT)", "—")

    # Main tabs
    if pollutant == "NO2":
        st.subheader("Nitrogen dioxide (NO2)")
        explanation = """
        NO2 is produced mainly from combustion processes (traffic, heating). Short-term exposure can impact respiratory health.
        Regulatory annual mean target: 40 µg/m³.
        """
        st.info(explanation)
    else:
        st.subheader("Ozone (O3)")
        explanation = """
        Ground-level ozone is harmful to human health and the environment.
        Regulatory 8-hour target: 100 µg/m³ (max exceedences per year apply).
        """
        st.info(explanation)

    tab_hourly, tab_annual, tab_capture = st.tabs(["Hourly", "Annually", "Capture Rate"])

    with tab_hourly:
        st.markdown("### Hourly measurements")
        hlines = []
        if pollutant == "NO2":
            hlines.append({"y": POLLUTANT_CONFIG["NO2"]["thresholds"]["annual_mean"], "text": "40 µg/m³ (annual target)"})
        else:
            hlines.append({"y": POLLUTANT_CONFIG["Ozone"]["thresholds"]["8hr_limit"], "text": "100 µg/m³ (8-hour target)"})

        fig = plot_time_series(
            df_hourly,
            x_col="@MeasurementDateGMT",
            y_col="@Value",
            color_col="@Site",
            title=f"Hourly {pollutant} measurements",
            y_label=f"{pollutant} concentration (µg/m³)",
            range_slider=True,
            hlines=hlines,
            rolling=rolling
        )
        st.plotly_chart(fig, use_container_width=True)

        # Download button
        if not df_hourly.empty:
            csv = df_hourly.to_csv(index=False).encode("utf-8")
            st.download_button("Download hourly CSV", csv, file_name=f"{pollutant}_hourly_{start_date}_{end_date}.csv")

    with tab_annual:
        st.markdown("### Annual summaries")
        # Build and run an SQL query to get annual data relevant to pollutant objectives
        if pollutant == "NO2":
            obj_expr = POLLUTANT_CONFIG["NO2"]["annual_objectives"]["annual_mean"]
            sql_ann = f"SELECT * FROM {annually_table} WHERE [@ObjectiveName] = '{obj_expr}' ORDER BY [@Year]"
        else:
            obj_expr = POLLUTANT_CONFIG["Ozone"]["annual_objectives"]["8hr_exceedances"]
            sql_ann = f"SELECT * FROM {annually_table} WHERE [@ObjectiveName] = '{obj_expr}' ORDER BY [@Year']" if False else f"SELECT * FROM {annually_table} WHERE [@ObjectiveName] = '{obj_expr}' ORDER BY [@Year]"

        try:
            df_ann = load_table_as_df(DB_PATH, sql_ann)
            if not df_ann.empty:
                fig_ann = plot_time_series(df_ann, x_col="@Year", y_col="@Value", color_col="@SiteName", title="Annual values", y_label="Value", range_slider=False)
                st.plotly_chart(fig_ann, use_container_width=True)
                st.dataframe(df_ann)
                st.download_button("Download annual CSV", df_ann.to_csv(index=False).encode("utf-8"), file_name=f"{pollutant}_annual.csv")
            else:
                st.info("No annual data available for this pollutant/objective in the local DB.")
        except Exception as e:
            st.error(f"Error reading annual data: {e}")

    with tab_capture:
        st.markdown("### Capture rate (annual % of readings available)")
        try:
            obj_expr = "Capture Rate (%)"
            sql_capture = f"SELECT * FROM {annually_table} WHERE [@ObjectiveName] = '{obj_expr}' ORDER BY [@Year]"
            df_cap = load_table_as_df(DB_PATH, sql_capture)
            if not df_cap.empty:
                fig_cap = plot_time_series(df_cap, x_col="@Year", y_col="@Value", color_col="@SiteName", title="Annual capture rate (%)", y_label="Capture Rate (%)", range_slider=False)
                st.plotly_chart(fig_cap, use_container_width=True)
                st.dataframe(df_cap)
            else:
                st.info("No capture rate data available for this pollutant in the local DB.")
        except Exception as e:
            st.error(f"Error reading capture rate data: {e}")

    st.sidebar.markdown("---")
    st.sidebar.write("Last cache clear: use 'Force refresh cache' to reset cached API reads and SQL reads.")

if __name__ == "__main__":
    main()
