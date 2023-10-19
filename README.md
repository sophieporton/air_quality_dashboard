# Tower Hamlets air quality dashbaord 

Link to dashboard (https://st-augustine-air-quality-dashboard-v2-main-vvrhjv.streamlit.app/#air-quality-dashboard)

 This project has allowed me to apply knowledge I have gained from the graduate program with ONS as well as learning about new data science relevant software features such as GitHub Actions and SQLite.  The key skills I have taken away are...

 - Creating and querying a SQLite database using the sqlite-utils3 package in Python, db querying was also supported by practising and formatting queries in Datasette
 
- Automation of the dashboard to display live air quality data using the auto-refresh feature in Streamlit, as well as GitHub Actions to run main.py python file every hour and commit new copy of db to repository
 
- Accessing a live API using control flow knowledge (i.e. loops, list comprehensions), and piping data points into a SQLite table 
 
- Managing performance of dashboard (how quickly it loads) by cleaning up code. For example, code for creating yearly means tables is commented out as this is not live data so does not need to be refreshed every time the dashboard loads
 
- Making use of modular programming techniques by creating a separate functions.py file, this improves the readability and organisation of my code

- Getting used to coding directly in a Python file rather than a notebook, as this improves efficiency when integrating with Streamlit
