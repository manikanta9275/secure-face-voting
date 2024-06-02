from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, session
from flask_mail import Mail, Message
import cv2
import face_recognition
import numpy as np
import mysql.connector
import base64
import uuid
import os
import secrets
import hashlib
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Update with your SMTP server details
app.config['MAIL_PORT'] = 587  # Update with the port number of your SMTP server
app.config['MAIL_USE_TLS'] = True  # Enable TLS
app.config['MAIL_USERNAME'] = 'abhiproject9275@gmail.com'  # Update with your email address
app.config['MAIL_PASSWORD'] = 'kvna acie pjzh kleq'  # Update with your email password

mail = Mail(app)

# Load the pre-trained Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Configure MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="", 
    database="sample"
)


# Function to generate a 4-digit OTP
def generate_otp():
    return str(secrets.randbelow(10000)).zfill(4)


# Function to send OTP via email
def send_otp_via_email(email, otp):
    try:
        msg = Message('Your OTP for Password Reset', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f'Your OTP for password reset is: {otp}'
        mail.send(msg)
        flash('OTP sent to your email address.')
    except smtplib.SMTPException as e:
        flash(f"Error sending OTP via email: {e}")
    except Exception as e:
        flash(f"An unexpected error occurred: {e}")

        
# Route for requesting password reset (Administrator)
@app.route('/forgot_password_adi', methods=['GET', 'POST'])
def forgot_password_adi():
    cursor = db.cursor()
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']

        # Check if email exists in the database
        cursor.execute("SELECT * FROM `Administrator Login` WHERE email = %s AND username = %s", (email, username))
        user = cursor.fetchone()

        if user:
            # Generate OTP
            otp = generate_otp()

            # Store OTP in the session for verification
            session['otp'] = otp
            session['email'] = email

            # Send OTP via email
            try:
                msg = Message('Your OTP for Password Reset', sender=app.config['MAIL_USERNAME'], recipients=[email])
                msg.body = f'Your OTP for password reset is: {otp}'
                mail.send(msg)
                flash('OTP sent to your email address.')
                return redirect(url_for('verify_otp_adi'))
            except Exception as e:
                flash(f"Error sending OTP via email: {e}")

        else:
            flash('User does not exist.')
    cursor.close()
    return render_template('forgot_pass_adi.html')


# Route for verifying OTP (Administrator)
@app.route('/verify_otp_adi', methods=['GET', 'POST'])
def verify_otp_adi():
    cursor = db.cursor()
    if 'otp' in session and 'email' in session:
        if request.method == 'POST':
            otp_entered = request.form['otp']
            if otp_entered == session['otp']:
                return redirect(url_for('reset_password_adi'))
            else:
                flash('Invalid OTP.')
        return render_template('verify_otp_adi.html')
    else:
        flash('Session expired. Please request OTP again.')
        return redirect(url_for('forgot_password_adi'))

# Route for resetting password (Administrator)
@app.route('/reset_password_adi', methods=['GET', 'POST'])
def reset_password_adi():
    cursor = db.cursor()
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password == confirm_password:
            

            # Update user's password in the database
            cursor.execute("UPDATE `Administrator Login` SET password = %s WHERE email = %s", (new_password, session['email']))
            db.commit()

            flash('Password reset successful. You can now login with your new password.')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match.')
    cursor.close()
    return render_template('reset_pass_adi.html')

# Route for requesting password reset (Volunteer)
@app.route('/forgot_password_vol', methods=['GET', 'POST'])
def forgot_password_vol():
    cursor = db.cursor()
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']  # Add this line to get the username from the form

        # Check if email and username exist in the database and belong to the same user
        cursor.execute("SELECT * FROM `volunteer Login` WHERE email = %s AND username = %s", (email, username))
        user = cursor.fetchone()

        if user:
            # Generate OTP
            otp = generate_otp()

            # Store OTP in the session for verification
            session['otp'] = otp
            session['email'] = email

            # Send OTP via email
            try:
                msg = Message('Your OTP for Password Reset', sender=app.config['MAIL_USERNAME'], recipients=[email])
                msg.body = f'Your OTP for password reset is: {otp}'
                mail.send(msg)
                flash('OTP sent to your email address.')
                return redirect(url_for('verify_otp_vol'))
            except Exception as e:
                flash(f"Error sending OTP via email: {e}")

        cursor.close()
    return render_template('forgot_pass_vol.html')

# Route for verifying OTP (Volunteer)
@app.route('/verify_otp_vol', methods=['GET', 'POST'])
def verify_otp_vol():
    cursor = db.cursor()
    if 'otp' in session and 'email' in session:
        if request.method == 'POST':
            otp_entered = request.form['otp']
            if otp_entered == session['otp']:
                return redirect(url_for('reset_password_vol'))
            else:
                flash('Invalid OTP.')
        return render_template('verify_otp_vol.html')
    else:
        flash('Session expired. Please request OTP again.')
        return redirect(url_for('forgot_password_vol'))

# Route for resetting password (Volunteer)
@app.route('/reset_password_vol', methods=['GET', 'POST'])
def reset_password_vol():
    cursor = db.cursor()
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password == confirm_password:
            

            # Update user's password in the database
            cursor.execute("UPDATE `volunteer Login` SET password = %s WHERE email = %s", (new_password, session['email']))
            db.commit()

            flash('Password reset successful. You can now login with your new password.')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match.')
    cursor.close()
    return render_template('reset_pass_vol.html')

# Fetch faces from database function
def fetch_faces_from_database():
    faces = []
    try:
        cursor = db.cursor()
        cursor.execute("SELECT name, father_name, card_number, photo FROM voter1")
        result = cursor.fetchall()

        for row in result:
            name, father_name, card_number, photo_blob = row
            if photo_blob:
                nparr = np.frombuffer(photo_blob, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    face_encodings = face_recognition.face_encodings(img)
                    if face_encodings:
                        faces.append((name, father_name, card_number, face_encodings[0]))
        return faces
    except Exception as e:
        print("Error fetching faces from database:", e)
        return []
    finally:
        cursor.close()


def recognize_faces(known_faces, unknown_frame, tolerance=0.4):
    unknown_face_encodings = face_recognition.face_encodings(unknown_frame)

    if len(unknown_face_encodings) > 1:
        return "", "", "", False, "Multiple persons detected"

    for unknown_face_encoding in unknown_face_encodings:
        for name, father_name, card_number, known_face_encoding in known_faces:
            matches = face_recognition.compare_faces([known_face_encoding], unknown_face_encoding)

            if matches[0]:
                # Check if card number exists in voter_id table
                cursor = db.cursor()
                cursor.execute("SELECT * FROM voter_id WHERE card_number = %s", (card_number,))
                result = cursor.fetchall()
                cursor.close()
                if not result:
                    return name, father_name, card_number, False, "Person not voted yet"
                else:
                    return name, father_name, card_number, True, "Person already voted"

    return "", "", "", False, "Unknown"
known_faces = fetch_faces_from_database()


@app.route('/submit_form', methods=['POST'])
def submit_form():
    card_number = request.form['card_number']
    cursor = db.cursor()
    cursor.execute("INSERT INTO voter_id (card_number, timestamp) VALUES (%s, NOW())", (card_number,))
    db.commit()
    cursor.close()
    return "Form submitted successfully!"


@app.route('/')
def login():
    return render_template('login_signup.html')


@app.route('/volunteer', methods=['POST'])
def volunteer():
    cursor = db.cursor()
    username = request.form['username']
    password = request.form['password']
    

    # Query Volunteer Login table
    cursor.execute("SELECT * FROM `Volunteer Login` WHERE username=%s AND password=%s", (username, password))
    volunteer_login = cursor.fetchone()
    
    if volunteer_login:
        return redirect(url_for('volunteer_page'))  # Redirect to volunteer_page

    return render_template('login_signup.html', error_message_vol='Invalid username or password')

@app.route('/volunteer')
def volunteer_page():
    return render_template('vol.html')

@app.route('/election')
def election():
    return render_template('election.html')

@app.route('/new_registration')
def new_registration():
    return render_template('new_reg.html')

@app.route('/display_images')
def display_images():
    cursor = db.cursor()
    try:
        cursor.execute("SELECT name, father_name, card_number, gender, dob, address, photo FROM voter1")
        details = cursor.fetchall()

        # Convert photo data to base64 for displaying in HTML
        for i, row in enumerate(details):
            if row[6]:  # Check if photo data is not empty
                photo_base64 = base64.b64encode(row[6]).decode('utf-8')
                details[i] = (*row[:6], photo_base64)  # Replace photo data with base64 encoded string

        return render_template('dis_img.html', details=details)
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()

@app.route('/administrator')
def administrator():
    return render_template('adm.html')

@app.route('/administrator', methods=['POST'])
def administrator_page():
    cursor = db.cursor()
    username = request.form['username']
    password = request.form['password']

    # Query Administrator Login table
    cursor.execute("SELECT * FROM `Administrator Login` WHERE username=%s AND password=%s", (username, password))
    admin_login = cursor.fetchone()
    cursor.close()
    if admin_login:
        return redirect(url_for('administrator_page'))  # Redirect to volunteer_page

    return render_template('login_signup.html', error_message='Invalid username or password')

@app.route('/new_reg_adm')
def new_reg_adm():
    return render_template('new_reg_adm.html')


@app.route('/register_admin', methods=['POST'])
def register_admin_post():
    cursor = db.cursor()
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    phone_number = request.form['phone_number']
    email = request.form['email']
    aadhar_number = request.form['aadhar_number']
    voter_id = request.form['voter_id']
    address = request.form['address']
    gender = request.form['gender']
    dob = request.form['dob']
    # Check if password matches the confirmation password
    if password != confirm_password:
        Flask("Password and confirmation password do not match.")
        return redirect('/register_admin')  # Redirect back to registration page

    try:
        # Insert data into the Administrator Login table
        cursor.execute("INSERT INTO `Administrator Login` (username, password, phone_number, aadhar_number, voter_id, address, gender, dob,email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (username, password, phone_number, aadhar_number, voter_id, address, gender, dob, email))
        db.commit()
        return "Administrator registered successfully!"
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()

@app.route('/display_adm')
def display_adm():
    cursor = db.cursor()
    try:
        # Fetch all records from the Administrator Login table
        cursor.execute("SELECT * FROM `Administrator Login`")
        administrators = cursor.fetchall()
        return render_template('display_adm.html', administrators=administrators)
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()


@app.route('/new_reg_vol')
def new_reg_vol():
    return render_template('new_reg_vol.html')


@app.route('/register_vol', methods=['POST'])
def register_vol_post():
    cursor = db.cursor()
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    phone_number = request.form['phone_number']
    email = request.form['email']
    aadhar_number = request.form['aadhar_number']
    voter_id = request.form['voter_id']
    address = request.form['address']
    gender = request.form['gender']
    dob = request.form['dob']
    # Check if password matches the confirmation password
    if password != confirm_password:
        Flask("Password and confirmation password do not match.")
        return redirect('/register_vol')  # Redirect back to registration page

    try:
        # Insert data into the Administrator Login table
        cursor.execute("INSERT INTO `volunteer login` (username, password, phone_number, aadhar_number, voter_id, address, gender,email,dob) VALUES (%s, %s, %s, %s, %s, %s, %s,%s,%s)",
                       (username, password, phone_number, aadhar_number, voter_id, address, gender,email,dob))
        db.commit()
        return "volunteer registered successfully!"
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()


@app.route('/display_vol')
def display_vol():
    cursor = db.cursor()
    try:
        # Fetch all records from the Administrator Login table
        cursor.execute("SELECT * FROM `volunteer Login`")
        volunteers = cursor.fetchall()
        return render_template('display_vol.html', volunteers=volunteers)
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()

def generate_filename(name):
    unique_id = str(uuid.uuid4())[:8]  # Generate a unique identifier
    return f"detected_faces/{name}_{unique_id}.jpg"

def store_in_database(name, father_name, card_number, gender, dob, address, photo):
    cursor = db.cursor()
    try:
        # Insert data into the voter1 table
        sql_query = """INSERT INTO voter1 (name, father_name, card_number, gender, dob, address, photo) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql_query, (name, father_name, card_number, gender, dob, address, photo))
        db.commit()
        print("Data inserted successfully into the database")
        return 'success'
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return 'failed'
    finally:
        cursor.close()

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    name = data['name']
    father_name = data['father_name']
    card_number = data['card_number']
    gender = data['gender']
    dob = data['dob']
    address = data['address']
    image_data = base64.b64decode(data['imageData'].split(',')[1])

    nparr = np.frombuffer(image_data, np.uint8)
    image_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

    success = False
    for (x, y, w, h) in faces:
        face_roi = image_np[y:y + h, x:x + w]
        _, buffer = cv2.imencode('.jpg', face_roi)
        photo_blob = buffer.tobytes()
        success = store_in_database(name, father_name, card_number, gender, dob, address, photo_blob)
    
    return jsonify({'status': success})


@app.route('/recognize', methods=['POST'])
def recognize():
    cursor = db.cursor()
    try:
        photo_data = request.json.get('photo')
        photo_data = base64.b64decode(photo_data.split(",")[1])
        nparr = np.frombuffer(photo_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        name, father_name, card_number, voted, status = recognize_faces(known_faces, img)
        return jsonify({'name': name, 'fatherName': father_name, 'cardNumber': card_number, 'voted': voted, 'status': status})
    except Exception as e:
        return jsonify({'status': 'failed', 'error': str(e)})
    finally:
        cursor.close()
        
@app.route('/fetch_details', methods=['POST'])
def fetch_details():
    cursor = db.cursor()
    try:
        card_number = request.json.get('card_number')
        cursor.execute("SELECT name, father_name, card_number FROM voter1 where card_number=%s", (card_number,))
        result = cursor.fetchone()

        if result:
            name, father_name, card_number = result
            cursor.execute("SELECT * FROM voter_id WHERE card_number = %s", (card_number,))
            result = cursor.fetchall()
            if not result:
                return jsonify({'name': name, 'fatherName': father_name, 'cardNumber': card_number, 'voted': False, 'status': 'not_voted'})
            else:
                return jsonify({'name': name, 'fatherName': father_name, 'cardNumber': card_number, 'voted': True, 'status': 'already_voted'})
        else:
            return jsonify({'status': 'not_found'})
    except Exception as e:
        return jsonify({'status': 'failed', 'error': str(e)})
    finally:
        cursor.close()

@app.route('/audio.mp3')
def static_audio():
    return send_from_directory('static', 'audio.mp3', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

