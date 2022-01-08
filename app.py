from flask import Flask, render_template, request, session
import re
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)

app.config["DEBUG"] = True

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dna'

mysql = MySQL(app)


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
