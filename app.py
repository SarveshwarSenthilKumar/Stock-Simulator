from tokenize import Pointfloat, group
from unittest import result
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from datetime import time
from datetime import date
from datetime import datetime
from collections import defaultdict
import hashlib
import re
from sql import *
import pytz
import yfinance

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

allowedChar = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'!#$%&()*+,./:;<=>?@[\]^_`{|}~ "

#stockname, stockprice, noStocks, transactionType, buyerID

def checkEmail(email):
   regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
   if(re.fullmatch(regex, email)):
    return True
   else:
    return False
   
def verifyName(name):
   names=name.split(" ")
   validName=""

   for name in names:
      invalidElement=any(character in name for character in allowedChar[63:])
      if invalidElement:
         return False, "Your name cannot contain any special elements!"
      if "-" in name:
         splitName=name.split("-")
         name=""
         for namePart in splitName:
            name+=namePart[0].upper()+namePart[1:]+"-"
         name=name[:-1]
      else:
         name=name[0].upper()+name[1:]
      validName+=name+" "
   
   return True, validName[:-1]

def checkUserPassword(username, password):

   if username.lower() in password.lower():
      return False, "Your password cannot contain your username!"
   if len(password)<8:
      return False, "Your password needs to be at least 8 characters!"
    
   for letter in username:
      if letter not in allowedChar:
         return False, "Your username may not contain any symbols or special characters!"
   
   if len(username)<8:
      return False, "Your password needs to be at least 8 characters!"
   
   hasUpper=False
   hasLower=False
   hasNumber=False

   for letter in password: 
      indexOfLetter = allowedChar.index(letter)
      if indexOfLetter < 25:   
         hasLower=True
      elif indexOfLetter < 51:
         hasUpper = True
      elif letter in allowedChar:
         hasNumber=True
      else:
         return False, "Your password may not contain any symbols or special characters!"
        
   if not hasUpper:
      return False, "Your password must contain at least one uppercase letter!"
   elif not hasLower:
      return False, "Your password must contain at least one lowercase letter!"
   elif not hasNumber:
      return False, "Your password must contain at least one uppercase letter!"
   else:
      return [True]

def hash(password):
   hashing_object = hashlib.sha256()
   hashing_object.update(password.encode())
   password = hashing_object.hexdigest()
   return password

@app.route("/")
def index():
   if not session.get("name"):
      return render_template("homePage.html")
   else:
      db = SQL("sqlite:///users.db")
      results = db.execute("SELECT * FROM users WHERE username = :username", username=session.get("name"))
      user = results[0]

      balance = (user["money"])
      value=balance

      db = SQL("sqlite:///transactions.db")
      transactions = db.execute("SELECT * FROM transactions WHERE buyerName = :buyerName AND stillHeld = :stillHeld", buyerName=session.get("name"), stillHeld=True)

      stocksOwned = {}

      for transaction in transactions:
         if transaction["stock"] not in stocksOwned:
            stocksOwned[transaction["stock"]] = 0
         if transaction["transactionType"] == "BUY":
            stocksOwned[transaction["stock"]] += transaction["amntStocks"]
         else:
            stocksOwned[transaction["stock"]] -= transaction["amntStocks"]

      for stock in stocksOwned.keys():
         amntShares=stocksOwned[stock]
         stock=yfinance.Ticker(stock)
         amountHeldInStock=stock.info["currentPrice"]*amntShares
         value+=amountHeldInStock

      comparator = int(user["setpoint"])
      valueDifference=0
      
      if (value-comparator) != 0:
         valueDifference=(value-comparator)/comparator*100
      value="${:,.2f}".format(value)
      balance="${:,.2f}".format(balance)
      return render_template("index.html", balance=balance, valueDifference=valueDifference, value=value, stocksOwned=stocksOwned)

@app.route("/signup", methods=["GET", "POST"])
def signup():
   if session.get("name"):
      return redirect("/")
   if request.method=="GET":
      return render_template("signUp.html")
    
   emailAddress = request.form.get("emailaddress").strip().lower()
   fullName = request.form.get("name").strip()
   username = request.form.get("username").strip().lower()
   password = request.form.get("password").strip()

   validName = verifyName(fullName)
   if not validName[0]:
      return render_template("signUp.html", error=validName[1])
   fullName = validName[1]

   db = SQL("sqlite:///users.db")
   results = db.execute("SELECT * FROM users WHERE username = :username", username=username)

   if len(results) != 0:
      return render_template("signUp.html", error="This username is already taken! Please select a different username!")
   if not checkEmail(emailAddress):
      return render_template("signUp.html", error="You have not entered a valid email address!")
   if len(checkUserPassword(username, password)) > 1:
      return render_template("signUp.html", error=checkUserPassword(username, password)[1])
   
   tz_NY = pytz.timezone('America/New_York') 
   now = datetime.now(tz_NY)
   dateJoined = now.strftime("%d/%m/%Y %H:%M:%S")
   
   startingMoney = 25000

   password = hash(password)
   
   db = SQL("sqlite:///users.db")
   db.execute("INSERT INTO users (username, password, emailaddress, name, money, dateJoined, setpoint) VALUES (?,?,?,?,?,?,?)", username, password, emailAddress, fullName, startingMoney, dateJoined, startingMoney)

   session["name"] = username
   
   return render_template("sentence.html", sentences=["You have successfully signed up for Sarveshwar Stock Simulator! Return to home page to start trading!"])

