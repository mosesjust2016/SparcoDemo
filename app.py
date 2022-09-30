
from email import header
from os import access
from flask import Flask, jsonify, request, session
from flask_jwt_extended import jwt_required, JWTManager, create_access_token, create_refresh_token, get_jwt_identity
from flask import render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from email.message import EmailMessage
from datetime import timedelta, datetime
from PIL import Image
from decouple import config
from urllib.request import urlopen 
import io,  base64, uuid, ssl, smtplib
import psycopg2
import psycopg2.extras
import random
import requests



app = Flask(__name__)


app.config['SECRET_KEY'] = config('SECRET_KEY')
CORS(app)
JWTManager(app)

email_sender = config('EMAIL_USER')
email_password =config('EMAIL_PASS')
sms_username = config('SMS_USER')
sms_password = config('SMS_PASS')


DB_HOST = "localhost"
DB_NAME = "sparcodemo"
DB_USER = "postgres"
DB_PASS = config('DB_PASS')

conn = psycopg2.connect(dbname= DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

@app.route('/profile')
@jwt_required()
def profile():

    _user = get_jwt_identity()

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = "SELECT * FROM useraccount WHERE id=%s"
    sql_where = (_user,)

    cursor.execute(sql, sql_where)
    row = cursor.fetchone()
    _firstname =  row['firstname']
    _lastname =  row['lastname']
    _email = row['email']
    _phonenumber = row['phonenumber']


    if row:
       
        return jsonify({
                            'firstname' : _firstname, 
                            'lastname' : _lastname,
                            'email': _email,
                            'phonenumber': _phonenumber})

    else:
         resp = jsonify({'message' : 'Unauthorized'})
         resp.status_code = 401
         return resp


#User List
@app.route('/userlist')
@jwt_required()
def userlist():

    _user = get_jwt_identity()

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = "SELECT * FROM useraccount"

    cursor.execute(sql)
    row = cursor.fetchall()
    _firstname =  row['firstname']
    _lastname =  row['lastname']
    _email = row['email']
    _phonenumber = row['phonenumber']


    if row:
       
        return jsonify({
                            'firstname' : _firstname, 
                            'lastname' : _lastname,
                            'email': _email,
                            'phonenumber': _phonenumber})

    else:
         resp = jsonify({'message' : 'Data not available'})
         resp.status_code = 401
         return resp






@app.route('/login', methods=['POST'])
def login():
    _json = request.json
    _email = _json['email']
    _password = _json['password']
   

    if _email and _password:
        #check if user exists
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        sql = "SELECT * FROM useraccount WHERE email=%s"
        sql_where = (_email,)

        cursor.execute(sql, sql_where)
        row = cursor.fetchone()
        _id =  row['id']
        email = row['email']
        password = row['password']

        if row:
            if check_password_hash(password, _password):
                cursor.close()

                refresh = create_refresh_token(identity= _id)
                access = create_access_token(identity= _id)

                return jsonify({
                                'user': {
                                    'refresh': refresh,
                                    'access' : access,
                                    'email' : email
                                } 
                             }), 200

            else:
                 resp = jsonify({'message' : 'Bad Request - invalid password'})
                 resp.status_code = 400
                 return resp


    else:
        resp = jsonify({'message' : 'Bad Request - invalid credentials'})
        resp.status_code = 400
        return resp

@app.route('/register', methods=['POST'])
def register():

        _json = request.json
        _platform = _json['platform']
        _firstname = _json['firstname']
        _lastname = _json['latstname']
        _email = _json['email']
        _password = _json['password']
        _phonenumber = _json['phonenumber']
        _userimage = _json['userimage']



        if _firstname and _lastname and _email and _password and _phonenumber and _userimage:
            _hashed_password = generate_password_hash(_password)

            image = base64.b64decode(str(_userimage))  
            my_id = uuid.uuid4().hex     
            fileName = my_id + '.png'

            imagePath = ('img/'+fileName)
            img = Image.open(io.BytesIO(image))
            img.save(imagePath, 'png')

            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            #Check if account exists using Postgres
            cursor.execute('SELECT * FROM useraccount WHERE email = %s', (_email,))
            account = cursor.fetchone()
            print(account)
            # If account exists show error and validation checks
            if account:
                resp = jsonify({'message' : 'Account already exists!'})
                return resp

            else:

                otp = str(random.randint(100000, 999999));

                if _platform  == "web":

                    subject = "Registration Notification"
                    body = render_template('index.html', user_otp = otp)

                    #Sending Email
                    send_msg(email_sender, _email, subject, body)

                if _platform == "mobile" :

                    #Sending SMS
                    resp = requests.get('https://api.rmlconnect.net/bulksms/bulksms?username='+ sms_username +'&password='+ sms_password +'&type=0&dlr=1&destination=26'+ _phonenumber + '&source=Sparcodemo&message=Your one time password to register for Sparco Demo is :' + otp)
        
                    print(resp)

                # Account doesnt exists and the form data is valid, now insert new account into users table
                cursor.execute("INSERT INTO useraccount (firstname, lastname, email, password, phonenumber, usertype, imagelocation, otp, email_confirmed, mobile_confirmed, profile) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (_firstname, _lastname, _email, _hashed_password, _phonenumber, 'Standard', imagePath, otp , 'False', 'False','closed' ))
                conn.commit()

                return jsonify({'message' : 'You have successfully registered!'})
        else:
            resp = jsonify({'message' : 'Please fill in all fields'})
            return resp


def send_msg(sender, sendto, heading, msg):

        em = EmailMessage()
        em['From'] = sender
        em['To'] = sendto
        em['Subject'] = heading
        em.add_header('Content-Type','text/html')
        em.set_payload(msg)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                    smtp.login(sender, email_password)
                    smtp.sendmail(email_sender, sendto, em.as_string().encode("utf-8"))


        return msg

@app.route('/accountVerify', methods=['PUT'])
def accountVerify():

    _json = request.json
    _platform = _json['platform']
    update_value = True

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if _platform  == "web":

            _email = _json['email']
            _otp = _json['otp']


            #Check if account exists using Postgres
            cursor.execute('SELECT * FROM useraccount WHERE email = %s AND otp = %s', (_email, _otp,))
            account = cursor.fetchone()

            if account:
                
                    cursor.execute('UPDATE useraccount SET email_confirmed = (%s) WHERE email = %s', (update_value, _email))
                    cursor.commit()
                    cursor.close()
                
                    return jsonify({'message' : 'Account confirmed'})

            else:
                return jsonify({'message' : 'Account does not exists!'})
            
            

    if _platform  == "mobile":
        
         _mobile = _json['mobile']
         _otp = _json['otp']
         
         
         #Check if account exists using Postgres
         cursor.execute('SELECT * FROM useraccount WHERE phonenumber = %s', (_mobile,))
         
         account = cursor.fetchone()

         if account:
                cursor.execute('UPDATE useraccount SET mobile_confirmed = "True" WHERE phonenumber = %s', (_mobile,))
                cursor.commit()
                return jsonify({'message' : 'Account confirmed'})
         else:
                return jsonify({'message' : 'Account does not exists!'})



if __name__ == "__main__":
    app.run(debug=True)