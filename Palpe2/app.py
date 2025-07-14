from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
import sqlite3
import os
import uuid
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from mediapipe.framework.formats import landmark_pb2
import json
from ultralytics import YOLO
from scipy.spatial.distance import cosine
from mediapipe.python.solutions import hands
from twilio.rest import Client
from xhtml2pdf import pisa
import io
import base64
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(TTFont('DejaVuSans', 'C:/Users/Ankan Dutta/OneDrive/Desktop/Palpe2/static/fonts/DejaVuSans.ttf'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load YOLOv8 hand detection model once
Model="Your Model"



def extract_landmarks(image):
    with hands.Hands(static_image_mode=True, max_num_hands=1) as hand_detector:
        results = hand_detector.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        multi_hand_landmarks = getattr(results, 'multi_hand_landmarks', None)
        if multi_hand_landmarks:
            return np.array([[lm.x, lm.y, lm.z] for lm in multi_hand_landmarks[0].landmark]).flatten().tolist()
    return None

def compare_landmarks(landmarks1, landmarks2, threshold=1.0):  # Try 1.0 or even higher
    arr1 = np.array(landmarks1)
    arr2 = np.array(landmarks2)
    if arr1.shape != arr2.shape:
        print("Shape mismatch:", arr1.shape, arr2.shape)
        return False
    dist = np.linalg.norm(arr1 - arr2)
    print("Landmark distance:", dist, "Threshold:", threshold)
    return dist < threshold

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect('database/db.sqlite3')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            palm_image TEXT,
            wallet_balance REAL DEFAULT 0.0,
            palm_embedding TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Merchants table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            business_name TEXT NOT NULL,
            business_address TEXT NOT NULL,
            business_license TEXT NOT NULL,
            wallet_balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            from_user_id INTEGER,
            to_user_id INTEGER,
            from_merchant_id INTEGER,
            to_merchant_id INTEGER,
            amount REAL NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users (id),
            FOREIGN KEY (to_user_id) REFERENCES users (id),
            FOREIGN KEY (from_merchant_id) REFERENCES merchants (id),
            FOREIGN KEY (to_merchant_id) REFERENCES merchants (id)
        )
    ''')
    
    # OTP table (for simulation)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            is_used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Helper to convert UTC to IST
IST = timezone(timedelta(hours=5, minutes=30))
def utc_to_ist(dt_str):
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        dt = dt.replace(tzinfo=timezone.utc).astimezone(IST)
        return dt.strftime('%b %d, %Y, %I:%M %p')
    except Exception:
        return dt_str

def set_otp(phone_number):
    otp = str(uuid.uuid4())[:6] # Generate a 6-digit OTP
    conn = sqlite3.connect('database/db.sqlite3')
    cursor = conn.cursor()
    now_ist = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO otps (phone_number, otp_code, created_at)
        VALUES (?, ?, ?)
    ''', (phone_number, otp, now_ist))
    conn.commit()
    conn.close()
    return otp



# Routes
@app.route('/')
def index():
    return render_template('user_login.html')

