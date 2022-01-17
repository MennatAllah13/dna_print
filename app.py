import csv
import io
import re

import matplotlib.pyplot as plt
import MySQLdb.cursors
import numpy as np
import pandas as pd
import skfuzzy as fuzz
import sklearn.metrics as metrics
from flask import Flask, render_template, request, session
from flask_mysqldb import MySQL
from skfuzzy import control as ctrl
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.utils import shuffle

app = Flask(__name__)

app.config["DEBUG"] = True

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dna'

mysql = MySQL(app)

UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
@app.route('/home')
def home():
    return render_template('Home.html')


@app.route('/sign')
def sign():
    return render_template('SignUp.html')


@app.route('/SignUp', methods=['GET', 'POST'])
def SignUp():

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST' and 'Fname' in request.form and 'Sname' in request.form and 'Email' in request.form and 'Phone' in request.form and 'password' in request.form and 'age' in request.form:
        FirstName = request.form['Fname']
        LastName = request.form['Sname']
        email = request.form['Email']
        phone = request.form['Phone']
        password = request.form['password']
        cpassword = request.form['password2']
        age = request.form['age']
        gender = request.form['gender']

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'

            return render_template('SignUp.html', msg=msg)

        elif re.match(r'[^@]+@[^@]+\.[^@]+', email):
            cursor.execute('SELECT * FROM user WHERE email = % s', (email))
            account = cursor.fetchone()

            if account:
                msg = 'Account already exists !'
                return render_template('SignUp.html', msg=msg)

            elif not re.match(r'[A-Za-z]+', FirstName):
                msg = 'First Name must contain only characters and numbers !'
                return render_template('SignUp.html', msg=msg)

            elif not re.match(r'[A-Za-z]+', LastName):
                msg = 'Last Name must contain only characters and numbers !'
                return render_template('SignUp.html', msg=msg)

            elif password != cpassword:
                msg = 'Password and confirm password should have the same value !'
                return render_template('SignUp.html', msg=msg)

            elif not FirstName or not LastName or not password or not email:
                msg = 'Please fill out the form !'
                return render_template('SignUp.html', msg=msg)

            else:
                cursor.execute('INSERT INTO user (FirstName, LastName, gender, password, email, phone, age, usertype_id) VALUES (% s, % s, % s, % s, % s, % s, % s, % s)',
                               (FirstName, LastName, gender, password, email, phone, age, 3))

                msg = 'You have successfully registered !'
                return render_template('Home.html', msg)

    elif request.method == 'POST':
        msg = 'Please fill out the form !'
        return render_template('SignUp.html', msg)


@app.route('/signIn')
def log():
    return render_template('SignIn.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST' and 'Email' in request.form and 'password' in request.form:
        email = request.form['Email']
        password = request.form['password']
        cursor.execute(
            'SELECT * FROM user WHERE email = % s AND password = % s', (email, password))
        result = cursor.fetchone()
        print("all : ", result)
        if result:
            session['loggedin'] = True
            session['id'] = result['id']
            session['FName'] = result['FirstName']
            session['LName'] = result['LastName']
            session['gender'] = result['gender']
            session['phone'] = result['phone']
            session['age'] = result['age']
            session['type'] = result['usertype_id']
            session['email'] = email

            if session['type'] == 1:
                session['user'] = "Admin"
                return render_template('AdminProfile.html', info={session['FName'], session['LName'], session['gender'], session['age'], session['phone'], session['email'], session['user']})
            elif session['type'] == 2:
                session['user'] = "Doctor"
                return render_template('DoctorProfile.html', info={session['FName'], session['LName'], session['gender'], session['age'], session['phone'], session['email'], session['user']})
            elif session['type'] == 3:
                session['user'] = "Client"
                return render_template('ClientProfile.html', info={session['FName'], session['LName'], session['gender'], session['age'], session['phone'], session['email'], session['user']})
        else:
            return render_template('SignIn.html')
    else:
        return render_template('SignIn.html')


@app.route('/admin')
def admin():
    return render_template('AdminProfile.html')


@app.route('/doctor')
def doctor():
    return render_template('DoctorProfile.html')


@app.route('/client')
def client():
    return render_template('ClientProfile.html')


@app.route('/logout')
def Logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return render_template('Home.html')


@app.route('/upload')
def upload():
    return render_template('UploadSample.html')


@app.route('/UploadSample', methods=['GET', 'POST'])
def uploadSample():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST' and 'client_id' in request.form and 'file' in request.files:
        clientID = request.form['client_id']

        f = request.files['file']
        stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)

        for row in csv_input:
            PHV_status = row[0]
            PPARA = row[1]
            NOS3 = row[2]
            COL1A1 = row[3]
            VDR = row[4]
            ACTN3 = row[5]
            BDNF = row[6]
            COL5A1 = row[7]
            COL2A1 = row[8]
            AMPD1 = row[9]
            AGT = row[10]
            GDF5 = row[11]
            IGF2 = row[12]
            PPAR = row[13]
            ACE = row[14]
            UCP3 = row[15]
            weight = row[16]

        cursor.execute('INSERT into samples (client_id, PHV_status, weight, PPARA, NOS3, COL1A1, VDR, ACTN3, BDNF, COL5A1, COL2A1, AMPD1, AGT, GDF5, IGF2, PPARα, ACE, UCP3) VALUES (% s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s)',
                       (clientID, PHV_status, weight, PPARA, NOS3, COL1A1, VDR, ACTN3, BDNF, COL5A1, COL2A1, AMPD1, AGT, GDF5, IGF2, PPAR, ACE, UCP3))

        #fuzzyLogic(clientID, ACE, ACTN3, PPAR, VDR, COL5A1, AGT, PPARA, UCP3)

        A = AthleteOrNot()
        KI = KneeInjuries()
        AI = AnkleInjuries()

        return render_template('Report2.html', result=np.array([A, KI, AI]))
    else:
        return render_template('UploadSample.html')


