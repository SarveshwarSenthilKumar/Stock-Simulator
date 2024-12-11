import sqlite3
import os

database = open('tickets.db', 'w')
database.truncate(0)  
database.close()
connection = sqlite3.connect("tickets.db")
crsr = connection.cursor()
crsr.execute("CREATE TABLE tickets (id INTEGER, noTickets, holder, type, used, PRIMARY KEY(id))")
connection.commit()
crsr.close()
connection.close()

