from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import os
import time

app = Flask(__name__)
app.secret_key = 'medical_super_secret_key'

def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            conn = mysql.connector.connect(
                host='db',
                user=os.environ.get('MYSQL_USER', 'medical_user'),
                password=os.environ.get('MYSQL_PASSWORD', 'medical_pass'),
                database=os.environ.get('MYSQL_DATABASE', 'medical_db')
            )
            return conn
        except mysql.connector.Error as e:
            print(f"DB接続エラー: {e}")
            retries -= 1
            time.sleep(2)
    return None

def init_db():
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor(buffered=True)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL, password_hash VARCHAR(255) NOT NULL, role ENUM('doctor', 'caregiver', 'family') NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # ★進化1：patientsテーブルに user_id（誰の患者か）を追加！
    cursor.execute('''CREATE TABLE IF NOT EXISTS patients (patient_id INT AUTO_INCREMENT PRIMARY KEY, patient_name VARCHAR(100) NOT NULL, user_id INT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS vitals (record_id INT AUTO_INCREMENT PRIMARY KEY, patient_id INT, user_id INT, temperature FLOAT, blood_pressure_high INT, blood_pressure_low INT, pulse INT, memo TEXT, measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (patient_id) REFERENCES patients(patient_id), FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'テスト介護士'")
    res_caregiver = cursor.fetchone()
    if res_caregiver is not None and res_caregiver[0] == 0:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES ('テスト介護士', 'pass123', 'caregiver')")
        
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'テスト医師'")
    res_doctor = cursor.fetchone()
    if res_doctor is not None and res_doctor[0] == 0:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES ('テスト医師', 'pass123', 'doctor')")
        
    cursor.execute("SELECT COUNT(*) FROM patients")
    res_patient = cursor.fetchone()
    if res_patient is not None and res_patient[0] == 0:
        # ★ダミー患者も「テスト介護士（user_id: 1）」に紐付けておく
        cursor.execute("INSERT INTO patients (patient_name, user_id) VALUES ('金子おじいちゃん', 1)")

    conn.commit()
    cursor.close()
    conn.close()

init_db()

# --------------------------------------------------------
# 🔐 ログイン・ログアウト・新規アカウント登録
# --------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, role FROM users WHERE username = %s AND password_hash = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                session['user_id'] = user[0]
                session['role'] = user[1]
                
                if session['role'] == 'doctor' or session['role'] == 'family':
                    return redirect(url_for('view_records'))
                else:
                    return redirect(url_for('index'))
            else:
                return render_template('login.html', error="名前かパスワードが違います")
                
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return render_template('register.html', error="その名前はすでに使われています")
            
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", (username, password, role))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
            
    return render_template('register.html')

# --------------------------------------------------------
# 👤 新規患者の登録処理
# --------------------------------------------------------
@app.route('/register_patient', methods=['GET', 'POST'])
def register_patient():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        patient_name = request.form.get('patient_name')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # ★進化2：誰が登録したか（session['user_id']）も一緒に保存！
            cursor.execute("INSERT INTO patients (patient_name, user_id) VALUES (%s, %s)", (patient_name, session['user_id']))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

    return render_template('register_patient.html')

# --------------------------------------------------------
# 📝 入力画面（介護士用）
# --------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    patients = []
    if conn:
        cursor = conn.cursor()
        # ★進化3：「自分のuser_id」と紐づいている患者だけを引っ張ってくる！
        cursor.execute("SELECT patient_id, patient_name FROM patients WHERE user_id = %s", (session['user_id'],))
        patients = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('index.html', patients=patients)

@app.route('/submit', methods=['POST'])
def submit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    patient_id = request.form.get('patient_id')
    temperature = request.form.get('temperature')
    bp_high = request.form.get('blood_pressure_high')
    bp_low = request.form.get('blood_pressure_low')
    pulse = request.form.get('pulse')
    memo = request.form.get('memo')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO vitals (patient_id, user_id, temperature, blood_pressure_high, blood_pressure_low, pulse, memo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (patient_id, session['user_id'], temperature, bp_high, bp_low, pulse, memo))
            conn.commit()
            return render_template('success.html')
        except mysql.connector.Error as err:
            conn.rollback()
            return f"<div style='text-align:center; margin-top:50px;'><h3>エラーが発生しました！</h3><p style='color:red;'>{err}</p><a href='/'>入力画面に戻る</a></div>"
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn.is_connected():
                conn.close()

    return "データベースに接続できませんでした"

# --------------------------------------------------------
# 📊 カルテ確認画面（医師用）
# --------------------------------------------------------
@app.route('/view')
def view_records():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    records = []
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DATE_FORMAT(v.measured_at, '%Y/%m/%d %H:%i'), p.patient_name, v.temperature, v.blood_pressure_high, v.blood_pressure_low, v.pulse, u.username, v.memo
            FROM vitals v
            JOIN patients p ON v.patient_id = p.patient_id
            JOIN users u ON v.user_id = u.user_id
            ORDER BY v.measured_at DESC
        ''')
        records = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('view.html', records=records)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)