@app.route('/AddDoctor', methods=['GET', 'POST'])
def AddDoctor():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST' and 'FirstName' in request.form and 'LastName' in request.form and 'email' in request.form and 'password' in request.form and 'age' in request.form:
        FirstName = request.form['FirstName']
        LastName = request.form['LastName']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']

        sql1 = 'SELECT * FROM user WHERE email = % s', (email)
        account = cursor.execute(sql1)

        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', FirstName):
            msg = 'First name must contain only characters and numbers !'
        elif not re.match(r'[A-Za-z0-9]+', LastName):
            msg = 'Last name must contain only characters and numbers !'
        elif not FirstName or not LastName or not password or not email:
            msg = 'Please fill out the form !'
        else:
            sql2 = 'INSERT INTO user (FirstName, LastName, gender, password, email, phone, usertype_id) VALUES (% s, % s, % s, % s, % s, % s, % s)', (
                FirstName, LastName, gender, password, email, phone, 2)
            cursor.execute(sql2)

            msg = 'Doctor is successfully added !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'

    return render_template('AddDoctor.html', msg=msg)


def Classification():
    AthleteOrNot()
    KneeInjuries()
    AnkleInjuries()


def AthleteOrNot():
    data = pd.read_csv(
        r'C:\Users\DELL\source\repos\FlaskWebProject6\FlaskWebProject6\FlaskWebProject6\static\Train1.csv', na_values="?")
    data = shuffle(data)

    z = data.drop(columns=["Athlete group"])
    x, y = z, data["Athlete group"]

    X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.3, random_state=0)

    gnb = GaussianNB()
    gnb.fit(X_train, y_train)
    nb = gnb.predict(X_test)
    print("Naive Bayes accuracy:", metrics.accuracy_score(y_test, nb))

    data2 = pd.read_csv(
        r'C:\Users\DELL\source\repos\FlaskWebProject6\FlaskWebProject6\FlaskWebProject6\static\Test.csv', na_values="?")

    data2 = data2.drop(columns=["GDF5", "IGF2", "PPAR", "ACE", "UCP3",
                       "Weight", "Ankle Injuries", "Knee Injuries", "Sample"])

    data2 = encoder(data2)

    status = gnb.predict(data2)

    if status == 1:
        return "Not Athlete"
    elif status == 2:
        return " an Athlete"


