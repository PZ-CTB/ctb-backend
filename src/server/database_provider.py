import sqlite3
import os

from constants import PATHS

def getDatabaseConnection():
    return sqlite3.connect(PATHS.DATABASE)

def loadDefaultDataToDatabase():
    pass

def initDatabase():
    if not os.path.exists(PATHS.DATABASE):
        connection = getDatabaseConnection()
        cursor = connection.cursor()
        with open(PATHS.DATABASE_SCHEMA) as f:
            cursor.executescript(f.read())
        with open(PATHS.DATABASE_DEFAULT_DUMP) as f:
            cursor.executescript(f.read())
        cursor.close()
        connection.commit()
        connection.close()
            
initDatabase()