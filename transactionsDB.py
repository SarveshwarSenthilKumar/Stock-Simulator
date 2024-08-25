import sqlite3
import os

database = open('transactions.db', 'w')
database.truncate(0)  
database.close()
connection = sqlite3.connect("transactions.db")
crsr = connection.cursor()
crsr.execute("CREATE TABLE transactions (id INTEGER, stock NOT NULL, amntStocks NOT NULL, stockPrice, transactionType, buyerName, transactionTime, stillHeld, PRIMARY KEY(id))")
connection.commit()
crsr.close()
connection.close()

