import sqlite3
import os

database = open('prisoners.db', 'w')
database.truncate(0)  
database.close()
connection = sqlite3.connect("prisoners.db")
crsr = connection.cursor()
crsr.execute("CREATE TABLE prisoners (id INTEGER, name NOT NULL, prisonSentence NOT NULL, description, origin, age, gender, languages, attorney, PRIMARY KEY(id))")
connection.commit()
crsr.close()
connection.close()

