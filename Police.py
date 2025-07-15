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
page = st.sidebar.radio("Go to", ["Police Logs Overview", "Visualization & Metrics", "Actionable Insights", "Violation Prediction Form"])


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
            fig = px.pie(country_violation_data, names='Country', values='Violation Count', title="Violation Distribution by Country", hole=0.3)
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
    st.subheader("Basic Insights")

    selected_query = st.selectbox("Select a Query to Run", [
        "1. Top 10 vehicle_numbers involved in drug-related stops",
        "2. Most frequently searched vehicle number",
        "3. Driver age group with highest arrest rate",
        "4. Gender distribution of drivers stopped in each country",
        "5. Race and gender combination with highest search rate",
        "6. Time of day with most traffic stops",
        "7. Average stop duration for different violations",
        "8. Are night stops more likely to lead to arrests?",
        "9. Violations most associated with searches or arrests",
        "10. Violations most common among drivers under age 25",
        "11. Violation that rarely results in search or arrest",
        "12. Countries with highest rate of drug-related stops",
        "13. Arrest rate by country and violation",
        "14. Countries with most stops where search was conducted"
    ])

    query_map = {
        "1. Top 10 vehicle_numbers involved in drug-related stops" : """
        SELECT vehicle_number, 
        COUNT(*) AS stop_count FROM traffic_stops 
        WHERE drugs_related_stop = TRUE 
        GROUP BY vehicle_number HAVING stop_count > 0 
        ORDER BY stop_count DESC LIMIT 10;""",

        "2. Most frequently searched vehicle number" : """
        SELECT vehicle_number, COUNT(*) AS search_count 
        FROM traffic_stops 
        WHERE search_conducted = TRUE 
        GROUP BY vehicle_number 
        ORDER BY search_count DESC LIMIT 10;""",


        "3. Driver age group with highest arrest rate" : """
        SELECT 
        CASE
            WHEN driver_age < 18 THEN 'Under 18'
            WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
            WHEN driver_age BETWEEN 26 AND 40 THEN '26-40'
            WHEN driver_age BETWEEN 41 AND 60 THEN '41-60'
            ELSE '60+'
        END AS age_group,
        COUNT(*) AS total_stops,
        SUM(is_arrested) AS total_arrests,
        ROUND(SUM(is_arrested) / COUNT(*) * 100, 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY age_group
        ORDER BY arrest_rate DESC;
        """,


        "4. Gender distribution of drivers stopped in each country" : """
        SELECT country_name, driver_gender, COUNT(*) AS stop_count 
        FROM traffic_stops 
        GROUP BY country_name, driver_gender 
        ORDER BY country_name;
        """,


        "5. Race and gender combination with highest search rate" : """
        SELECT driver_race, driver_gender, COUNT(*) AS total_stops,
        SUM(search_conducted) AS total_searches, 
        ROUND(SUM(search_conducted) / COUNT(*) * 100, 2) AS search_rate 
        FROM traffic_stops 
        GROUP BY driver_race, driver_gender 
        ORDER BY search_rate DESC;
        """,


        "6. Time of day with most traffic stops" : """
        SELECT
        CASE 
            WHEN HOUR(stop_time) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN HOUR(stop_time) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN HOUR(stop_time) BETWEEN 17 AND 20 THEN 'Evening'
            ELSE 'Night'
        END AS time_of_day,
        COUNT(*) AS total_stops
        FROM traffic_stops
        GROUP BY time_of_day
        ORDER BY total_stops DESC;
        """,


        "7. Average stop duration for different violations" : """
        SELECT violation, AVG(stop_duration) AS avg_duration
        FROM traffic_stops
        GROUP BY violation
        ORDER BY avg_duration DESC;
        """,    


        "8. Are night stops more likely to lead to arrests?" : """
        SELECT
        CASE
            WHEN HOUR(stop_time) >= 20 OR HOUR(stop_time) < 6 THEN 'Night'
            ELSE 'Day'
        END AS time_period,
        COUNT(*) AS total_stops,
        SUM(is_arrested) AS arrests,
        ROUND(SUM(is_arrested) / COUNT(*) * 100, 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY time_period;
        """,


        "9. Violations most associated with searches or arrests" : """
        SELECT violation,
        ROUND(SUM(search_conducted)/COUNT(*)*100, 2) AS search_rate,
        ROUND(SUM(is_arrested)/COUNT(*)*100, 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY search_rate DESC, arrest_rate DESC;
        """,


        "10. Violations most common among drivers under age 25" : """
        SELECT violation, COUNT(*) AS count
        FROM traffic_stops
        WHERE driver_age < 25
        GROUP BY violation
        ORDER BY count DESC;
        """,


        "11. Violation that rarely results in search or arrest" : """
        SELECT violation,
        ROUND(SUM(search_conducted)/COUNT(*)*100, 2) AS search_rate,
        ROUND(SUM(is_arrested)/COUNT(*)*100, 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY search_rate ASC, arrest_rate ASC
        LIMIT 5;
        """,


        "12. Countries with highest rate of drug-related stops" : """
        SELECT country_name,
        COUNT(*) AS total_stops,
        SUM(drugs_related_stop) AS drug_stops,
        ROUND(SUM(drugs_related_stop)/COUNT(*)*100, 2) AS drug_rate
        FROM traffic_stops
        GROUP BY country_name
        ORDER BY drug_rate DESC;
        """,


        "13. Arrest rate by country and violation" : """
        SELECT country_name, violation,
        COUNT(*) AS total,
        SUM(is_arrested) AS arrests,
        ROUND(SUM(is_arrested)/COUNT(*)*100, 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY country_name, violation
        ORDER BY country_name ASC, arrest_rate DESC;
        """,


        "14. Countries with most stops where search was conducted" : """
        SELECT country_name, COUNT(*) AS searches
        FROM traffic_stops
        WHERE search_conducted = TRUE
        GROUP BY country_name
        ORDER BY searches DESC;
        """


    }

    if st.button("Run", key = "button_1"):
        result = fetch_data(query_map[selected_query])
        if not result.empty:
             st.write(result)
        else:
            st.warning("No result for the selected query")

    st.subheader("Advanced Insights")

    selected_query1 = st.selectbox("Select a Query to Run", [
        "1. Yearly breakdown of stops and arrests by country",
        "2. Driver violation trends by age and race",
        "3. Time period analysis of stops (Year, Month, Hour)",
        "4. Violations with high search and arrest rates",
        "5. Driver demographics by country (age, gender, race)",
        "6. Top 5 violations with highest arrest rates"
    ])

    query_map1 = {
        
        "1. Yearly breakdown of stops and arrests by country" : """
        SELECT 
        country_name,
        stop_year,
        total_stops,
        total_arrests,
        ROUND((total_arrests / total_stops) * 100, 2) AS arrest_rate_percent,
        SUM(total_stops) OVER (PARTITION BY country_name ORDER BY stop_year) AS cumulative_stops,
        SUM(total_arrests) OVER (PARTITION BY country_name ORDER BY stop_year) AS cumulative_arrests
        FROM (
            SELECT 
                country_name,
                YEAR(stop_date) AS stop_year,
                COUNT(*) AS total_stops,
                SUM(is_arrested) AS total_arrests
            FROM traffic_stops
            GROUP BY country_name, YEAR(stop_date)
        ) AS yearly_stats
        ORDER BY country_name, stop_year;

        """,


        "2. Driver violation trends by age and race" : """
        SELECT DISTINCT
        t.driver_race, t.driver_age, t.violation, v.total_violations
        FROM traffic_stops t
        JOIN (
            SELECT driver_age, driver_race, violation, COUNT(*) AS total_violations
            FROM traffic_stops
            GROUP BY driver_age, driver_race, violation
        ) v
        ON t.driver_age = v.driver_age
        AND t.driver_race = v.driver_race
        AND t.violation = v.violation
        ORDER BY t.driver_race, v.total_violations DESC;

        """,


        "3. Time period analysis of stops (Year, Month, Hour)" : """
        SELECT 
        YEAR(stop_date) AS year,
        MONTH(stop_date) AS month,
        HOUR(stop_time) AS hour,
        COUNT(*) AS total_stops
        FROM traffic_stops
        GROUP BY year, month, hour
        ORDER BY year, month, hour;
        """,


        "4. Violations with high search and arrest rates" : """
        SELECT *, 
        DENSE_RANK() OVER (ORDER BY search_rate DESC) AS search_rank,
        DENSE_RANK() OVER (ORDER BY arrest_rate DESC) AS arrest_rank
        FROM (
        SELECT violation,
            ROUND(SUM(search_conducted)/COUNT(*)*100, 2) AS search_rate,
            ROUND(SUM(is_arrested)/COUNT(*)*100, 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ) AS rates;

        """,


        "5. Driver demographics by country (age, gender, race)" : """
        SELECT country_name, 
        driver_age,
        driver_gender,
        driver_race,
        COUNT(*) AS count
        FROM traffic_stops
        GROUP BY country_name, driver_gender, driver_age, driver_race
        ORDER BY country_name;
        """,

        
        "6. Top 5 violations with highest arrest rates" : """
        SELECT violation,
        COUNT(*) AS total,
        SUM(is_arrested) AS arrests,
        ROUND(SUM(is_arrested)/COUNT(*)*100, 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY arrest_rate DESC
        LIMIT 5;
        """
    }

    if st.button("Run", key = "button_2"):
        result1 = fetch_data(query_map1[selected_query1])
        if not result1.empty:
             st.write(result1)
        else:
            st.warning("No result for the selected query")



