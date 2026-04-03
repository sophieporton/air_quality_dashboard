# Tower Hamlets Air Quality Dashboard

🌐 **Live Dashboard:**  
https://airqualitydashboardlbth.streamlit.app/

---

## Overview

This project delivers a **fully automated, real-time air quality monitoring dashboard** for Tower Hamlets using open data from the Environmental Research Group (ERG) at King’s College London.

The dashboard presents clear, client-ready insights into pollutant trends using **live API ingestion, automated data engineering pipelines, and interactive visualisation** - without requiring any manual intervention.

It is designed to be:

- **Reliable** – data automatically refreshes hourly  
- **Transparent** – all historical records stored in a structured SQLite database  
- **Accessible** – interactive visual analytics via Streamlit  
- **Lightweight & maintainable** – optimised for fast loading and stable performance  

---

## Key Features

### 📡 Live Data Ingestion
- Automatically retrieves air quality readings from the London Air Quality Network API.  
- Includes full ETL flow: API → validation → filtering → typed data → SQLite storage.

### 🗄️ Robust Data Engineering (SQLite)
- Clean, relational data model for pollutants (NO₂ and O₃).  
- Structured tables for hourly and annual measures.  
- Uses SQLite-utils for consistent schema definition, constraints, and upserts.

### ⚙️ Automation
- Scheduled updates via **GitHub Actions** run hourly, rebuilding the database and ensuring the dashboard stays up-to-date.  
- Streamlit auto-refresh triggers live updates for users.

### 📊 Interactive Visualisation
- Clear trend lines for annual pollutant levels, regulatory limit exceedances, and sensor capture rates.  
- Intuitive UI allowing users to filter by pollutant and metric.  
- Highlights whether annual/limit thresholds are being exceeded.

### ⚡ High Performance
- Removed unnecessary recomputation to ensure fast loading times.  
- Optimised API calls and selective data refreshes reduce bandwidth and processing load.

### 🧩 Clean Code Architecture
- Separation of concerns using a dedicated `functions.py` module.  
- Modular design supports scalability - new pollutant types or endpoints can be added easily.

---

## Impact & Use Cases

This dashboard demonstrates how modern data engineering and automation can support:

### **Local Government & Public Health**
- Track compliance with UK air quality targets.  
- Identify long-term trends and periods of poor air quality.  
- Support environmental reporting and community transparency.

### **Consultancy & Analytics Work**
- Shows capability in building fully automated data pipelines.  
- Demonstrates deployable, client-facing interactive products.  
- Highlights expertise in real-time data, API integration, and cloud-based dashboards.

### **Environmental, Scientific & Urban Planning Applications**
- Monitor pollution hotspots  
- Support hypothesis testing and intervention analysis  
- Provide evidence for policy decisions  

---

## Tech Stack

- **Python**  
- **Streamlit**  
- **SQLite / sqlite-utils**  
- **GitHub Actions**  
- **Plotly**  
- **Pandas**  
- **Requests**  
- **Datasette**  
- **PIL**
