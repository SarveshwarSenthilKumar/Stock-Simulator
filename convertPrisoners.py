import random
from sql import *

suitsLawyers=[]
with open('lawyers.txt') as lawyers:
    for lawyer in lawyers:
        suitsLawyers.append(lawyer.strip())

with open('prisoners.txt') as prisoners:
    for prisoner in prisoners:
        lawyerChosen=suitsLawyers[random.randint(0,len(suitsLawyers)-1)]
        prisonerDetails=prisoner.strip().split(",")

        for detail in prisonerDetails:
            if prisonerDetails[prisonerDetails.index(detail)][0] == " ":
                prisonerDetails[prisonerDetails.index(detail)-1]+="," + prisonerDetails[prisonerDetails.index(detail)]
                prisonerDetails.remove(detail)

        fullName = prisonerDetails[0]
        sentence = prisonerDetails[1]
        languagesSpoken = prisonerDetails[-1]
        gender = prisonerDetails[-2]
        age = prisonerDetails[-3]
        location = prisonerDetails[-4]
        description = prisonerDetails[-5]
        
        db = SQL("sqlite:///prisoners.db")
        db.execute("INSERT INTO prisoners (name, prisonsentence, description, origin, age, gender, languages, attorney) VALUES (?,?,?,?,?,?,?,?)", fullName, sentence, description, location, age, gender, languagesSpoken, lawyerChosen)
