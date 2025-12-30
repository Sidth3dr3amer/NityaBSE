import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_db():
    return psycopg2.connect(os.getenv('DATABASE_URL'))
