import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

# Connect without specifying a database to allow creating it
connection = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "")
)

try:
    with connection.cursor() as cursor:
        with open("database/schema.sql", "r") as f:
            sql_script = f.read()
            
        # Split script by semicolon to execute commands one by one
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        connection.commit()
    print("✅ Database and tables created successfully!")
except Exception as e:
    print(f"❌ Error creating database: {e}")
finally:
    connection.close()