def KneeInjuries():
    data = pd.read_csv(
        r'C:\Users\DELL\source\repos\FlaskWebProject6\FlaskWebProject6\FlaskWebProject6\static\Train2.csv', na_values="?")
    data = data.fillna(0)

    z = data.drop(columns=["Knee Injuries"])
    x, y = z, data["Knee Injuries"]

    X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.3, random_state=0)

    svc = make_pipeline(StandardScaler(), SVC(gamma='auto'))
    svc.fit(X_train, y_train)
    sv = svc.predict(X_test)

    print('SVC accuracy:', round(accuracy_score(y_test, sv), 5))

    data2 = pd.read_csv(
        r'C:\Users\DELL\source\repos\FlaskWebProject6\FlaskWebProject6\FlaskWebProject6\static\Test.csv', na_values="?")

    data2 = data2.drop(columns=["PHV Status", "PPARA", "NOS3", "COL1A1", "VDR",
                       "ACTN3", "BDNF", "COL2A1", "AGT", "PPAR", "ACE", "UCP3", "Knee Injuries"])

    data2 = encoder(data2)

    status = svc.predict(data2)

    if status == 0:
        return "You don't have the possibility of having knee injuries"
    elif status == 1:
        return "You have the possibility of having knee injuries"


def AnkleInjuries():
    data = pd.read_csv(
        r'C:\Users\DELL\source\repos\FlaskWebProject6\FlaskWebProject6\FlaskWebProject6\static\Train2.csv', na_values="?")
    data = data.fillna(0)

    z = data.drop(columns=["Ankle Injuries"])
    x, y = z, data["Ankle Injuries"]

    X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.3, random_state=0)

    svc = make_pipeline(StandardScaler(), SVC(gamma='auto'))
    svc.fit(X_train, y_train)
    sv = svc.predict(X_test)

    print('SVC accuracy:', round(accuracy_score(y_test, sv), 5))

    data2 = pd.read_csv(
        r'C:\Users\DELL\source\repos\FlaskWebProject6\FlaskWebProject6\FlaskWebProject6\static\Test.csv', na_values="?")

    data2 = data2.drop(columns=["PHV Status", "PPARA", "NOS3", "COL1A1", "VDR",
                       "ACTN3", "BDNF", "COL2A1", "AGT", "PPAR", "ACE", "UCP3", "Ankle Injuries"])

    data2 = encoder(data2)

    status = svc.predict(data2)

    if status == 0:
        return "You don't have the possibility of having ankle injuries"
    elif status == 1:
        return "You have the possibility of having ankle injuries"


def fuzzyLogic(clientID, ace, actn3, ppar, vdr, col5a1, agt, ppara, ucp3):
    CS = CombatSports(ace, actn3, pparα)
    S = Soccer(actn3, vdr, col5a1)
    WL = Weightlifter(actn3, vdr, ace)
    BB = Bodybuilding(actn3, agt, ppara)
    R = Rowers(actn3, ace, ucp3)
    TF = Trackandfield(ace, actn3, pparα)

    #cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # cursor.execute('INSERT into sports (user_id, CombatSports, Soccer, Weightlifters, Bodybuilding, Rowers, TrackAndField)',
    # (clientID, CS, S, WL, BB, R, TF))


def CombatSports(ace, actn3, pparα):
    x = [0, 1, 2]

    ACE = ctrl.Antecedent(x, 'ACE')
    ACTN3 = ctrl.Antecedent(x, 'ACTN3')
    PPARα = ctrl.Antecedent(x, 'PPARα')

    ACE.automf(3)
    ACTN3.automf(3)
    PPARα.automf(3)

    Combat = ctrl.Consequent(np.arange(0, 100, 1), 'Combat')

    Combat['poor'] = fuzz.trimf(Combat.universe, [0, 30, 35])
    Combat['average'] = fuzz.trimf(Combat.universe, [35, 60, 70])
    Combat['good'] = fuzz.trimf(Combat.universe, [71, 80, 101])

    rule1 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      PPARα['good'], Combat['good'])
    rule2 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      PPARα['average'], Combat['good'])
    rule3 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      PPARα['poor'], Combat['good'])
    rule4 = ctrl.Rule(ACTN3['good'] & ACE['average']
                      & PPARα['good'], Combat['good'])
    rule5 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      PPARα['average'], Combat['average'])
    rule6 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      PPARα['poor'], Combat['average'])
    rule7 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      PPARα['good'], Combat['good'])
    rule8 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      PPARα['average'], Combat['average'])
    rule9 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      PPARα['poor'], Combat['average'])

    rule10 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & PPARα['good'], Combat['good'])
    rule11 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & PPARα['average'], Combat['average'])
    rule12 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & PPARα['poor'], Combat['average'])
    rule13 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & PPARα['good'], Combat['average'])
    rule14 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & PPARα['average'], Combat['average'])
    rule15 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & PPARα['poor'], Combat['average'])
    rule16 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & PPARα['good'], Combat['average'])
    rule17 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & PPARα['average'], Combat['average'])
    rule18 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & PPARα['poor'], Combat['poor'])

    rule19 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       PPARα['good'], Combat['good'])
    rule20 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       PPARα['average'], Combat['average'])
    rule21 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       PPARα['poor'], Combat['poor'])
    rule22 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & PPARα['good'], Combat['average'])
    rule23 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & PPARα['average'], Combat['average'])
    rule24 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & PPARα['poor'], Combat['poor'])
    rule25 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       PPARα['good'], Combat['average'])
    rule26 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       PPARα['average'], Combat['poor'])
    rule27 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       PPARα['poor'], Combat['poor'])

    Combat_Ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12,
                                     rule13, rule14, rule15, rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule27])
    combat = ctrl.ControlSystemSimulation(Combat_Ctrl)

    combat.input['ACE'] = ace
    combat.input['ACTN3'] = actn3
    combat.input['PPARα'] = pparα

    combat.compute()

    print(combat.output['Combat'])
    return combat.output['Combat']


