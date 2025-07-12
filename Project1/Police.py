import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import plotly.express as px
from datetime import datetime

# Create Database Connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '',
            database = 'securecheck'
        )
        return connection
    except Error as e:
        st.error(f"Database Connection Error: {e}")
        return None
    

# Fetch Data from Database
def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            result = cursor.fetchall()
            df = pd.DataFrame(result)
            return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()
    

# Streamlit App Title
st.set_page_config(page_title="SecureCheck - Police Logs Dashboard", layout="wide")
st.title("🚦🚦 SecureCheck: Police Check Post Digital Ledger")
st.markdown("Real-Time monitoring and actionable insights for Law Enforcement 🚨🚨")

# Sidebar for navigation
st.sidebar.title("Menu")
page = st.sidebar.radio("Go to", ["Police Logs Overview", "Visualization & Metrics", "Actionable Insights", "Natural Language Prediction Form"])


# Full Table Display
query = "SELECT * FROM traffic_stops"
data = fetch_data(query)

if page == "Police Logs Overview":
    st.header("📋Police Logs Overview")
    st.dataframe(data,use_container_width=False)

# Data Visualization & Key Metrics
elif page == "Visualization & Metrics":
    st.header("📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_stops = data.shape[0]
        st.metric("Total Police Stops", total_stops)
    
    with col2:
        arrest = data[data['stop_outcome'].str.contains('arrest', case = False, na = False)].shape[0]
        st.metric("Total Arrests", arrest)

    with col3:
        warning = data[data['stop_outcome'].str.contains('warning', case = False, na = False)].shape[0]
        st.metric("Total Warnings", warning)
    
    with col4:
        drug = data[data['drugs_related_stop']==1].shape[0]
        st.metric("Total Drug Related Stops", drug)

    st.header("📈 Visual Insights")

    tab1, tab2, tab3 = st.tabs(["Stops by Violation", "Country Violation Distribution", "Driver Gender Distribution"])

    with tab1:
        if not data.empty and 'violation' in data.columns:
            violation_data = data['violation'].value_counts().reset_index()
            violation_data.columns = ['Violation', 'Count']
            fig = px.bar(violation_data, x = 'Violation', y = 'Count', title = 'Stops by Violation type', color = 'Violation')
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("No Data Available for Violation Chart")
    
    with tab2:
        if not data.empty and 'country_name' in data.columns:
            country_violation_data = data.groupby('country_name')['violation'].count().reset_index()
            country_violation_data.columns = ['Country', 'Violation Count']
            fig = px.bar(country_violation_data,x='Country', y='Violation Count', title = "Violation counts by country", color = 'Country')
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No Data Available for Country-wise Violation Chart")
    
    with tab3:
        if not data.empty and 'driver_gender' in data.columns:
            gender_data = data['driver_gender'].value_counts().reset_index()
            gender_data.columns = ['Gender', 'Count']
            fig = px.bar(gender_data, x = 'Gender', y = 'Count', title = 'Driver Gender Distribution', color = 'Gender')
            st.plotly_chart(fig, use_container_width=True)
        
        else:
        
            st.warning("No Data available for Gender Distribution Chart")

elif page == "Actionable Insights":
    st.header("🔎 Actionable Insights")

    selected_query = st.selectbox("Select a Query to Run", [
        "Top 10 vehicle_numbers involved in drug-related stops",
        "Most frequently searched vehicle number",
        "Driver age group with highest arrest rate"
    ])

    query_map = {
        "Top 10 vehicle_numbers involved in drug-related stops" : "SELECT vehicle_number, COUNT(*) AS stop_count "
        "FROM traffic_stops WHERE drugs_related_stop = TRUE GROUP BY vehicle_number HAVING stop_count > 0 "
        "ORDER BY stop_count DESC LIMIT 10;",
        
        "Most frequently searched vehicle number" : "SELECT vehicle_number, COUNT(*) AS search_count FROM traffic_stops "
        "WHERE search_conducted = TRUE GROUP BY vehicle_number ORDER BY search_count DESC LIMIT 10;",

        "Driver age group with highest arrest rate" : "SELECT age_group, COUNT(*) AS total_stops, "
        "SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) AS arrests, "
        "ROUND(SUM(CASE WHEN is_arrested = 'TRUE' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate_percent "
        "FROM ( SELECT *, CASE WHEN driver_age < 18 THEN '<18' "
        "WHEN driver_age BETWEEN 18 AND 25 THEN '18-25' "
        "WHEN driver_age BETWEEN 26 AND 35 THEN '26-35' "
        "WHEN driver_age BETWEEN 36 AND 50 THEN '36-50' "
        "ELSE '51+' END AS age_group FROM traffic_stops "
        "WHERE driver_age IS NOT NULL) AS grouped_data "
        "GROUP BY age_group ORDER BY arrest_rate_percent DESC;"

    }

    if st.button("Run Query"):
        result = fetch_data(query_map[selected_query])
        if not result.empty:
             st.write(result)
        else:
            st.warning("No result for the selected query")

elif page == "Natural Language Prediction Form":
    st.header("🔍 Natural Language Prediction Form")
    st.markdown("Fill in the details below to get the prediction of the stop outcome based on existing data")
    st.subheader("Predict Outcome and Violation")

    with st.form("New Log Form"):
        stop_date = st.date_input("Stop Date")
        stop_time = st.time_input("Stop Time", value="14:30")  # HH:MM format
        country_name = st.text_input("Country Name")
        driver_gender = st.selectbox("Driver Gender", ['male', 'female'])
        driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
        driver_race = st.text_input("Driver Race")
        search_conducted = st.selectbox("Was a search conducted?", ['0', '1'])
        search_type = st.text_input("Search Type")
        drugs_related_stop = st.selectbox("Was it Drug Related?", ["0", "1"])
        stop_duration = st.selectbox("Stop Duration", data['stop_duration'].dropna().unique())
        vehicle_number = st.text_input("Vehicle Number")
        stop_datetime = pd.Timestamp.now()

        submitted = st.form_submit_button("Predict Stop Outcome & Violation")

        if submitted:
            # Convert stop_time to proper time format
            try:
                stop_time_obj = datetime.strptime(stop_time, "%H:%M").time()
                time_str = stop_time_obj.strftime('%-I:%M %p')
            except:
                stop_time_obj = datetime.now().time()
                time_str = stop_time_obj.strftime('%I:%M %p')

            # Filter dataset
            filtered_data = data[
                (data['driver_gender'] == driver_gender) &
                (data['driver_age'] == driver_age) &
                (data['search_conducted'] == int(search_conducted)) &
                (data['stop_duration'] == stop_duration) &
                (data['drugs_related_stop'] == int(drugs_related_stop)) &
                (data['vehicle_number'] == vehicle_number)
            ]

            # Predict based on most frequent values
            if not filtered_data.empty:
                predicted_outcome = filtered_data['stop_outcome']
                predicted_violation = filtered_data['violation']
            else:
                predicted_outcome = "Warning"
                predicted_violation = "Speeding"

            # Summary components
            search_text = "A search was conducted" if int(search_conducted) else "No search was conducted"
            drug_text = "was drug-related" if int(drugs_related_stop) else "was not drug-related"

            # Final output
            st.markdown(f""" 
            ### 🚨 Prediction Summary

            **Predicted Violation:** {predicted_violation}  
            **Predicted Stop Outcome:** {predicted_outcome}

            A {driver_age}-year-old {driver_gender} driver from **{country_name}** was stopped for **{predicted_violation}** at **{time_str}** on **{stop_date.strftime('%B %d, %Y')}**.  
            {search_text}, and the stop {drug_text}.  
            
            **Stop duration:** {stop_duration}  
            **Vehicle number:** {vehicle_number}
            """)