@app.route("/login", methods=["GET", "POST"])
def login():
   if session.get("name"):
      return redirect("/")
   if request.method == "GET":
      return render_template("login.html")
   else:
      username = request.form.get("username").strip().lower()
      password = request.form.get("password").strip()

      password = hash(password)

      db = SQL("sqlite:///users.db")
      users=db.execute("SELECT * FROM users WHERE username = :username", username=username)

      if len(users) == 0:
         return render_template("login.html", error="No account has been found with this username!")
      user = users[0]
      if user["password"] == password:
         session["name"] = username
         return redirect("/")

      return render_template("login.html", error="You have entered an incorrect password! Please try again!")
   
@app.route("/logout")
def logout():
   session["name"] = None
   return redirect("/login")

@app.route("/search")
def searchStock():
   if not session.get("name"):
      return redirect("/")
   
   query=request.args.get("query").strip().upper()
   stock=yfinance.Ticker(query)

   username=session.get("name")

   db = SQL("sqlite:///users.db")
   users=db.execute("SELECT * FROM users WHERE username = :username", username=username)
   user=users[0]

   balance=user["money"]

   stockInformation=stock.info
   try:
      previousClose=stockInformation["regularMarketPreviousClose"]
      currentPrice=stockInformation["currentPrice"]
   except:
      return render_template("sentence.html", sentences=["There is no information about this ticker! Please enter a valid ticker!"])

   db = SQL("sqlite:///transactions.db")
   transactions=db.execute("SELECT * FROM transactions WHERE buyerName = :username AND stillHeld = :stillHeld AND stock = :stock", username=username, stillHeld=True, stock=stockInformation["underlyingSymbol"])

   stockInformation["owned"] = 0
      
   for transaction in transactions:
      if transaction["transactionType"] == "BUY":
         stockInformation["owned"]+=transaction["amntStocks"]
      else:
         stockInformation["owned"]-=transaction["amntStocks"]

   priceChange=((currentPrice/previousClose))*100-100
   stockInformation["priceChange"]=priceChange

   stockInformation["max"]=int(balance/currentPrice)

   return render_template("displayStock.html", stockInfo=stockInformation)

@app.route("/sellstock")
def sellStock():
   if not session.get("name"):
      return redirect("/")
   
   username=session.get("name")

   symbol=request.args.get("symbol")
   numberOfShares=int(request.args.get("numberOfShares"))

   if numberOfShares<=0:
      return render_template("sentence.html", sentences=["You may not sell less than at least one share!"])

   db = SQL("sqlite:///users.db")
   users=db.execute("SELECT * FROM users WHERE username = :username", username=username)
   user=users[0]

   balance=user["money"]

   stock=yfinance.Ticker(symbol)
   currentPrice=stock.info["currentPrice"]

   amntOwned=0

   db = SQL("sqlite:///transactions.db")
   transactions=db.execute("SELECT * FROM transactions WHERE buyerName = :username AND stillHeld = :stillHeld AND stock = :stock", username=username, stillHeld=True, stock=symbol)

   for transaction in transactions:
      if transaction["transactionType"] == "BUY":
         amntOwned+=transaction["amntStocks"]
      else:
         amntOwned-=transaction["amntStocks"]
   
   if numberOfShares > amntOwned:
      return render_template("sentence.html", sentences=["You cannot sell more than you curruntly have! You may only sell up to " + str(amntOwned) + " shares of " + symbol])
   elif numberOfShares == amntOwned:
      db = SQL("sqlite:///transactions.db")
      db.execute("UPDATE transactions SET stillHeld = :stillHeld WHERE stock = :stock AND buyerName = :username", stillHeld=False, stock=symbol, username=username)

      tz_NY = pytz.timezone('America/New_York') 
      now = datetime.now(tz_NY)
      transactionTime = now.strftime("%d/%m/%Y %H:%M:%S")

      balance+=currentPrice*numberOfShares

      db = SQL("sqlite:///transactions.db")
      db.execute("INSERT INTO transactions (stock, amntStocks, stockPrice, transactionType, buyerName, transactionTime, stillHeld) VALUES (?,?,?,?,?,?,?)", symbol, numberOfShares, currentPrice, "SELL", username, transactionTime, False)

      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money WHERE username = :username", money=balance, username=username)

      return render_template("sentence.html", sentences=["You have successfully sold all(" + str(numberOfShares) + ") your shares of " + symbol + " at the price of $" + str(currentPrice) + " for a total transaction of " + "${:,.2f}".format(currentPrice*numberOfShares) + "$"])
   else:
      tz_NY = pytz.timezone('America/New_York') 
      now = datetime.now(tz_NY)
      transactionTime = now.strftime("%d/%m/%Y %H:%M:%S")

      balance+=currentPrice*numberOfShares

      db = SQL("sqlite:///transactions.db")
      db.execute("INSERT INTO transactions (stock, amntStocks, stockPrice, transactionType, buyerName, transactionTime, stillHeld) VALUES (?,?,?,?,?,?,?)", symbol, numberOfShares, currentPrice, "SELL", username, transactionTime, True)

      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET money = :money WHERE username = :username", money=balance, username=username)

      return render_template("sentence.html", sentences=["You have successfully sold " + str(numberOfShares) + " shares of " + symbol + " at the price of $" + str(currentPrice) + " for a total transaction of " + "${:,.2f}".format(currentPrice*numberOfShares) + "$"])