def Soccer(actn3, vdr, col5a1):
    x = [0, 1, 2]

    ACTN3 = ctrl.Antecedent(x, 'ACTN3')
    VDR = ctrl.Antecedent(x, 'VDR')
    COL5A1 = ctrl.Antecedent(x, 'COL5A1')

    ACTN3.automf(3)
    VDR.automf(3)
    COL5A1.automf(3)

    Soccer = ctrl.Consequent(np.arange(0, 100, 1), 'Soccer')

    Soccer['poor'] = fuzz.trimf(Soccer.universe, [0, 30, 35])
    Soccer['average'] = fuzz.trimf(Soccer.universe, [35, 60, 70])
    Soccer['good'] = fuzz.trimf(Soccer.universe, [71, 80, 101])

    rule1 = ctrl.Rule(ACTN3['good'] & VDR['good'] &
                      COL5A1['good'], Soccer['good'])
    rule2 = ctrl.Rule(ACTN3['good'] & VDR['good'] &
                      COL5A1['average'], Soccer['good'])
    rule3 = ctrl.Rule(ACTN3['good'] & VDR['good'] &
                      COL5A1['poor'], Soccer['good'])
    rule4 = ctrl.Rule(ACTN3['good'] & VDR['average'] &
                      COL5A1['good'], Soccer['good'])
    rule5 = ctrl.Rule(ACTN3['good'] & VDR['average'] &
                      COL5A1['average'], Soccer['average'])
    rule6 = ctrl.Rule(ACTN3['good'] & VDR['average'] &
                      COL5A1['poor'], Soccer['average'])
    rule7 = ctrl.Rule(ACTN3['good'] & VDR['poor'] &
                      COL5A1['good'], Soccer['good'])
    rule8 = ctrl.Rule(ACTN3['good'] & VDR['poor'] &
                      COL5A1['average'], Soccer['average'])
    rule9 = ctrl.Rule(ACTN3['good'] & VDR['poor'] &
                      COL5A1['poor'], Soccer['average'])

    rule10 = ctrl.Rule(ACTN3['average'] & VDR['good']
                       & COL5A1['good'], Soccer['good'])
    rule11 = ctrl.Rule(ACTN3['average'] & VDR['good']
                       & COL5A1['average'], Soccer['average'])
    rule12 = ctrl.Rule(ACTN3['average'] & VDR['good']
                       & COL5A1['poor'], Soccer['average'])
    rule13 = ctrl.Rule(ACTN3['average'] & VDR['average']
                       & COL5A1['good'], Soccer['average'])
    rule14 = ctrl.Rule(ACTN3['average'] & VDR['average']
                       & COL5A1['average'], Soccer['average'])
    rule15 = ctrl.Rule(ACTN3['average'] & VDR['average']
                       & COL5A1['poor'], Soccer['average'])
    rule16 = ctrl.Rule(ACTN3['average'] & VDR['poor']
                       & COL5A1['good'], Soccer['average'])
    rule17 = ctrl.Rule(ACTN3['average'] & VDR['poor']
                       & COL5A1['average'], Soccer['average'])
    rule18 = ctrl.Rule(ACTN3['average'] & VDR['poor']
                       & COL5A1['poor'], Soccer['poor'])

    rule19 = ctrl.Rule(ACTN3['poor'] & VDR['good'] &
                       COL5A1['good'], Soccer['good'])
    rule20 = ctrl.Rule(ACTN3['poor'] & VDR['good'] &
                       COL5A1['average'], Soccer['average'])
    rule21 = ctrl.Rule(ACTN3['poor'] & VDR['good'] &
                       COL5A1['poor'], Soccer['poor'])
    rule22 = ctrl.Rule(ACTN3['poor'] & VDR['average']
                       & COL5A1['good'], Soccer['average'])
    rule23 = ctrl.Rule(ACTN3['poor'] & VDR['average']
                       & COL5A1['average'], Soccer['average'])
    rule24 = ctrl.Rule(ACTN3['poor'] & VDR['average']
                       & COL5A1['poor'], Soccer['poor'])
    rule25 = ctrl.Rule(ACTN3['poor'] & VDR['poor'] &
                       COL5A1['good'], Soccer['average'])
    rule26 = ctrl.Rule(ACTN3['poor'] & VDR['poor'] &
                       COL5A1['average'], Soccer['poor'])
    rule27 = ctrl.Rule(ACTN3['poor'] & VDR['poor'] &
                       COL5A1['poor'], Soccer['poor'])

    Soccer_Ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12,
                                     rule13, rule14, rule15, rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule27])
    Soccer = ctrl.ControlSystemSimulation(Soccer_Ctrl)

    Soccer.input['VDR'] = vdr
    Soccer.input['ACTN3'] = actn3
    Soccer.input['COL5A1'] = col5a1

    Soccer.compute()

    print(Soccer.output['Soccer'])


