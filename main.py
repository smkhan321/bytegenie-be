from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields, Namespace
from flask_mysqldb import MySQL
import requests
import os
from flask_cors import CORS
import sqlparse
import re

# Set up the Flask app
app = Flask(__name__)
CORS(app)
api = Api(app, version='1.0', title='Event Company People API',
          description='AI base system for query generation and fetching data using that query from SQL database.',
          )
# Configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'Musab'
app.config['MYSQL_PASSWORD'] = 'rajpoot123'
app.config['MYSQL_DB'] = 'EventCompanyPeople'
mysql = MySQL(app)
# Set your Hugging Face API Token
os.environ['HF_TOKEN'] = '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'
# API models for documentation
query_model = api.model('Query', {
    'question': fields.String(required=True, description='The question to generate SQL query for',
                              default='Find me companies in Financial Services sector.')
})
query_namespace = Namespace('Query Generation API', description='Click here to see query generation api.')

api.add_namespace(query_namespace)


def extract_query(query_text):
    pattern = r"\[SQL\](.*?)\[/SQL\]"
    match = re.search(pattern, query_text, re.DOTALL)
    sql_query = ''
    if match:
        sql_query = match.group(1).strip()
    else:
        print("No SQL query found between the tags.")
    return sql_query


# Helper function to execute query
def execute_query(query):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute(query)
        column_names = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        return results, column_names
    except Exception as e:
        print(e)
        return [], []


