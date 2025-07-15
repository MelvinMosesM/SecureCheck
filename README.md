# SecureCheck - A Python-SQL Digital Ledger for Police Post Logs


**SecureCheck** is a data analysis and visualization dashboard built using **Streamlit**, **MySQL**, and **Python (Pandas)** to monitor, analyze, and visualize police traffic stop records and related activities such as searches, arrests, and violations. It is designed to help law enforcement agencies or analysts ensure accountability, improve efficiency, and detect patterns in police stop-and-search behavior.

---

# Dataset

traffic_stops - traffic_stops_with_vehicle_number.csv 


## 📁 Project Structure

Police_SecureCheck/
├── SecureCheck.ipynb #  for data preprocessing
├── Police.py # Streamlit dashboard application
├── requirements.txt # List of Python dependencies
└── README.md # Project documentation

## install dependencies

pip install -r requirements.txt

Set Up MySQL Database

## Create a database named SecureCheck

Import the cleaned data using the insert and iterrows 


Update your MySQL credentials in Police.py:


## Run the streamlit app

streamlit run file_path/Police.py

## Sample queries
-- Top 5 violations with highest arrest rates



SELECT violation,
COUNT(*) AS total,
SUM(is_arrested) AS arrests,
ROUND(SUM(is_arrested)/COUNT(*)*100, 2) AS arrest_rate
FROM traffic_stops
GROUP BY violation
ORDER BY arrest_rate DESC
LIMIT 5;

## 🙋‍♂️ Author
Melvin Moses M.