def Weightlifter(actn3, vdr, ace):
    x = [0, 1, 2]

    ACTN3 = ctrl.Antecedent(x, 'ACTN3')
    VDR = ctrl.Antecedent(x, 'VDR')
    ACE = ctrl.Antecedent(x, 'ACE')

    ACTN3.automf(3)
    VDR.automf(3)
    ACE.automf(3)

    Weightlifter = ctrl.Consequent(np.arange(0, 100, 1), 'Weightlifter')

    Weightlifter['poor'] = fuzz.trimf(Weightlifter.universe, [0, 30, 35])
    Weightlifter['average'] = fuzz.trimf(Weightlifter.universe, [35, 60, 70])
    Weightlifter['good'] = fuzz.trimf(Weightlifter.universe, [71, 80, 101])

    rule1 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      VDR['good'], Weightlifter['good'])
    rule2 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      VDR['average'], Weightlifter['good'])
    rule3 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      VDR['poor'], Weightlifter['good'])
    rule4 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      VDR['good'], Weightlifter['good'])
    rule5 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      VDR['average'], Weightlifter['average'])
    rule6 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      VDR['poor'], Weightlifter['average'])
    rule7 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      VDR['good'], Weightlifter['good'])
    rule8 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      VDR['average'], Weightlifter['average'])
    rule9 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      VDR['poor'], Weightlifter['average'])

    rule10 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & VDR['good'], Weightlifter['good'])
    rule11 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & VDR['average'], Weightlifter['average'])
    rule12 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & VDR['poor'], Weightlifter['average'])
    rule13 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & VDR['good'], Weightlifter['average'])
    rule14 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & VDR['average'], Weightlifter['average'])
    rule15 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & VDR['poor'], Weightlifter['average'])
    rule16 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & VDR['good'], Weightlifter['average'])
    rule17 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & VDR['average'], Weightlifter['average'])
    rule18 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & VDR['poor'], Weightlifter['poor'])

    rule19 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       VDR['good'], Weightlifter['good'])
    rule20 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       VDR['average'], Weightlifter['average'])
    rule21 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       VDR['poor'], Weightlifter['poor'])
    rule22 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & VDR['good'], Weightlifter['average'])
    rule23 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & VDR['average'], Weightlifter['average'])
    rule24 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & VDR['poor'], Weightlifter['poor'])
    rule25 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       VDR['good'], Weightlifter['average'])
    rule26 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       VDR['average'], Weightlifter['poor'])
    rule27 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       VDR['poor'], Weightlifter['poor'])

    Weightlifter_Ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12,
                                           rule13, rule14, rule15, rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule27])
    Weightlifter = ctrl.ControlSystemSimulation(Weightlifter_Ctrl)

    Weightlifter.input['VDR'] = vdr
    Weightlifter.input['ACTN3'] = actn3
    Weightlifter.input['ACE'] = ace

    Weightlifter.compute()

    print(Weightlifter.output['Weightlifter'])