# Function to generate SQL query
def query_generator(question):
    # Prepare the joins information
    #     join_info = """
    #     Events and company data can be merged using ‘event_url’ column.
    #     Company and people data can be merged using ‘homepage_base_url’ column.
    #     Each event_url corresponds to a unique event, and each homepage_base_url can be interpreted as a unique company.
    #     """
    #     template = f"""Generate a SQL query max 50 words limit:
    #     I have only 3 tables name as people, Event and Company make sure to use these 3 tables only
    #     Metadat:
    #     table_name,column_name,data_type
    # people,first_name,TEXT
    # people,middle_name,TEXT
    # people,last_name,TEXT
    # people,job_title,TEXT
    # people,person_city,TEXT
    # people,person_state,TEXT
    # people,person_country,TEXT
    # people,email_pattern,TEXT
    # people,homepage_base_url,VARCHAR(255)
    # people,duration_in_current_job,TEXT
    # people,duration_in_current_company,TEXT
    # people,email,TEXT
    # Event,event_logo_url,TEXT
    # Event,event_name,TEXT
    # Event,event_start_date,DATE
    # Event,event_end_date,DATE
    # Event,event_venue,TEXT
    # Event,event_country,TEXT
    # Event,event_description,TEXT
    # Event,event_url,VARCHAR(255)
    # Company,company_logo_url,TEXT
    # Company,company_logo_text,TEXT
    # Company,company_name,TEXT
    # Company,relation_to_event,TEXT
    # Company,event_url,TEXT
    # Company,company_revenue,REAL
    # Company,n_employees,TEXT
    # Company,company_phone,TEXT
    # Company,company_founding_year,REAL
    # Company,company_address,TEXT
    # Company,company_industry,TEXT
    # Company,company_overview,TEXT
    # Company,homepage_url,TEXT
    # Company,linkedin_company_url,TEXT
    # Company,homepage_base_url,VARCHAR(255)
    # Company,company_logo_url_on_event_page,TEXT
    # Company,company_logo_match_flag,TEXT
    #
    #     Here is the schema details of my database:
    #     Scheme:[
    #     TABLE people (
    #     People first_name TEXT NOT NULL,
    #     People middle_name TEXT NULL,
    #     People last_name TEXT NULL,
    #     People job_title TEXT NULL,
    #     People person_city TEXT NULL,
    #     People person_state TEXT NULL,
    #     People person_country TEXT NULL,
    #     People email_pattern TEXT NULL,
    #     People homepage_base_url VARCHAR(255) NOT NULL,
    #     People duration_in_current_job TEXT NULL,
    #     People duration_in_current_company TEXT NULL,
    #     People email TEXT NULL
    #     );
    #     TABLE Event (
    #     Event event_logo_url TEXT NULL,
    #     Event event_name TEXT  NULL,
    #     Event event_start_date DATE  NULL,
    #     Event event_end_date DATE NULL,
    #     Event event_venue TEXT NULL,
    #     Event event_country TEXT NULL,
    #     Event event_description TEXT NULL,
    #     Event event_url VARCHAR(255) NOT NULL
    #     );
    #     TABLE Company (
    #     Company company_logo_url text null,
    #     Company company_logo_text TEXT NULL,
    #     Company company_name TEXT NULL,
    #     Company relation_to_event TEXT NULL,
    #     Company event_url TEXT NULL,
    #     Company company_revenue REAL NULL,
    #     Company n_employees TEXT NULL,
    #     Company company_phone TEXT NULL,
    #     Company company_founding_year REAL NULL,
    #     Company company_address TEXT NULL,
    #     Company company_industry TEXT NULL,
    #     Company company_overview TEXT NULL,
    #     Company homepage_url TEXT NULL,
    #     Company linkedin_company_url TEXT NULL,
    #     Company homepage_base_url VARCHAR(255) NOT NULL,
    #     Company company_logo_url_on_event_page TEXT NULL,
    #     Company company_logo_match_flag TEXT NULL
    #     );
    #     ]
    #     Make sure to write column name in small alphabet.Use DATE_ADD instead of DATEADD and Maximum length of query should
    #      be 50 to 100 words.The tables can be joined using the following information
    #     use join query only if required:
    #     {join_info}
    #     The question to answer is: {question}.
    #     Output only the simple SQL query:
    #     """
    # - company
    # relation_to_event
    # column
    # values
    # are: partner, sponsor, exhibitor, associate, expert, organizer, speaker, attendee.
    template = f"""### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Instructions
- Don't give any note or text at the end only give query.
- If you cannot answer the question with the available database schema
- I have only 3 tables name as people, Event and Company make sure to use these 3 tables only
- Use DATE_ADD instead of DATEADD.

### Database Schema
This query will run on a database whose schema is represented in this string:
   CREATE TABLE people (
    People first_name TEXT NOT NULL,
    People middle_name TEXT NULL,
    People last_name TEXT NULL,
    People job_title TEXT NULL,
    People person_city TEXT NULL,
    People person_state TEXT NULL,
    People person_country TEXT NULL,
    People email_pattern TEXT NULL,
    People homepage_base_url VARCHAR(255) NOT NULL,
    People duration_in_current_job TEXT NULL,
    People duration_in_current_company TEXT NULL,
    People email TEXT NULL
    );
    CREATE TABLE Event (
    Event event_logo_url TEXT NULL,
    Event event_name TEXT  NULL,
    Event event_start_date DATE  NULL,
    Event event_end_date DATE NULL,
    Event event_venue TEXT NULL,
    Event event_country TEXT NULL,
    Event event_description TEXT NULL,
    Event event_url VARCHAR(255) NOT NULL
    );
    CREATE TABLE Company (
    Company company_logo_url text null,
    Company company_logo_text TEXT NULL,
    Company company_name TEXT NULL,
    Company relation_to_event TEXT NULL,
    Company event_url TEXT NULL,
    Company company_revenue REAL NULL,
    Company n_employees TEXT NULL,
    Company company_phone TEXT NULL,
    Company company_founding_year REAL NULL,
    Company company_address TEXT NULL,
    Company company_industry TEXT NULL,
    Company company_overview TEXT NULL,
    Company homepage_url TEXT NULL,
    Company linkedin_company_url TEXT NULL,
    Company homepage_base_url VARCHAR(255) NOT NULL,
    Company company_logo_url_on_event_page TEXT NULL,
    Company company_logo_match_flag TEXT NULL
    );

-- event.event_url can be joined with company.event_url.
-- company.homepage_base_url can be joined with people.homepage_base_url.
-- if you want to join people with company you have to join people with company on homepage_base_url and then company with event on event_url.
-- Each event_url corresponds to a unique event, and each homepage_base_url can be interpreted as a unique company.

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]
[SQL]

"""
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}
    payload = {"inputs": template, "parameters": {
        "max_new_tokens": 1024  # Adjust according to the API's parameter requirements
    }
               }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        output_query = response.json()[0]['generated_text']
        # print(output_query)
        # gen_query = extract_query(output_query)
        gen_query = sqlparse.format(output_query.split("[SQL]")[-1], reindent=True)
        return gen_query
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")


@api.route('/generate_query')
class QueryGenerator(Resource):
    @api.expect(query_model)
    def post(self):
        query=''
        data = request.json
        question = data['question']
        try:
            query = query_generator(question)
            print(query)
            results, column_names = execute_query(query)
            return jsonify({
                'status_code': 200,
                'query': query,
                'results': results,
                'column_names': column_names
            })
        except Exception as e:
            print(str(e))
            return {'query': query, 'error': str(e)}, 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
