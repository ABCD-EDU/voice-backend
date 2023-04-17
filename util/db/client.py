import MySQLdb
import os
from dotenv import load_dotenv
load_dotenv()

connection = MySQLdb.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
)


def get_db():
    return connection