def Bodybuilding(actn3, agt, ppara):
    x = [0, 1, 2]

    ACTN3 = ctrl.Antecedent(x, 'ACTN3')
    PPARA = ctrl.Antecedent(x, 'PPARA')
    AGT = ctrl.Antecedent(x, 'AGT')

    ACTN3.automf(3)
    PPARA.automf(3)
    AGT.automf(3)

    Bodybuilding = ctrl.Consequent(np.arange(0, 100, 1), 'Bodybuilding')

    Bodybuilding['poor'] = fuzz.trimf(Bodybuilding.universe, [0, 30, 35])
    Bodybuilding['average'] = fuzz.trimf(Bodybuilding.universe, [35, 60, 70])
    Bodybuilding['good'] = fuzz.trimf(Bodybuilding.universe, [71, 80, 101])

    rule1 = ctrl.Rule(ACTN3['good'] & PPARA['good'] &
                      AGT['good'], Bodybuilding['good'])
    rule2 = ctrl.Rule(ACTN3['good'] & PPARA['good'] &
                      AGT['average'], Bodybuilding['good'])
    rule3 = ctrl.Rule(ACTN3['good'] & PPARA['good'] &
                      AGT['poor'], Bodybuilding['good'])
    rule4 = ctrl.Rule(ACTN3['good'] & PPARA['average']
                      & AGT['good'], Bodybuilding['good'])
    rule5 = ctrl.Rule(ACTN3['good'] & PPARA['average']
                      & AGT['average'], Bodybuilding['average'])
    rule6 = ctrl.Rule(ACTN3['good'] & PPARA['average']
                      & AGT['poor'], Bodybuilding['average'])
    rule7 = ctrl.Rule(ACTN3['good'] & PPARA['poor'] &
                      AGT['good'], Bodybuilding['good'])
    rule8 = ctrl.Rule(ACTN3['good'] & PPARA['poor'] &
                      AGT['average'], Bodybuilding['average'])
    rule9 = ctrl.Rule(ACTN3['good'] & PPARA['poor'] &
                      AGT['poor'], Bodybuilding['average'])

    rule10 = ctrl.Rule(ACTN3['average'] & PPARA['good']
                       & AGT['good'], Bodybuilding['good'])
    rule11 = ctrl.Rule(ACTN3['average'] & PPARA['good']
                       & AGT['average'], Bodybuilding['average'])
    rule12 = ctrl.Rule(ACTN3['average'] & PPARA['good']
                       & AGT['poor'], Bodybuilding['average'])
    rule13 = ctrl.Rule(ACTN3['average'] & PPARA['average']
                       & AGT['good'], Bodybuilding['average'])
    rule14 = ctrl.Rule(ACTN3['average'] & PPARA['average']
                       & AGT['average'], Bodybuilding['average'])
    rule15 = ctrl.Rule(ACTN3['average'] & PPARA['average']
                       & AGT['poor'], Bodybuilding['average'])
    rule16 = ctrl.Rule(ACTN3['average'] & PPARA['poor']
                       & AGT['good'], Bodybuilding['average'])
    rule17 = ctrl.Rule(ACTN3['average'] & PPARA['poor']
                       & AGT['average'], Bodybuilding['average'])
    rule18 = ctrl.Rule(ACTN3['average'] & PPARA['poor']
                       & AGT['poor'], Bodybuilding['poor'])

    rule19 = ctrl.Rule(ACTN3['poor'] & PPARA['good'] &
                       AGT['good'], Bodybuilding['good'])
    rule20 = ctrl.Rule(ACTN3['poor'] & PPARA['good'] &
                       AGT['average'], Bodybuilding['average'])
    rule21 = ctrl.Rule(ACTN3['poor'] & PPARA['good'] &
                       AGT['poor'], Bodybuilding['poor'])
    rule22 = ctrl.Rule(ACTN3['poor'] & PPARA['average']
                       & AGT['good'], Bodybuilding['average'])
    rule23 = ctrl.Rule(ACTN3['poor'] & PPARA['average']
                       & AGT['average'], Bodybuilding['average'])
    rule24 = ctrl.Rule(ACTN3['poor'] & PPARA['average']
                       & AGT['poor'], Bodybuilding['poor'])
    rule25 = ctrl.Rule(ACTN3['poor'] & PPARA['poor'] &
                       AGT['good'], Bodybuilding['average'])
    rule26 = ctrl.Rule(ACTN3['poor'] & PPARA['poor'] &
                       AGT['average'], Bodybuilding['poor'])
    rule27 = ctrl.Rule(ACTN3['poor'] & PPARA['poor'] &
                       AGT['poor'], Bodybuilding['poor'])

    Bodybuilding_Ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12,
                                           rule13, rule14, rule15, rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule27])
    Bodybuilding = ctrl.ControlSystemSimulation(Bodybuilding_Ctrl)

    Bodybuilding.input['AGT'] = agt
    Bodybuilding.input['ACTN3'] = actn3
    Bodybuilding.input['PPARA'] = ppara

    Bodybuilding.compute()

    print(Bodybuilding.output['Bodybuilding'])


