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
      return False, "Your username needs to be at least 8 characters!"
   
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
   return render_template("homePage.html")

@app.route("/myaccount")
def myacc():
   if not session.get("name"):
      return redirect("/")
   db = SQL("sqlite:///users.db")
   user=db.execute("SELECT * FROM users WHERE name = :name", name=session.get("name"))[0]
   return render_template("digivisit.html", users=[user])

"""
@app.route("/viewall")
def viewall():
   if not session.get("name"):
      return redirect("/")
   db = SQL("sqlite:///prisoners.db")
   allPrisoners=db.execute("SELECT * FROM prisoners")
   
   return render_template("digivisit.html", results=allPrisoners)
"""

@app.route("/search")
def search():
   if not session.get("name"):
      return redirect("/")
   query=request.args.get("query")

   allRes=[]

   db = SQL("sqlite:///prisoners.db")
   results=db.execute("SELECT * FROM prisoners")

   if query.lower().strip() == "all":
      return render_template("digivisit.html", results=results)

   for result in results:
      if query.isnumeric():
         if int(query) == result["id"]:
            allRes.append(result)
      elif query.lower() in result["name"].lower():
         allRes.append(result)
      elif query.lower() in result["prisonSentence"].lower():
         allRes.append(result)
      elif query.lower() in result["description"].lower():
         allRes.append(result)
      elif query.lower() in result["origin"].lower():
         allRes.append(result)
      elif query.lower() in result["age"].lower():
         allRes.append(result)
      elif query.lower() in result["gender"].lower():
         allRes.append(result)
      elif query.lower() in result["languages"].lower():
         allRes.append(result)
      elif query.lower() in result["attorney"].lower():
         allRes.append(result)

   return render_template("digivisit.html", results=allRes)
   
@app.route("/gettickets")
def tickets():
   if not session.get("name"):
      return redirect("/signup")
   return render_template("tickets.html")

@app.route("/digivisit")
def digivisit():
   if not session.get("name"):
      return redirect("/")
   if request.method == "GET":
      return render_template("digivisit.html")

@app.route("/createprisoner", methods=["GET", "POST"])
def createprisoner():
   print(session.get("name"))
   if session.get("name") != "sarveshwar" and session.get("name") != "elijahrw":
      return redirect("/")
   else:
      if request.method == "GET":
         return render_template("createprisoner.html")
      else:
         name=request.form.get("name")
         prisonsentence=request.form.get("prison")
         description=request.form.get("description")
         origin=request.form.get("origin")
         age=request.form.get("age")
         gender=request.form.get("gender")
         languages=request.form.get("languages")
         attorney=request.form.get("attorney")

         db = SQL("sqlite:///prisoners.db")
         db.execute("INSERT INTO prisoners (name, prisonsentence, description, origin, age, gender, languages, attorney) VALUES (?,?,?,?,?,?,?,?)", name, prisonsentence, description, origin, age, gender, languages, attorney)

         return render_template("sentence.html", sentences=["You have successfully created a prisoner!"])



#Username: sarveshwar Password: Snakisle@2008
   
   
   
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

   password = hash(password)
   
   db = SQL("sqlite:///users.db")
   db.execute("INSERT INTO users (username, password, emailaddress, name, dateJoined) VALUES (?,?,?,?,?)", username, password, emailAddress, fullName, dateJoined)

   session["name"] = username
   
   return render_template("sentence.html", sentences=["You have successfully signed up for Snakisle Penitentiary! Return to home page to start viewing!"])

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

