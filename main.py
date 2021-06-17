from flask import Flask, render_template, request,redirect,flash,send_file,session,url_for
from forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message
import json
import os
import smtplib
from datetime import datetime
from io import BytesIO
import smtplib
import imghdr
from email.message import EmailMessage


'''This is for extracting the contents of config.json file'''
with open('config.json','r') as c:
    params = json.load(c)["params"]
    print(params)
local_server = True
app = Flask(__name__)

# Setting secretkey
app.secret_key = 'my secret key'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

print("Helo")
class Bookscollection(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    names_books = db.Column(db.String(100), nullable=False)
    pdf_books = db.Column(db.LargeBinary, nullable=False)

class Login(db.Model):
   
    id = db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(15), unique=True)
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(256), unique=True)
    email = db.Column(db.String(50), unique=True)

class Records(db.Model):

    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    domain = db.Column(db.String(12), nullable=False)
    book = db.Column(db.String(12), nullable=False)
    year = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def homepage():
    return redirect('/login')


@app.route("/about/")
def about():
    return render_template('about.html',params = params)


@app.route("/news/")
def news():
    return render_template('news.html',params = params)


@app.route("/upload", methods = ['POST'])
def uploader():
    f= request.files['file1']
    newFile = Bookscollection(names_books = f.filename, pdf_books = f.read())
    db.session.add(newFile)
    db.session.commit()
    return redirect('/addbook')
      

@app.route('/download/<string:names_books>',methods = ['GET'])
def download(names_books):
    file_data = Bookscollection.query.filter_by(names_books = names_books).first()
    return send_file(BytesIO(file_data.pdf_books),attachment_filename=names_books, as_attachment=True)
 

@app.route('/mystore/')
def mystore():
    books = Bookscollection.query.filter_by().all()
    return render_template('mystorestud.html', params=params, books=books)


# User Registration Api End Point
@app.route('/register/', methods = ['GET', 'POST'])
def register():
    # Creating RegistrationForm class object
    form = RegisterForm(request.form)

    # Cheking that method is post and form is valid or not.
    if request.method == 'POST' and form.validate():

        # if all is fine, generate hashed password
        hashed_password = generate_password_hash(form.password.data, method='sha256')

        # create new user model object
        new_user = Login(
            name = form.name.data,
           username = form.username.data,
            email = form.email.data,
            password = hashed_password )
        # saving user object into data base with hashed password
        db.session.add(new_user)
        db.session.commit()
        flash('You have successfully registered', 'success')
        # if registration successful, then redirecting to login Api

        return render_template('studentsbase.html', form=form, params=params)
        # return redirect("/dashboard")
    else:
        # if method is Get, than render registration form
        return render_template('studentregister.html', form = form,params = params)

# Login API endpoint implementation
@app.route('/login/', methods = ['GET', 'POST'])
def login():
    # Creating Login form object
    form = LoginForm(request.form)
    # verifying that method is post and form is valid
    if request.method == 'POST' and form.validate:
        # checking that user is exist or not by email
        user = Login.query.filter_by(email = form.email.data).first()

        if user:
            # if user exist in database than we will compare our database hased password and password come from login form
            if check_password_hash(user.password, form.password.data):
                # if password is matched, allow user to access and save email and username inside the session
                flash('You have successfully logged in.', "success")
                session['logged_in'] = True
                session['email'] = user.email
                session['username'] = user.username
                # After successful login, redirecting to home page
                # return redirect("/dashboard")
                return render_template('studentsbase.html', form=form, params=params)
            else:

                # if password is in correct , redirect to login page
                flash('Username or Password Incorrect', "Danger")
                return redirect(url_for('login'))
    # rendering login page
    return render_template('studentlogin.html', form = form, params = params)

@app.route('/studentlogout/')
def studentlogout():
#     # Removing data from session by setting logged_flag to False.
    session['logged_in'] = False
    # redirecting to home page
    return redirect(url_for('login'))

@app.route('/studentsbase/')
def dashboardstudent():
    books = Bookscollection.query.filter_by().all()
    return render_template('studentsbase.html', params=params, books=books)