def Rowers(ACTN3, ACE, UCP3):
    x = [0, 1, 2]

    ACTN3 = ctrl.Antecedent(x, 'ACTN3')
    ACE = ctrl.Antecedent(x, 'ACE')
    UCP3 = ctrl.Antecedent(x, 'UCP3')

    ACTN3.automf(3)
    ACE.automf(3)
    UCP3.automf(3)

    Rowers = ctrl.Consequent(np.arange(0, 100, 1), 'Rowers')

    Rowers['poor'] = fuzz.trimf(Rowers.universe, [0, 30, 35])
    Rowers['average'] = fuzz.trimf(Rowers.universe, [35, 60, 70])
    Rowers['good'] = fuzz.trimf(Rowers.universe, [71, 80, 101])

    rule1 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      UCP3['good'], Rowers['good'])
    rule2 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      UCP3['average'], Rowers['good'])
    rule3 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      UCP3['poor'], Rowers['good'])
    rule4 = ctrl.Rule(ACTN3['good'] & ACE['average']
                      & UCP3['good'], Rowers['good'])
    rule5 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      UCP3['average'], Rowers['average'])
    rule6 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      UCP3['poor'], Rowers['average'])
    rule7 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      UCP3['good'], Rowers['good'])
    rule8 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      UCP3['average'], Rowers['average'])
    rule9 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      UCP3['poor'], Rowers['average'])

    rule10 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & UCP3['good'], Rowers['good'])
    rule11 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & UCP3['average'], Rowers['average'])
    rule12 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & UCP3['poor'], Rowers['average'])
    rule13 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & UCP3['good'], Rowers['average'])
    rule14 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & UCP3['average'], Rowers['average'])
    rule15 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & UCP3['poor'], Rowers['average'])
    rule16 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & UCP3['good'], Rowers['average'])
    rule17 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & UCP3['average'], Rowers['average'])
    rule18 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & UCP3['poor'], Rowers['poor'])

    rule19 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       UCP3['good'], Rowers['good'])
    rule20 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       UCP3['average'], Rowers['average'])
    rule21 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       UCP3['poor'], Rowers['poor'])
    rule22 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & UCP3['good'], Rowers['average'])
    rule23 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & UCP3['average'], Rowers['average'])
    rule24 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & UCP3['poor'], Rowers['poor'])
    rule25 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       UCP3['good'], Rowers['average'])
    rule26 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       UCP3['average'], Rowers['poor'])
    rule27 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       UCP3['poor'], Rowers['poor'])

    Rowers_Ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12,
                                     rule13, rule14, rule15, rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule27])
    Rowers = ctrl.ControlSystemSimulation(Rowers_Ctrl)

    Rowers.input['ACE'] = ace
    Rowers.input['ACTN3'] = actn3
    Rowers.input['UCP3'] = ucp3

    Rowers.compute()

    print(Rowers.output['Rowers'])