#Prediction Form

elif page == "Violation Prediction Form":
    st.header("🔍 Violation Prediction Form")
    st.markdown("Fill in the details below to get the prediction of the stop outcome based on existing data")
    st.subheader("Predict Outcome and Violation")

    with st.form("new_log_form"):
        stop_date = st.date_input("Stop Date")
        stop_time = st.time_input("Stop Time")
        country_name = st.selectbox("Country Name", ["Canada", "USA", "India"])
        driver_gender = st.selectbox("Driver Gender", ["M", "F"])
        driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
        driver_race = st.selectbox("Driver Race", ["White", "Black", "Hispanic", "Asian", "Other"])
        search_conducted = st.selectbox("Was a Search Conducted?", ["0", "1"])
        search_type = st.text_input("Search Type")
        drugs_related_stop = st.selectbox("Was it Drug Related?", ["0", "1"])
        stop_duration = st.selectbox("Stop Duration", data['stop_duration'].dropna().unique())
        vehicle_number = st.text_input("Vehicle Number")

        submitted = st.form_submit_button("Predict Stop Outcome & Violation")

# --- Filter Dataset ---
    if submitted:
        filtered_data = data[
        (data['driver_gender'] == driver_gender) &
        (data['driver_age'] == driver_age) &
        (data['search_conducted'] == int(search_conducted)) &
        (data['stop_duration'] == stop_duration) &
        (data['drugs_related_stop'] == int(drugs_related_stop)) &
        (data['vehicle_number'] == vehicle_number)
    ]

        if not filtered_data.empty:
            predicted_outcome = filtered_data['stop_outcome'].mode()[0]
            predicted_violation = filtered_data['violation'].mode()[0]
        else:
            predicted_outcome = "warning"
            predicted_violation = "speeding"

        # Summary Components
        search_text = "A search was conducted" if int(search_conducted) else "no search was conducted"
        drug_text = "was drug-related" if int(drugs_related_stop) else "was not drug-related"


        # Final output
        st.markdown(f""" 
            ### 🚨 Prediction Summary

            **Predicted Violation:** {predicted_violation}  
            **Predicted Stop Outcome:** {predicted_outcome}

            A **{driver_age}-year-old {driver_gender}** (M - Male / F - Female) **driver** from **{country_name}** was stopped for **{predicted_violation}** at **{stop_time.strftime('%I:%M %p')}** on **{stop_date.strftime('%B %d, %Y')}**.  
            {search_text}, and the stop {drug_text}.  
            
            **Stop duration:** {stop_duration}  
            **Vehicle number:** {vehicle_number}
            """)


    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; font-size: 24px; font-weight: bold; color: #fff033;'>
            Obey the Law ❤️ Respect the Law ❤️ Protect the Law
        </div>
        """,
        unsafe_allow_html=True
    )