@app.route("/adminlogin/")
def adminlogin():
    if ('user' in session and session['user'] == params['admin_user']):
        return render_template('admindashboard.html', params=params)

    else:
        return render_template('adminlogin.html',params = params)

@app.route("/adminhomepage/", methods=['GET', 'POST'])
def adminhomepage():

    if ('user' in session and session['user'] == params['admin_user']):
        return render_template('admindashboard.html', params=params)


    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            #setting the session variable
            session['user'] = username
            return render_template('admindashboard.html', params=params)
        else:

            return render_template('adminlogin.html', params=params)

@app.route("/adminlogout/")
def logout():
    if ('user' in session and session['user'] == params['admin_user']):
        session.pop('user')
    return redirect(url_for('login'))
      
@app.route("/searchbooks/")
def search():
        return render_template('searchbooks.html',params=params)

@app.route("/bklist/")
def bklist():
    res = Records.query.filter_by().all()
    print(res)
    return render_template('bklist.html',params=params,res= res)

@app.route("/addbook/")
def addbk():
        return render_template('addbook.html',params=params)

@app.route("/issuebook/" , methods = ['GET','POST'])
def issuebk():
    print("Helo")
    print("Helo")

    if 'user' in session and session['user'] == params['admin_user']:
      if request.method == 'POST':
            print("Helo")
            '''Add entry to the database'''
            name = request.form.get('name')
            email = request.form.get('inputEmail4')
            domain = request.form.get('domainVal')
            book = request.form.get('inputBook')

            year = request.form.get('year')

            if name == '' and book == '' and email == '':
                flash("Please enter the required details", "info")
                return render_template('issuebook.html', params=params)



            else:

                library1 = Records(name=name, email=email,domain = domain ,book=book, year=year, date=datetime.now())

                db.session.add(library1)
                db.session.commit()

                flash("Successfully recorded your details", "success")


                return redirect('/records')

      return render_template('issuebook.html',params=params)
    else:
        return render_template('landing.html', params=params)


    return render_template('issuebook.html',params=params)

@app.route("/records/")
def records():

    if ('user' in session and session['user'] == params['admin_user']):
        posts = Records.query.filter_by().all()
        return render_template('records.html',params=params,posts = posts)

@app.route("/delete/<int:sno>" , methods = ['GET'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        nam = request.form.get('libDomain')
        print(nam)
        posts = Records.query.filter_by(sno=sno).first()
        db.session.delete(posts)
        db.session.commit()
    return redirect('/records')
    
@app.route("/update/<int:sno>" , methods = ['GET','POST'])
def update(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            '''Add entry to the database'''
            name = request.form.get('name')
            email = request.form.get('inputEmail4')
            domain = request.form.get('domainVal')
            book = request.form.get('inputBook')
            year = request.form.get('year')
            date = datetime.now()

            posts = Records.query.filter_by(sno=sno).first()
            posts.name = name
            posts.email = email
            posts.domain = domain
            posts.book = book
            posts.year = year
            posts.date = date
            db.session.commit()

            return redirect('/records')
        posts = Records.query.filter_by(sno=sno).first()
        return render_template('edit.html',params = params,posts = posts)
    


@app.route("/reissue/<int:sno>",methods = ['GET','POST'])
def reissue(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            '''Add entry to the database'''
            posts = Records.query.filter_by(sno=sno).first()
            posts.date = datetime.now()
            db.session.commit()
            return redirect('/records')
        posts = Records.query.filter_by(sno=sno).first()
        return redirect('/records')


@app.route("/contact/" ,methods = ['GET','POST'])
def contact():
    if request.method == 'POST':
        print("Helo")
        '''Add entry to the database'''
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        message = request.form.get('message')
        mail.send_message ('New message from ' + fname + " " + lname,
                          sender = email,
                          recipients = [params['gmail-user']],
                          body = "\n" + message  + "\n"
                          )
        return redirect('/studentsbase')
    return render_template('contact.html',params=params)
app.run(debug=True,host='localhost',port=8000)