def Trackandfield(ACE, ACTN3, PPARα):
    x = [0, 1, 2]
    ACE = ctrl.Antecedent(x, 'ACE')
    ACTN3 = ctrl.Antecedent(x, 'ACTN3')
    PPARα = ctrl.Antecedent(x, 'PPARα')

    ACE.automf(3)
    ACTN3.automf(3)
    PPARα.automf(3)

    Trackandfield = ctrl.Consequent(np.arange(0, 100, 1), 'Trackandfield')

    Trackandfield['poor'] = fuzz.trimf(Trackandfield.universe, [0, 30, 35])
    Trackandfield['average'] = fuzz.trimf(Trackandfield.universe, [35, 60, 70])
    Trackandfield['good'] = fuzz.trimf(Trackandfield.universe, [71, 80, 101])

    rule1 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      PPARα['good'], Trackandfield['good'])
    rule2 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      PPARα['average'], Trackandfield['good'])
    rule3 = ctrl.Rule(ACTN3['good'] & ACE['good'] &
                      PPARα['poor'], Trackandfield['good'])
    rule4 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      PPARα['good'], Trackandfield['good'])
    rule5 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      PPARα['average'], Trackandfield['average'])
    rule6 = ctrl.Rule(ACTN3['good'] & ACE['average'] &
                      PPARα['poor'], Trackandfield['average'])
    rule7 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      PPARα['good'], Trackandfield['good'])
    rule8 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      PPARα['average'], Trackandfield['average'])
    rule9 = ctrl.Rule(ACTN3['good'] & ACE['poor'] &
                      PPARα['poor'], Trackandfield['average'])

    rule10 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & PPARα['good'], Trackandfield['good'])
    rule11 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & PPARα['average'], Trackandfield['average'])
    rule12 = ctrl.Rule(ACTN3['average'] & ACE['good']
                       & PPARα['poor'], Trackandfield['average'])
    rule13 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & PPARα['good'], Trackandfield['average'])
    rule14 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & PPARα['average'], Trackandfield['average'])
    rule15 = ctrl.Rule(ACTN3['average'] & ACE['average']
                       & PPARα['poor'], Trackandfield['average'])
    rule16 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & PPARα['good'], Trackandfield['average'])
    rule17 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & PPARα['average'], Trackandfield['average'])
    rule18 = ctrl.Rule(ACTN3['average'] & ACE['poor']
                       & PPARα['poor'], Trackandfield['poor'])

    rule19 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       PPARα['good'], Trackandfield['good'])
    rule20 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       PPARα['average'], Trackandfield['average'])
    rule21 = ctrl.Rule(ACTN3['poor'] & ACE['good'] &
                       PPARα['poor'], Trackandfield['poor'])
    rule22 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & PPARα['good'], Trackandfield['average'])
    rule23 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & PPARα['average'], Trackandfield['average'])
    rule24 = ctrl.Rule(ACTN3['poor'] & ACE['average']
                       & PPARα['poor'], Trackandfield['poor'])
    rule25 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       PPARα['good'], Trackandfield['average'])
    rule26 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       PPARα['average'], Trackandfield['poor'])
    rule27 = ctrl.Rule(ACTN3['poor'] & ACE['poor'] &
                       PPARα['poor'], Trackandfield['poor'])

    Trackandfield_Ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12,
                                            rule13, rule14, rule15, rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule27])
    Trackandfield = ctrl.ControlSystemSimulation(Trackandfield_Ctrl)

    Trackandfield.input['ACE'] = ace
    Trackandfield.input['ACTN3'] = actn3
    Trackandfield.input['PPARα'] = pparα

    Trackandfield.compute()
    print(Trackandfield.output['Trackandfield'])


def encoder(data):
    change = {"PHV Status": {"Pre-PHV": 1, "Mid-PHV": 2, "Post-PHV": 3},
              "PPARA": {"CC": 1, "GG": 2, "CG": 3},
              "NOS3": {"CC": 1, "TT": 2, "CT": 3},
              "COL1A1": {"TT": 1, "CC": 2, "TC": 3},
              "VDR": {"AA": 1, "GG": 2, "AG": 3},
              "ACTN3": {"RR": 1, "RX": 2, "XX": 3},
              "BDNF": {"CC": 1, "CT": 2, "TT": 3},
              "COL5A1": {"CC": 1, "CT": 2, "TT": 3},
              "COL2A1": {"CC": 1, "CT": 2, "TT": 3},
              "AMPD1": {"CC": 1, "CT": 2, "TT": 3},
              "AGT": {"GG": 1, "GC": 2, "CC": 3},
              "GDF5": {"TC": 1, "TT": 2, "CC": 3},
              "IGF2": {"GG": 1, "AG": 2, "AA": 3},
              "Sample": {"Amatuer": 1, "pro": 2, "semi": 3},
              "Ankle Injuries": {"Not": 0, "Diseased": 1},
              "Knee Injuries": {"Not": 0, "Diseased": 1}}
    data = data.replace(change)
    return data


def effects():
    pass