@app.route("/purchasestock")
def purchaseStock():
   if not session.get("name"):
      return redirect("/")
   
   username=session.get("name")

   symbol=request.args.get("symbol")
   numberOfShares=int(request.args.get("numberOfShares"))

   if numberOfShares<=0:
      return render_template("sentence.html", sentences=["You may not purchase less than at least one share!"])


   db = SQL("sqlite:///users.db")
   users=db.execute("SELECT * FROM users WHERE username = :username", username=username)
   user=users[0]

   balance=user["money"]

   stock=yfinance.Ticker(symbol)
   currentPrice=stock.info["currentPrice"]

   availableShares=int(balance/currentPrice)
   if numberOfShares>availableShares:
      return render_template("sentence.html", sentences=["You have insufficient funds for this purchase! You may only purchase up to " + str(availableShares) + " shares of " + symbol])
   
   balance-=currentPrice*numberOfShares

   tz_NY = pytz.timezone('America/New_York') 
   now = datetime.now(tz_NY)
   transactionTime = now.strftime("%d/%m/%Y %H:%M:%S")

   db = SQL("sqlite:///transactions.db")
   db.execute("INSERT INTO transactions (stock, amntStocks, stockPrice, transactionType, buyerName, transactionTime, stillHeld) VALUES (?,?,?,?,?,?,?)", symbol, numberOfShares, currentPrice, "BUY", username, transactionTime, True)

   db = SQL("sqlite:///users.db")
   db.execute("UPDATE users SET money = :money WHERE username = :username", money=balance, username=username)

   amountSpent=currentPrice*numberOfShares

   return render_template("sentence.html", sentences=["You have successfully bought " + str(numberOfShares) + " shares of " + symbol + " at the price of $" + str(currentPrice) + " for a total buyout of " + "${:,.2f}".format(amountSpent) + "$"])

@app.route("/setpoint")
def setpoint():
   referencePoint=request.args.get("referencePoint")
   if not session.get("name"):
      return redirect("/")
   username=session.get("name")

   if not referencePoint:
      db = SQL("sqlite:///users.db")
      user=db.execute("SELECT * FROM users WHERE username = :username", username=username)[0]

      currentBalance = user["money"]

      db = SQL("sqlite:///transactions.db")
      transactions = db.execute("SELECT * FROM transactions WHERE buyerName = :buyerName AND stillHeld = :stillHeld", buyerName=session.get("name"), stillHeld=True)

      stocksOwned = {}

      for transaction in transactions:
         if transaction["stock"] not in stocksOwned:
            stocksOwned[transaction["stock"]] = 0
         if transaction["transactionType"] == "BUY":
            stocksOwned[transaction["stock"]] += transaction["amntStocks"]
         else:
            stocksOwned[transaction["stock"]] -= transaction["amntStocks"]

      for stock in stocksOwned.keys():
         amntShares=stocksOwned[stock]
         stock=yfinance.Ticker(stock)
         amountHeldInStock=stock.info["currentPrice"]*amntShares
         currentBalance+=amountHeldInStock
      

      newReferencePoint = currentBalance

      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET setpoint = :setpoint WHERE username = :username", setpoint=newReferencePoint, username=username)

   else:
      newReferencePoint=int(referencePoint)
      db = SQL("sqlite:///users.db")
      db.execute("UPDATE users SET setpoint = :setpoint WHERE username = :username", setpoint=newReferencePoint, username=username)

   return render_template("sentence.html", sentences=["You have successfuly reset your reference point to " + "${:,.2f}".format(newReferencePoint)])

@app.route("/viewtransactions")
def viewTransactions():
   if not session.get("name"):
      return redirect("/")
   username=session.get("name")
   db = SQL("sqlite:///transactions.db")
   transactions=db.execute("SELECT * FROM transactions where buyerName = :username", username=username)

   transactions=transactions[::-1]

   if len(transactions) == 0:
      return render_template("sentence.html", sentences=["You have not made any transactions yet!"])
   
   return render_template("viewTransactions.html", transactions=transactions)
