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
