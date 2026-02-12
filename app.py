import os
import sqlite3
import random
import pickle
import pandas as pd
from flask import Flask, render_template, request
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "health_data.db")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
DATASET_PATH = os.path.join(BASE_DIR, "health_data.csv")

app = Flask(__name__)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        bp INTEGER,
        hr INTEGER,
        sugar INTEGER,
        bmi REAL,
        risk TEXT,
        confidence REAL
    )
    """)

    conn.commit()
    conn.close()

# ---------------- DATASET ----------------
def generate_dataset():
    if os.path.exists(DATASET_PATH):
        return

    data = []
    for _ in range(800):
        age = random.randint(18, 80)
        gender = random.choice([0, 1])
        bp = random.randint(90, 180)
        hr = random.randint(60, 120)
        sugar = random.randint(70, 240)
        bmi = round(random.uniform(18, 40), 1)

        if bp > 160 or sugar > 200 or bmi > 35:
            risk = 2
        elif bp > 130 or sugar > 140 or bmi > 30:
            risk = 1
        else:
            risk = 0

        data.append([age, gender, bp, hr, sugar, bmi, risk])

    pd.DataFrame(
        data,
        columns=["Age","Gender","BP","HR","Sugar","BMI","Risk"]
    ).to_csv(DATASET_PATH, index=False)

# ---------------- MODEL ----------------
def train_model():
    if os.path.exists(MODEL_PATH):
        return (
            pickle.load(open(MODEL_PATH,"rb")),
            pickle.load(open(SCALER_PATH,"rb"))
        )

    df = pd.read_csv(DATASET_PATH)
    X = df.drop("Risk", axis=1)
    y = df["Risk"]

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=1000)
    model.fit(Xs, y)

    pickle.dump(model, open(MODEL_PATH,"wb"))
    pickle.dump(scaler, open(SCALER_PATH,"wb"))
    return model, scaler

init_db()
generate_dataset()
model, scaler = train_model()

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        age = int(request.form["age"])
        gender_text = request.form["gender"]
        gender = 1 if gender_text == "Male" else 0
        bp = int(request.form["bp"])
        hr = int(request.form["hr"])
        sugar = int(request.form["sugar"])
        bmi = float(request.form["bmi"])

        data = scaler.transform([[age, gender, bp, hr, sugar, bmi]])
        pred = model.predict(data)[0]
        prob = model.predict_proba(data)[0]
        confidence = round(max(prob) * 100, 1)

        risk_map = {0: "Normal", 1: "At Risk", 2: "Critical"}
        risk = risk_map[pred]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO patients VALUES (NULL,?,?,?,?,?,?,?,?,?)",
            (name, age, gender_text, bp, hr, sugar, bmi, risk, confidence)
        )

        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            name=name,
            risk=risk,
            confidence=confidence,
            active_page="predict"
        )


    return render_template(
        "index.html",
        active_page="predict"      # ✅ ADD
    )

# ---------------- ANALYTICS ----------------
@app.route("/analytics")
def analytics():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql(
        "SELECT risk, COUNT(*) as count FROM patients GROUP BY risk",
        conn
    )

    total = pd.read_sql(
        "SELECT COUNT(*) as total FROM patients",
        conn
    )["total"][0]

    conn.close()

    # Convert to dict for easy lookup
    counts = {"Normal": 0, "At Risk": 0, "Critical": 0}
    for row in df.itertuples():
        counts[row.risk] = row.count

    # Create pie chart
    import matplotlib
    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    plt.figure(figsize=(5, 5))
    plt.pie(
        counts.values(),
        labels=counts.keys(),
        autopct="%1.1f%%",
        startangle=140
    )
    plt.title("Health Risk Distribution")

    chart_path = os.path.join(BASE_DIR, "static", "risk_chart.png")
    plt.savefig(chart_path)
    plt.close()

    return render_template(
        "analytics.html",
        total=total,
        normal=counts["Normal"],
        at_risk=counts["At Risk"],
        critical=counts["Critical"],
        chart="risk_chart.png",
        active_page="analytics"
    )

# ---------------- RECORDS ----------------
@app.route("/records")
def records():
    conn = sqlite3.connect(DB_PATH)
    rows = pd.read_sql(
        "SELECT * FROM patients ORDER BY id DESC",
        conn
    )
    conn.close()

    return render_template(
        "records.html",
        rows=rows.to_dict(orient="records"),
        active_page="records"      # ✅ ADD
    )

if __name__ == "__main__":
    app.run(debug=True)
