import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_mercor_schema():
    # Get database connection parameters
    db_params = {
        'host': os.getenv('POSTGRES_SERVER'),
        'database': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }

    # Validate parameters
    if not all(db_params.values()):
        print("Error: Missing PostgreSQL connection parameters in .env file.")
        return

    try:
        # Connect to the database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        
        # Create a cursor
        cur = conn.cursor()
        
        # Check if schema exists
        cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'mercor')")
        schema_exists = cur.fetchone()[0]
        
        if not schema_exists:
            # Create the Mercor schema
            cur.execute('CREATE SCHEMA mercor')
            print("Mercor schema created successfully.")
        else:
            print("Mercor schema already exists.")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error creating Mercor schema: {e}")

if __name__ == '__main__':
    create_mercor_schema()
