# =========================================================
# ULTRA ADVANCED AI SECURITY SYSTEM
# SPAM + CREDIT CARD FRAUD DETECTION
# =========================================================

from flask import Flask, render_template, request, redirect, session
import sqlite3
import pandas as pd
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.secret_key = "advanced_security_key"

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(
    "database.db",
    check_same_thread=False
)

cursor = conn.cursor()

# USERS TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE,

    password TEXT

)

""")

# SPAM HISTORY TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS spam_history (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT,

    message TEXT,

    result TEXT,

    probability REAL,

    time TEXT

)

""")

# FRAUD HISTORY TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS fraud_history (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT,

    amount REAL,

    location TEXT,

    device TEXT,

    result TEXT,

    probability REAL,

    threat TEXT,

    time TEXT

)

""")

conn.commit()

# =========================================================
# SPAM DATASET
# =========================================================

spam_data = {

    "message":[

        "Win free iphone now",
        "Lottery winner claim money",
        "Free recharge available",
        "Urgent bank update click now",
        "Congratulations you won cash",
        "Limited time offer",

        "Hello friend",
        "Meeting tomorrow",
        "Project discussion",
        "Good morning",
        "Dinner tonight",
        "Call me later"

    ],

    "label":[

        "spam",
        "spam",
        "spam",
        "spam",
        "spam",
        "spam",

        "ham",
        "ham",
        "ham",
        "ham",
        "ham",
        "ham"

    ]

}

spam_df = pd.DataFrame(spam_data)

spam_df['label_num'] = spam_df.label.map({

    'ham':0,
    'spam':1

})

spam_vectorizer = TfidfVectorizer()

X_spam = spam_vectorizer.fit_transform(
    spam_df['message']
)

y_spam = spam_df['label_num']

spam_model = MultinomialNB()

spam_model.fit(
    X_spam,
    y_spam
)

# =========================================================
# FRAUD DATASET
# =========================================================

fraud_data = {

    "amount":[

        50,
        100,
        150,
        200,
        300,
        500,
        700,
        1000,
        2000,
        5000,
        7000,
        10000,
        15000,
        20000,
        30000,
        40000,
        50000,
        60000,
        70000,
        80000

    ],

    "location":[

        "India",
        "India",
        "India",
        "India",
        "India",

        "India",
        "India",
        "India",

        "Russia",
        "Russia",

        "USA",
        "China",

        "Nigeria",
        "Russia",

        "China",
        "Nigeria",

        "USA",
        "Russia",

        "China",
        "Nigeria"

    ],

    "device":[

        "Mobile",
        "Mobile",
        "Laptop",
        "Desktop",
        "Mobile",

        "Laptop",
        "Desktop",
        "Mobile",

        "VPN",
        "VPN",

        "Desktop",
        "Unknown",

        "VPN",
        "Unknown",

        "VPN",
        "Unknown",

        "Desktop",
        "VPN",

        "Unknown",
        "VPN"

    ],

    "fraud":[

        0,
        0,
        0,
        0,
        0,

        0,
        0,
        0,

        1,
        1,

        1,
        1,

        1,
        1,

        1,
        1,

        1,
        1,

        1,
        1

    ]

}

fraud_df = pd.DataFrame(fraud_data)

# =========================================================
# LABEL ENCODING
# =========================================================

location_encoder = LabelEncoder()

device_encoder = LabelEncoder()

fraud_df['location'] = location_encoder.fit_transform(
    fraud_df['location']
)

fraud_df['device'] = device_encoder.fit_transform(
    fraud_df['device']
)

X_fraud = fraud_df[['amount', 'location', 'device']]

y_fraud = fraud_df['fraud']

# =========================================================
# FRAUD MODEL
# =========================================================

fraud_model = RandomForestClassifier(
    n_estimators=100
)

fraud_model.fit(
    X_fraud,
    y_fraud
)

# =========================================================
# HOME
# =========================================================

@app.route('/')
def home():

    return render_template('login.html')

# =========================================================
# REGISTER PAGE
# =========================================================

@app.route('/register')
def register():

    return render_template('register.html')

# =========================================================
# REGISTER USER
# =========================================================

@app.route('/register_user', methods=['POST'])
def register_user():

    username = request.form['username']

    password = request.form['password']

    cursor.execute(

        "SELECT * FROM users WHERE username=?",

        (username,)

    )

    existing_user = cursor.fetchone()

    if existing_user:

        return render_template(

            'register.html',

            error="Username Already Exists"

        )

    cursor.execute("""

    INSERT INTO users
    (username, password)

    VALUES (?, ?)

    """, (

        username,
        password

    ))

    conn.commit()

    return redirect('/')

# =========================================================
# LOGIN
# =========================================================

@app.route('/login', methods=['POST'])
def login():

    username = request.form['username']

    password = request.form['password']

    cursor.execute("""

    SELECT * FROM users

    WHERE username=? AND password=?

    """, (

        username,
        password

    ))

    user = cursor.fetchone()

    if user:

        session['user'] = username

        return redirect('/dashboard')

    else:

        return render_template(

            'login.html',

            error="Invalid Username or Password"

        )

# =========================================================
# DASHBOARD
# =========================================================

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:

        return redirect('/')

    username = session['user']

    cursor.execute("""

    SELECT * FROM spam_history
    WHERE username=?
    ORDER BY id DESC

    """, (

        username,

    ))

    spam_history = cursor.fetchall()

    cursor.execute("""

    SELECT * FROM fraud_history
    WHERE username=?
    ORDER BY id DESC

    """, (

        username,

    ))

    fraud_history = cursor.fetchall()

    return render_template(

        'dashboard.html',

        username=username,

        spam_history=spam_history,

        fraud_history=fraud_history

    )

# =========================================================
# SPAM PREDICTION
# =========================================================

@app.route('/predict_spam', methods=['POST'])
def predict_spam():

    if 'user' not in session:

        return redirect('/')

    username = session['user']

    message = request.form['message']

    transformed = spam_vectorizer.transform(
        [message]
    )

    prediction = spam_model.predict(
        transformed
    )[0]

    probability = round(

        spam_model.predict_proba(
            transformed
        )[0][1] * 100,

        2

    )

    if prediction == 1:

        result = "SPAM"

    else:

        result = "SAFE"

    current_time = datetime.now().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    cursor.execute("""

    INSERT INTO spam_history
    (username, message, result, probability, time)

    VALUES (?, ?, ?, ?, ?)

    """, (

        username,
        message,
        result,
        probability,
        current_time

    ))

    conn.commit()

    return redirect('/dashboard')

# =========================================================
# FRAUD PREDICTION
# =========================================================

@app.route('/predict_fraud', methods=['POST'])
def predict_fraud():

    if 'user' not in session:

        return redirect('/')

    username = session['user']

    amount = float(
        request.form['amount']
    )

    location = request.form['location']

    device = request.form['device']

    encoded_location = location_encoder.transform(
        [location]
    )[0]

    encoded_device = device_encoder.transform(
        [device]
    )[0]

    prediction = fraud_model.predict([[
        amount,
        encoded_location,
        encoded_device
    ]])[0]

    probability = round(

        fraud_model.predict_proba([[
            amount,
            encoded_location,
            encoded_device
        ]])[0][1] * 100,

        2

    )

    # EXTRA SECURITY RULES

    if amount > 10000:

        prediction = 1

    if location in ["Russia", "Nigeria", "China"]:

        prediction = 1

    if device in ["VPN", "Unknown"]:

        prediction = 1

    # RESULT

    if prediction == 1:

        result = "FRAUD"

    else:

        result = "SAFE"

    # THREAT LEVEL

    if probability > 80:

        threat = "HIGH RISK"

    elif probability > 50:

        threat = "MEDIUM RISK"

    else:

        threat = "LOW RISK"

    current_time = datetime.now().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    cursor.execute("""

    INSERT INTO fraud_history
    (
        username,
        amount,
        location,
        device,
        result,
        probability,
        threat,
        time
    )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        username,
        amount,
        location,
        device,
        result,
        probability,
        threat,
        current_time

    ))

    conn.commit()

    return redirect('/dashboard')

# =========================================================
# LOGOUT
# =========================================================

@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/')

# =========================================================
# RUN
# =========================================================

if __name__ == '__main__':

    app.run(debug=True)