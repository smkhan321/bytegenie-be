# ByteGenieTest API

This repository contains the backend API for the ByteGenieTest project, which processes raw event, company, and
people data to make it queryable via a Flask API. The API can generate SQL queries based on user questions, execute
these queries against a MySQL database, and return the results to the user. The API also includes a Swagger interface
for ease of use.

## Table of Contents

1. [Introduction](#introduction)
2. [Data Engineering and Processing](#data-engineering-and-processing)
3. [API Functionalities](#api-functionalities)
4. [API Response Overview](#api-response-overview)
5. [Key Challenges](#key-challenges)
6. [Future Improvements](#future-improvements)
7. [Setup and Installation](#setup-and-installation)
8. [Usage](#usage)

## Introduction

The ByteGenieTest API allows users to query event, company, and people data using natural language questions. The
API processes raw data from CSV files, performs necessary data cleaning and standardization, and stores it in a MySQL
database. Users can interact with the API to retrieve information by asking questions in plain English, which are then
converted to SQL queries using a large language model (LLM).

## Data Engineering and Processing

### Main Steps and Motivation

1. **Standardization of Column Names**: Column names in the raw data are standardized to lowercase and spaces are
   replaced with underscores for consistency.
2. **Data Type Conversion**: Certain columns, such as dates and revenue figures, are converted to appropriate data
   types (e.g., `datetime` and `float`) for better query performance and accuracy.
3. **Email Generation**: Emails are generated for people based on the provided email patterns and names using the
   following logic:
    - Replace placeholders like `[first]`, `[last]`, `[first_initial]`, and `[last_initial]` with actual values from the
      data.
4. **Revenue Conversion**: Company revenue values are standardized to numerical formats (e.g., converting '1M' to
   1,000,000).
5. **Data Insertion into MySQL**: The cleaned and processed data is inserted into a MySQL database with the appropriate
   schema.

### Example Scripts

- **Data Cleaning and Processing**:
  ```python
  import pandas as pd
  import mysql.connector
  import re
  # Read CSV files
  people_df = pd.read_csv('people_info.csv')
  events_df = pd.read_csv('event_info.csv')
  companies_df = pd.read_csv('company_info.csv')
  # Standardize column names
  people_df.columns = [col.strip().lower().replace(' ', '_') for col in people_df.columns]
  events_df.columns = [col.strip().lower().replace(' ', '_') for col in events_df.columns]
  companies_df.columns = [col.strip().lower().replace(' ', '_') for col in companies_df.columns]
  # Convert data types
  events_df['event_start_date'] = pd.to_datetime(events_df['event_start_date'])
  events_df['event_end_date'] = pd.to_datetime(events_df['event_end_date'])
  def convert_revenue(revenue):
      if pd.isna(revenue):
          return None
      revenue = revenue.strip().upper()
      if 'M' in revenue:
          return float(re.sub(r'[^\d.]', '', revenue)) * 1e6
      elif 'B' in revenue:
          return float(re.sub(r'[^\d.]', '', revenue)) * 1e9
      elif 'K' in revenue:
          return float(re.sub(r'[^\d.]', '', revenue)) * 1e3
      else:
          return float(re.sub(r'[^\d.]', '', revenue))
  def create_email(row):
      email_pattern = row['email_pattern']
      first_name = row['first_name']
      last_name = row['last_name']
      homepage_base_url = row['homepage_base_url']
      if pd.notna(email_pattern) and pd.notna(first_name) and pd.notna(last_name) and pd.notna(homepage_base_url):
          first_initial = first_name[0]
          last_initial = last_name[0]
          email = email_pattern.replace('[first]', first_name)\
                              .replace('[last]', last_name)\
                              .replace('[first_initial]', first_initial)\
                              .replace('[last_initial]', last_initial)
          email += f"@{homepage_base_url}"
          return email
      return None
  people_df['email'] = people_df.apply(create_email, axis=1)
  companies_df['company_revenue'] = companies_df['company_revenue'].apply(convert_revenue)
  # Connect to MySQL and insert data
  conn = mysql.connector.connect(
      host='localhost',
      user='your_mysql_username',
      password='your_mysql_password',
      database='EventCompanyPeople'
  )
  cursor = conn.cursor()
  people_df.to_sql('People', conn, if_exists='replace', index=False)
  events_df.to_sql('Event', conn, if_exists='replace', index=False)
  companies_df.to_sql('Company', conn, if_exists='replace', index=False)
  conn.commit()
  conn.close()
  ```

## API Functionalities

The main functionalities of the API are as follows:

1. **Question to SQL Query Conversion**: Converts user questions into SQL queries using the Hugging Face LLM Model *
   *mistralai/Mistral-7B-Instruct-v0.1**.
2. **SQL Query Execution**: Executes the generated SQL queries against the MySQL database and retrieves the results.
3. **Result Return**: Returns the query results to the user in a JSON format.
4. **Swagger Interface**: Provides an interactive Swagger interface for easy API exploration and testing.

### Example Endpoints

- **Generate Query**:
    - Endpoint: **'/generate_query'**
    - Method: **'POST'**
    - Request Body:
  ```json
  {
  "question": "Find me companies that are in the Financial Service Sector"
  }
  ```
    - Response:
  ```json
  {
  "column_names": [
    "company_logo_url",
    "company_logo_text",
    "company_name",
    "relation_to_event",
    "event_url",
    "company_revenue",
    "n_employees",
    "company_phone",
    "company_founding_year",
    "company_address",
    "company_industry",
    "company_overview",
    "homepage_url",
    "linkedin_company_url",
    "homepage_base_url",
    "company_logo_url_on_event_page",
    "company_logo_match_flag"
  ],
  "query": "SELECT * FROM Company\n    WHERE company_industry = 'Financial Services'\n    ORDER BY company_name ASC;",
  "results": [
    [
      "https://d1hbpr09pwz0sk.cloudfront.net/logo_url/100-women-in-finance-6a062f47",
      "Women in Finance",
      "100 Women In Finance",
      "partner",
      "https://apac.commoditytradingweek.com/",
      null,
      "11-50",
      null,
      2001,
      null,
      "Financial Services",
      "100 Women in Finance strengthens the global finance industry by empowering women to achieve their professional potential at each career stage. Its members inspire, equip and advocate for a new generation of industry leadership, in which women and men serve as investment professionals and executives, equal in achievement and impact. Through Education, Peer Engagement and Impact, the organization furthers the progress of women who have chosen finance as a career, and enables their positive influence over pre-career young women.",
      "https://100women.org/events/",
      "https://www.linkedin.com/company/100-women-in-finance/about",
      "100women.org",
      "https://apac.commoditytradingweek.com/wp-content/uploads/2022/03/100wif_web-1.png",
      "yes"
    ],
    [
      "https://media.licdn.com/dms/image/C4E0BAQGKgXIlmfps_w/company-logo_200_200/0/1630605312325/accelya_kale_consultants_limited_logo?e=1727308800&v=beta&t=Gh4Er-mDBFk64FTwHg7p62CSygPO4wbz_WHWUei_pyw",
      "accelya",
      "Accelya Group",
      "sponsor",
      "https://www.terrapinn.com/exhibition/aviation-festival-asia/index.stm",
      34000000,
      "1,001-5,000 employees",
      "(305) 552-6094",
      1976,
      "Modi House Eastern Express Hwy Naupada Fl 3, Mumbai, Maharashtra 400602, IN",
      "Financial Services",
      "Accelya Kale Consultants Limited is an electrical/electronic manufacturing company based out of 3rd Floor Modi House Eastern Express Highway Naupada West, Mumbai, Maharashtra, India.",
      "https://w3.accelya.com",
      "https://in.linkedin.com/company/accelya-limited/about",
      "accelya.com",
      "https://terrapinn-cdn.com/tres/pa-images/10759/a0AN20000050gFiMAI_org.jpg?20240104150021",
      "yes"
    ]
  ],
  "status_code": 200
   }
  ```
## API Response Overview
The API response provides details about companies in the Financial Services industry that are related to various events. The response includes the column names, the SQL query used to fetch the data, and the results. The results contain data coming from SQL database.
### Column Names ('columns_names')
Columns Names are basically header of table that we will display on UI side.
### SQL Query ('query')
This is the SQL query generated by our LLM model and this query will be executed to get data from the Database.
```SQL
SELECT * FROM Company
WHERE company_industry = 'Financial Services'
ORDER BY company_name ASC;
```
### Results ('results')
The results field contains an array of arrays, where each inner array represents a company's details. Each inner array contains values corresponding to the column names listed above.
### Status Code ('status_code')
The **'status_code'** field indicates the HTTP status code of the response. In this case, it is **'200'**, meaning the request was successful.
## Key Challenges
1. **Data Cleaning and Standardization**: Ensuring that the raw data is cleaned and standardized correctly to avoid any issues during querying.
2. **Query Generation Accuracy**: Ensuring the generated SQL queries accurately reflect the user's intent and the structure of the database.
3. **Database Integration**: Efficiently integrating the processed data into the MySQL database and ensuring seamless querying and retrieval.
4. **Performance Optimization**: Handling potentially large datasets and ensuring the API responds promptly to user queries.
## Future Improvements
1. **Enhanced Data Processing**: Further standardizing and enriching the data using additional LLM models to derive more insightful features.
2. **Improved Query Generation**: Enhancing the LLM prompt engineering to generate more accurate and efficient SQL queries.
3. **Scalability**: Optimizing the database and API architecture to handle larger volumes of data and concurrent user requests.
4. **Additional Features**: Adding more endpoints and functionalities, such as user authentication, advanced filtering options, and detailed analytics.
## Setup and Installation
### Prerequisites
- Python 3.9+
- MySQL Server OR MySQL Workbench
- Pip
### Installation Steps
1. **Clone the Repository**:
```bash
git clone https://github.com/yourusername/ByteGenieTest.git
```
2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```
3. **Set Up MySQL Database**:
```SQL
CREATE DATABASE EventCompanyPeople;
USE EventCompanyPeople;
CREATE TABLE People (
    first_name TEXT NOT NULL,
    middle_name TEXT NULL,
    last_name TEXT NULL,
    job_title TEXT NULL,
    person_city TEXT NULL,
    person_state TEXT NULL,
    person_country TEXT NULL,
    email_pattern TEXT NULL,
    homepage_base_url VARCHAR(255) NOT NULL,
    duration_in_current_job TEXT NULL,
    duration_in_current_company TEXT NULL,
    email TEXT NULL
);
CREATE TABLE Event (
    event_logo_url TEXT NULL,
    event_name TEXT  NULL,
    event_start_date DATE  NULL,
    event_end_date DATE NULL,
    event_venue TEXT NULL,
    event_country TEXT NULL,
    event_description TEXT NULL,
    event_url VARCHAR(255) NOT NULL
);
CREATE TABLE Company (
    company_logo_url text null,
    company_logo_text TEXT NULL,
    company_name TEXT NULL,
    relation_to_event TEXT NULL,
    event_url TEXT NULL,
    company_revenue REAL NULL,
    n_employees TEXT NULL,
    company_phone TEXT NULL,
    company_founding_year REAL NULL,
    company_address TEXT NULL,
    company_industry TEXT NULL,
    company_overview TEXT NULL,
    homepage_url TEXT NULL,
    linkedin_company_url TEXT NULL,
    homepage_base_url VARCHAR(255) NOT NULL,
    company_logo_url_on_event_page TEXT NULL,
    company_logo_match_flag TEXT NULL
);
```
### Example Script for insert data into DataBase
```python
import pandas as pd
from mysql.connector import connection, Error


# Function to insert data from a CSV file into a MySQL table
def insert_data_from_csv(file_path, table_name, user, password, host, database):
    try:
        # Connect to the MySQL server
        conn = connection.MySQLConnection(
            user=user,
            password=password,
            host=host,
            database=database
        )

        # Read the CSV file into a DataFrame
        data = pd.read_csv(file_path)

        # Create a cursor object
        cursor = conn.cursor()

        # Get column names from the DataFrame
        columns = ', '.join(data.columns)

        # Insert each row of the DataFrame into the table
        for index, row in data.iterrows():
            # Create a list of values for each row
            values = tuple(row)

            # Generate a placeholder string for the values
            placeholders = ', '.join(['%s'] * len(values))

            # Create the SQL insert statement
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            # Execute the insert statement
            cursor.execute(sql, values)

        # Commit the transaction
        conn.commit()

        print("Data inserted successfully")

    except Error as e:
        print(f"Error: {e}")

    finally:
        # Close the cursor and connection
        if conn.is_connected():
            cursor.close()
            conn.close()


# Define parameters
file_path = 'data/companies.csv'
table_name = 'company'
user = 'Musab'
password = 'rajpoot123'
host = 'localhost'
database = 'eventcompanypeople'

# Insert data from CSV to MySQL table
insert_data_from_csv(file_path, table_name, user, password, host, database)
```
4. **Data Dump**:
I have created a SQL Database Dump inside database Folder you can take that file to dump data into sql also i have csv files data inside data folder

```bash
cd ByteGenieTest\data
cd ByteGenieTest\Database
```
here you will find three files compaines.csv, events.csv, people.csv.
These files contain the clean and process data you can upload it into your sql database tables.
5. **Set Up Environment Variables**:
Add these credential into main file of project
```python
# Setup MySQL Connection
app.config['MYSQL_HOST'] = 'localhost'
# I have set this username and password into mySQL Workbench
app.config['MYSQL_USER'] = '*****'
app.config['MYSQL_PASSWORD'] = '*****'
app.config['MYSQL_DB'] = 'EventCompanyPeople'

#Set your Hugging Face API Token
os.environ['HF_TOKEN'] = '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'
```
6. **Run the Application**
```bash
python main.py
```
## Usage
Access the Swagger interface at '**http://127.0.0.1:5000**' to test the API endpoints you can also edit the url from main.py file.
```python
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
```
here in host you can define url.