# User routes
@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        full_name = request.form['full_name']
        # Phone number validation
        if not phone_number.isdigit() or len(phone_number) != 10:
            flash('Phone number must be exactly 10 digits!')
            return render_template('user_signup.html')
        
        # Check if user already exists
        conn = sqlite3.connect('database/db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE phone_number = ?', (phone_number,))
        if cursor.fetchone():
            flash('User already exists with this phone number!')
            conn.close()
            return render_template('user_signup.html')
        
        # Handle palm image upload
        palm_image = None
        if 'palm_image' in request.files:
            file = request.files['palm_image']
            if file and allowed_file(file.filename):
                file.save('debug_uploaded.jpg')  # Save for manual inspection
                file.stream.seek(0)  # Reset stream for further reading
                npimg = np.frombuffer(file.read(), np.uint8)
                img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
                if img is None:
                    conn.close()
                    flash('Uploaded image could not be read. Please try again.')
                    return render_template('user_signup.html')
                #hand_img = crop_hand_from_image(img)
                #if hand_img is None:
                    conn.close()
                    flash('No hand detected in the uploaded image. Please upload a clear palm image.')
                    return render_template('user_signup.html')
                landmarks = extract_landmarks(img)
                if landmarks is None:
                    conn.close()
                    flash('No hand detected in the uploaded image. Please upload a clear palm image.')
                    return render_template('user_signup.html')
                landmarks_json = json.dumps(landmarks)
                # Save only the cropped hand image
                filename = secure_filename(f"palm_{phone_number}_{uuid.uuid4().hex[:8]}.jpg")
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                #cv2.imwrite(save_path, hand_img)
                palm_image = filename
        
        # Create user
        now_ist = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO users (phone_number, full_name, palm_image, palm_embedding, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (phone_number, full_name, palm_image, landmarks_json, now_ist))
        
        conn.commit()
        conn.close()
        
        flash('User registered successfully! Please login.')
        return redirect(url_for('user_login'))
    
    return render_template('user_signup.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        otp = request.form['otp']  # In real app, verify OTP
        
        conn = sqlite3.connect('database/db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE phone_number = ?', (phone_number,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_type'] = 'user'
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid phone number or OTP!')
    
    return render_template('user_login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session['user_type'] != 'user':
        return redirect(url_for('user_login'))
    
    conn = sqlite3.connect('database/db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Get transaction history with merchant name
    cursor.execute('''
        SELECT t.*, m.business_name FROM transactions t
        LEFT JOIN merchants m ON t.to_merchant_id = m.id
        WHERE t.from_user_id = ? OR t.to_user_id = ?
        ORDER BY t.created_at DESC
        LIMIT 9
    ''', (session['user_id'], session['user_id']))
    transactions = cursor.fetchall()
    conn.close()
    # Pass created_at as-is (IST)
    transactions = [
        list(t[:8]) + [t[8]] + [t[9] if len(t) > 9 else None] for t in transactions
    ]
    return render_template('dashboard_user.html', user=user, transactions=transactions)

@app.route('/user/add_money', methods=['POST'])
def add_money():
    if 'user_id' not in session or session['user_type'] != 'user':
        return jsonify({'error': 'Not authenticated'}), 401
    amount = float(request.form['amount'])
    otp = request.form.get('otp')
    if not otp:
        return jsonify({'error': 'OTP required'}), 400
    conn = sqlite3.connect('database/db.sqlite3')
    cursor = conn.cursor()
    # Get user's phone number
    cursor.execute('SELECT phone_number FROM users WHERE id = ?', (session['user_id'],))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    phone_number = row[0]
    # Verify OTP (must be latest, unused, and within 10 min)
    cursor.execute('''SELECT id, created_at FROM otps WHERE phone_number = ? AND otp_code = ? AND is_used = 0 ORDER BY created_at DESC LIMIT 1''', (phone_number, otp))
    otp_row = cursor.fetchone()
    if not otp_row:
        conn.close()
        return jsonify({'error': 'Invalid or expired OTP'}), 400
    otp_id, otp_created = otp_row
    # Check OTP expiry (10 min)
    try:
        otp_time = datetime.strptime(otp_created, '%Y-%m-%d %H:%M:%S')
        if (datetime.now(IST) - otp_time).total_seconds() > 600:
            conn.close()
            return jsonify({'error': 'OTP expired'}), 400
    except Exception:
        pass
    # Mark OTP as used
    cursor.execute('UPDATE otps SET is_used = 1 WHERE id = ?', (otp_id,))
    # Update wallet balance
    cursor.execute('UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?', (amount, session['user_id']))
    # Record transaction
    now_ist = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO transactions (
            transaction_type, from_user_id, to_user_id, from_merchant_id, to_merchant_id, amount, description, created_at
        ) VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?)
    ''', ('DEPOSIT', session['user_id'], float(amount), 'Money added to wallet', now_ist))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Added ₹{amount} to wallet'})

@app.route('/user/send_otp', methods=['POST'])
def user_send_otp():
    phone = request.form['phone_number']
    otp = set_otp(phone)
    #send_otp_sms(phone, otp)
    return jsonify({'success': True, 'message': 'OTP sent to your phone.'})

# Merchant routes
@app.route('/merchant/signup', methods=['GET', 'POST'])
def merchant_signup():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        business_name = request.form['business_name']
        business_address = request.form['business_address']
        business_license = request.form['business_license']
        # Phone number validation
        if not phone_number.isdigit() or len(phone_number) != 10:
            flash('Phone number must be exactly 10 digits!')
            return render_template('merchant_signup.html')
        
        conn = sqlite3.connect('database/db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM merchants WHERE phone_number = ?', (phone_number,))
        if cursor.fetchone():
            flash('Merchant already exists with this phone number!')
            conn.close()
            return render_template('merchant_signup.html')
        
        now_ist = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO merchants (phone_number, business_name, business_address, business_license, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (phone_number, business_name, business_address, business_license, now_ist))
        
        conn.commit()
        conn.close()
        
        flash('Merchant registered successfully! Please login.')
        return redirect(url_for('merchant_login'))
    
    return render_template('merchant_signup.html')

@app.route('/merchant/login', methods=['GET', 'POST'])
def merchant_login():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        otp = request.form['otp']  # In real app, verify OTP
        
        conn = sqlite3.connect('database/db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM merchants WHERE phone_number = ?', (phone_number,))
        merchant = cursor.fetchone()
        conn.close()
        
        if merchant:
            session['merchant_id'] = merchant[0]
            session['user_type'] = 'merchant'
            return redirect(url_for('merchant_dashboard'))
        else:
            flash('Invalid phone number or OTP!')
    
    return render_template('merchant_login.html')

@app.route('/merchant/send_otp', methods=['POST'])
def merchant_send_otp():
    phone = request.form['phone_number']
    otp = set_otp(phone)
    #send_otp_sms(phone, otp)
    return jsonify({'success': True, 'message': 'OTP sent to your phone.'})

@app.route('/merchant/dashboard')
def merchant_dashboard():
    if 'merchant_id' not in session or session['user_type'] != 'merchant':
        return redirect(url_for('merchant_login'))
    
    conn = sqlite3.connect('database/db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM merchants WHERE id = ?', (session['merchant_id'],))
    merchant = cursor.fetchone()
    
    # Get transaction history with user name
    cursor.execute('''
        SELECT t.*, u.full_name FROM transactions t
        LEFT JOIN users u ON t.from_user_id = u.id
        WHERE t.from_merchant_id = ? OR t.to_merchant_id = ?
        ORDER BY t.created_at DESC
        LIMIT 9
    ''', (session['merchant_id'], session['merchant_id']))
    transactions = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard_merchant.html', merchant=merchant, transactions=transactions)

@app.route('/merchant/create_payment', methods=['POST'])
def create_payment():
    if 'merchant_id' not in session or session['user_type'] != 'merchant':
        return jsonify({'error': 'Not authenticated'}), 401
    
    amount = float(request.form['amount'])
    note = request.form['note']
    
    # Store payment request in session for palm scan
    session['payment_request'] = {
        'amount': amount,
        'note': note,
        'merchant_id': session['merchant_id']
    }
    
    return redirect(url_for('payment_scan'))

@app.route('/payment/scan')
def payment_scan():
    if 'payment_request' not in session:
        return redirect(url_for('merchant_dashboard'))
    
    return render_template('payment_scan.html', payment_request=session['payment_request'])

@app.route('/payment/process', methods=['POST'])
def process_payment():
    if 'payment_request' not in session:
        return jsonify({'error': 'No payment request'}), 400
    payment_request = session['payment_request']
    # Get phone number
    phone_number = request.form.get('phone_number')
    if not phone_number:
        return jsonify({'error': 'Phone number required'}), 400
    # Get uploaded palm image
    if 'scanned_palm_image' not in request.files:
        return jsonify({'error': 'No palm image uploaded'}), 400
    file = request.files['scanned_palm_image']
    file.save('debug_uploaded.jpg')  # Save for debugging
    file.stream.seek(0)  # Reset stream for reading again
    npimg = np.frombuffer(file.read(), np.uint8)
    scanned_img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if scanned_img is None:
        return jsonify({'error': 'Image decode failed'}), 400
    landmarks_scan = extract_landmarks(scanned_img)
    if landmarks_scan is None:
        return jsonify({'error': 'No hand detected in the scanned image.'}), 400

    conn = sqlite3.connect('database/db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT id, palm_embedding FROM users WHERE phone_number = ? AND palm_embedding IS NOT NULL', (phone_number,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid phone number or user not registered with palm'}), 404
    user_id, palm_embedding_json = user
    registered_landmarks = json.loads(palm_embedding_json)

    if not compare_landmarks(landmarks_scan, registered_landmarks):
        conn.close()
        return jsonify({'error': 'Palm does not match registered user.'}), 403
    # Check balance
    cursor.execute('SELECT wallet_balance FROM users WHERE id = ?', (user_id,))
    user_row = cursor.fetchone()
    if not user_row or user_row[0] < payment_request['amount']:
        conn.close()
        return jsonify({'error': 'Insufficient balance'}), 400
    # Deduct from user, add to merchant
    cursor.execute('UPDATE users SET wallet_balance = wallet_balance - ? WHERE id = ?', (payment_request['amount'], user_id))
    cursor.execute('UPDATE merchants SET wallet_balance = wallet_balance + ? WHERE id = ?', (payment_request['amount'], payment_request['merchant_id']))
    # Record transaction
    now_ist = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO transactions (
            transaction_type, from_user_id, to_user_id, from_merchant_id, to_merchant_id, amount, description, created_at
        ) VALUES (?, ?, NULL, NULL, ?, ?, ?, ?)
    ''', ('PAYMENT', user_id, payment_request['merchant_id'], float(payment_request['amount']), payment_request['note'], now_ist))
    conn.commit()
    conn.close()
    session.pop('payment_request', None)
    return jsonify({'success': True, 'message': f'Successful transaction: Payment of ${payment_request["amount"]} processed.'})

@app.route('/user/download_transactions')
def download_user_transactions():
    if 'user_id' not in session or session['user_type'] != 'user':
        return redirect(url_for('user_login'))
    conn = sqlite3.connect('database/db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, m.business_name FROM transactions t
        LEFT JOIN merchants m ON t.to_merchant_id = m.id
        WHERE t.from_user_id = ? OR t.to_user_id = ?
        ORDER BY t.created_at DESC
    ''', (session['user_id'], session['user_id']))
    transactions = cursor.fetchall()
    # Shorten date string for PDF
    transactions = [list(t[:8]) + [t[8][:16]] + list(t[9:]) for t in transactions]
    # Fetch user info
    cursor.execute('SELECT full_name, phone_number FROM users WHERE id = ?', (session['user_id'],))
    user_row = cursor.fetchone()
    user_info = {'full_name': user_row[0], 'phone_number': user_row[1]} if user_row else {}
    conn.close()
    # Read logo as base64
    with open('static/CO.png', 'rb') as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    # Render HTML for PDF
    rendered = render_template('transactions_pdf.html', transactions=transactions, user_type='user', logo_base64=logo_base64, user_info=user_info, user_id=session['user_id'])
    pdf = io.BytesIO()
    pisa.CreatePDF(io.StringIO(rendered), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name='user_transactions.pdf', mimetype='application/pdf')

@app.route('/merchant/download_transactions')
def download_merchant_transactions():
    if 'merchant_id' not in session or session['user_type'] != 'merchant':
        return redirect(url_for('merchant_login'))
    conn = sqlite3.connect('database/db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, u.full_name FROM transactions t
        LEFT JOIN users u ON t.from_user_id = u.id
        WHERE t.from_merchant_id = ? OR t.to_merchant_id = ?
        ORDER BY t.created_at DESC
    ''', (session['merchant_id'], session['merchant_id']))
    transactions = cursor.fetchall()
    # Shorten date string for PDF
    transactions = [list(t[:8]) + [t[8][:16]] + list(t[9:]) for t in transactions]
    # Fetch merchant info
    cursor.execute('SELECT business_name, business_license, phone_number FROM merchants WHERE id = ?', (session['merchant_id'],))
    merchant_row = cursor.fetchone()
    merchant_info = {'business_name': merchant_row[0], 'business_license': merchant_row[1], 'phone_number': merchant_row[2]} if merchant_row else {}
    conn.close()
    # Read logo as base64
    with open('static/CO.png', 'rb') as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    # Render HTML for PDF
    rendered = render_template('transactions_pdf.html', transactions=transactions, user_type='merchant', logo_base64=logo_base64, merchant_info=merchant_info)
    pdf = io.BytesIO()
    pisa.CreatePDF(io.StringIO(rendered), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name='merchant_transactions.pdf', mimetype='application/pdf')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
