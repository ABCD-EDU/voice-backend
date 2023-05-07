import MySQLdb
import os
from dotenv import load_dotenv
load_dotenv()

connection = MySQLdb.connect(
    host=os.getenv("LOCAL_DB_HOST"),
    user=os.getenv("LOCAL_DB_USERNAME"),
    passwd=os.getenv("LOCAL_DB_PASSWORD"),
    db=os.getenv("LOCAL_DB_NAME"),
)


def get_db():
    return connection
