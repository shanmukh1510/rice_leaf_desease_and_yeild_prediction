"""
SmartRice – AI Powered Rice Disease Detection & Yield Prediction System
With Full Authentication: Login, Signup, Profile, Session Management
"""
import sys, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import uuid
import sqlite3
import joblib
import hashlib
import secrets
import numpy as np
import pandas as pd
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash)
from werkzeug.utils import secure_filename
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

# ─── App Configuration ────────────────────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
MODEL_DIR = os.path.join(BASE_DIR, "models")

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))
app.config["SECRET_KEY"] = "smartrice_secure_key_2024_xyz"
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ─── Disease Classes & Treatments ────────────────────────────────────────────

DISEASE_CLASSES = [
    "Bacterial leaf blight", "Blast", "Brown spot",
    "Leaf smut", "Tungro", "healthy",
]

TREATMENTS = {
    "Bacterial leaf blight": {
        "icon": "🦠", "severity": "High", "color": "danger",
        "description": "Bacterial infection causing water-soaked to yellowish stripes on leaf margins.",
        "treatment": [
            "Apply copper-based bactericides (Copper oxychloride @ 2.5 g/L)",
            "Use Streptomycin sulfate @ 0.5 g/L + Copper oxychloride @ 2 g/L",
            "Drain fields and avoid excessive nitrogen fertilization",
            "Use resistant varieties like IR64, Pusa Basmati",
            "Remove and destroy infected plant debris",
        ],
        "prevention": "Use certified disease-free seeds, practice crop rotation, and avoid excess nitrogen.",
    },
    "Blast": {
        "icon": "💥", "severity": "Very High", "color": "danger",
        "description": "Fungal disease causing diamond-shaped lesions with grey centers and brown borders.",
        "treatment": [
            "Spray Tricyclazole @ 0.6 g/L water immediately",
            "Apply Propiconazole @ 1 mL/L or Isoprothiolane @ 1.5 mL/L",
            "Use Carbendazim + Mancozeb combination fungicide",
            "Avoid excessive nitrogen — reduces blast susceptibility",
            "Silicon fertilization improves blast resistance",
        ],
        "prevention": "Plant resistant varieties, avoid dense planting, and ensure good drainage.",
    },
    "Brown spot": {
        "icon": "🟤", "severity": "Medium", "color": "warning",
        "description": "Fungal disease causing brown oval spots on leaves, leading to reduced grain quality.",
        "treatment": [
            "Apply Mancozeb @ 2.5 g/L or Iprobenfos @ 1.5 mL/L",
            "Spray Propiconazole @ 1 mL/L at early infection stage",
            "Improve soil nutrition — apply balanced NPK fertilizers",
            "Use potassium silicate to strengthen cell walls",
            "Remove heavily infected leaves before spraying",
        ],
        "prevention": "Apply balanced fertilizers, use treated seeds, and avoid water stress.",
    },
    "Healthy": {
        "icon": "✅", "severity": "None", "color": "success",
        "description": "The rice leaf is healthy with no signs of disease or infection.",
        "treatment": [
            "Continue regular monitoring every 7-10 days",
            "Maintain optimal irrigation and drainage",
            "Apply balanced NPK fertilizers as per soil test",
            "Practice preventive spraying of mild fungicides",
            "Monitor for early signs of pest infestations",
        ],
        "prevention": "Keep up good agricultural practices and regular field scouting.",
    },
    "Leaf smut": {
        "icon": "⬛", "severity": "Medium", "color": "warning",
        "description": "Fungal disease causing small, angular, black spots on leaf surface.",
        "treatment": [
            "Apply Propiconazole @ 1 mL/L or Hexaconazole @ 2 mL/L",
            "Spray Carbendazim @ 1 g/L at early infection",
            "Remove and burn infected plant material",
            "Avoid high humidity conditions by improving air circulation",
            "Apply Thiram-based seed treatment @ 3 g/kg seed",
        ],
        "prevention": "Seed treatment with fungicides, avoid high plant density.",
    },
    "Tungro": {
        "icon": "🟡", "severity": "Very High", "color": "danger",
        "description": "Viral disease transmitted by green leafhoppers causing yellow-orange discoloration.",
        "treatment": [
            "Control vector (green leafhopper) using Imidacloprid @ 0.5 mL/L",
            "Apply Thiamethoxam @ 0.2 g/L for leafhopper control",
            "Remove and destroy infected plants immediately",
            "Use resistant varieties: TN1, IR36, MTU 7029",
            "Spray Carbofuran granules @ 20 kg/ha in nursery",
        ],
        "prevention": "Use resistant varieties, synchronize planting, control leafhopper vectors.",
    },
}

# ─── Database ─────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'farmer',
            state TEXT DEFAULT NULL,
            farm_size TEXT DEFAULT NULL,
            joined_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS disease_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            image_name TEXT NOT NULL,
            predicted_class TEXT NOT NULL,
            confidence REAL NOT NULL,
            date_time TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS yield_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            rainfall_mm REAL, avg_temp_c REAL, min_temp_c REAL, max_temp_c REAL,
            soil_ph REAL, nitrogen_kg_ha REAL, phosphorus_kg_ha REAL,
            potassium_kg_ha REAL, fertilizer_kg_ha REAL,
            irrigation_type TEXT, season TEXT, rice_variety TEXT, region TEXT,
            predicted_yield REAL NOT NULL, date_time TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return user


@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}


# ─── Model Loading ────────────────────────────────────────────────────────────

dl_model = yield_model = scaler = feature_columns = None


def load_models():
    global dl_model, yield_model, scaler, feature_columns
    try:
        import tensorflow as tf
        for name in ["rice_leaf_disease_model.h5", "rice_leaf_disease_cnn_model.h5"]:
            path = os.path.join(MODEL_DIR, name)
            if os.path.exists(path):
                dl_model = tf.keras.models.load_model(path)
                print(f"[OK] DL Model Loaded: {path}")
                break
        else:
            print(f"[!] No DL model found in {MODEL_DIR}")
    except Exception as e:
        print(f"[ERR] DL error: {e}")
    try:
        rf_path = os.path.join(MODEL_DIR, "rice_yield_model.pkl")
        sc_path = os.path.join(MODEL_DIR, "scaler.pkl")
        col_path = os.path.join(MODEL_DIR, "feature_columns.pkl")
        
        yield_model     = joblib.load(rf_path)
        scaler          = joblib.load(sc_path)
        feature_columns = joblib.load(col_path)
        print("[OK] ML Models loaded successfully")
    except Exception as e:
        print(f"[ERR] ML error: {e}")


load_models()


def allowed_file(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def predict_disease(path):
    if dl_model is None:
        return None, None, "Model not loaded"
    try:
        img = np.expand_dims(np.array(Image.open(path).convert("RGB").resize((224, 224))) / 255.0, 0)
        preds = dl_model.predict(img, verbose=0)
        idx = int(np.argmax(preds[0]))
        return DISEASE_CLASSES[idx], float(np.max(preds[0])) * 100, None
    except Exception as e:
        return None, None, str(e)


def predict_yield(data):
    if not all([yield_model, scaler, feature_columns]):
        return None, "ML models not loaded"
    try:
        df = pd.get_dummies(pd.DataFrame([data])).reindex(columns=feature_columns, fill_value=0)
        return round(float(yield_model.predict(scaler.transform(df))[0]), 2), None
    except Exception as e:
        return None, str(e)


# ════════════════════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════════════════════

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email     = request.form.get("email", "").strip().lower()
        username  = request.form.get("username", "").strip().lower()
        password  = request.form.get("password", "")
        confirm   = request.form.get("confirm_password", "")
        state     = request.form.get("state", "").strip()
        farm_size = request.form.get("farm_size", "").strip()

        errors = []
        if not full_name:         errors.append("Full name is required.")
        if not email or "@" not in email: errors.append("Valid email is required.")
        if len(username) < 3:     errors.append("Username must be at least 3 characters.")
        if len(password) < 6:     errors.append("Password must be at least 6 characters.")
        if password != confirm:   errors.append("Passwords do not match.")

        # Validate
        conn = get_db()
        existing = conn.execute(
            "SELECT * FROM users WHERE LOWER(email)=LOWER(?) OR LOWER(username)=LOWER(?)",
            (email, username)
        ).fetchone()
        conn.close()
        
        if existing:
            errors.append("Email or username already registered.")
        
        if not errors:
            try:
                conn = get_db()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    "INSERT INTO users (full_name,email,username,password_hash,state,farm_size,joined_at) VALUES (?,?,?,?,?,?,?)",
                    (full_name, email, username, hash_password(password), state, farm_size, now)
                )
                conn.commit()
                user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
                conn.close()
                session["user_id"]  = user["id"]
                session["username"] = user["username"]
                flash(f"🎉 Welcome to SmartRice, {full_name}!", "success")
                return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                errors.append("Email or username already registered.")

        for e in errors:
            flash(e, "danger")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password", "")
        remember   = request.form.get("remember")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE LOWER(email)=LOWER(?) OR LOWER(username)=LOWER(?)", 
            (identifier, identifier)
        ).fetchone()
        conn.close()

        if user and user["password_hash"] == hash_password(password):
            session.permanent = bool(remember)
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['full_name']}! 👋", "success")
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully. See you soon! 🌾", "info")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    user = get_current_user()
    conn = get_db()
    d_count = conn.execute("SELECT COUNT(*) FROM disease_predictions WHERE user_id=?", (user["id"],)).fetchone()[0]
    y_count = conn.execute("SELECT COUNT(*) FROM yield_predictions WHERE user_id=?", (user["id"],)).fetchone()[0]
    recent_d = conn.execute("SELECT * FROM disease_predictions WHERE user_id=? ORDER BY id DESC LIMIT 5", (user["id"],)).fetchall()
    recent_y = conn.execute("SELECT * FROM yield_predictions WHERE user_id=? ORDER BY id DESC LIMIT 5", (user["id"],)).fetchall()
    conn.close()
    return render_template("profile.html", user=user,
                           disease_count=d_count, yield_count=y_count,
                           recent_disease=recent_d, recent_yield=recent_y)


# ════════════════════════════════════════════════════════
#  MAIN ROUTES
# ════════════════════════════════════════════════════════

@app.route("/")
def index():
    conn = get_db()
    dc = conn.execute("SELECT COUNT(*) FROM disease_predictions").fetchone()[0]
    yc = conn.execute("SELECT COUNT(*) FROM yield_predictions").fetchone()[0]
    rd = conn.execute("SELECT * FROM disease_predictions ORDER BY id DESC LIMIT 3").fetchall()
    ry = conn.execute("SELECT * FROM yield_predictions ORDER BY id DESC LIMIT 3").fetchall()
    conn.close()
    return render_template("index.html", disease_count=dc, yield_count=yc,
        recent_disease=rd, recent_yield=ry,
        dl_model_status=dl_model is not None, ml_model_status=yield_model is not None)


@app.route("/detect", methods=["GET", "POST"])
@login_required
def detect():
    result = None
    if request.method == "POST":
        f = request.files.get("file")
        if not f or f.filename == "":
            return render_template("detect.html", error="No file selected.")
        if not allowed_file(f.filename):
            return render_template("detect.html", error="Invalid file type. Use PNG/JPG/JPEG/BMP/WEBP.")
        if dl_model is None:
            return render_template("detect.html", error="Disease model not loaded. Place model in models/ folder.")

        fn = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
        fp = os.path.join(app.config["UPLOAD_FOLDER"], fn)
        f.save(fp)

        disease, conf, err = predict_disease(fp)
        if err:
            return render_template("detect.html", error=f"Prediction failed: {err}")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        conn.execute("INSERT INTO disease_predictions (user_id,image_name,predicted_class,confidence,date_time) VALUES (?,?,?,?,?)",
                     (session["user_id"], fn, disease, conf, now))
        conn.commit()
        conn.close()

        result = {"disease": disease, "confidence": round(conf, 2),
                  "image_path": f"uploads/{fn}", "treatment": TREATMENTS.get(disease, TREATMENTS["Healthy"])}

    return render_template("detect.html", result=result)


@app.route("/yield", methods=["GET", "POST"])
@login_required
def yield_pred():
    result = None
    form_data = {}
    if request.method == "POST":
        try:
            form_data = {
                "rainfall_mm": float(request.form.get("rainfall_mm", 0)),
                "avg_temp_c": float(request.form.get("avg_temp_c", 0)),
                "min_temp_c": float(request.form.get("min_temp_c", 0)),
                "max_temp_c": float(request.form.get("max_temp_c", 0)),
                "soil_ph": float(request.form.get("soil_ph", 0)),
                "nitrogen_kg_ha": float(request.form.get("nitrogen_kg_ha", 0)),
                "phosphorus_kg_ha": float(request.form.get("phosphorus_kg_ha", 0)),
                "potassium_kg_ha": float(request.form.get("potassium_kg_ha", 0)),
                "fertilizer_kg_ha": float(request.form.get("fertilizer_kg_ha", 0)),
                "irrigation_type": request.form.get("irrigation_type", "Canal"),
                "season": request.form.get("season", "Kharif"),
                "rice_variety": request.form.get("rice_variety", "IR64"),
                "region": request.form.get("region", "Tamil Nadu"),
            }
        except ValueError as e:
            return render_template("yield.html", error=f"Invalid input: {e}", form_data=form_data)

        if yield_model is None:
            return render_template("yield.html", error="Yield model not loaded.", form_data=form_data)

        pred, err = predict_yield(form_data)
        if err:
            return render_template("yield.html", error=f"Prediction failed: {err}", form_data=form_data)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        conn.execute("""
            INSERT INTO yield_predictions (user_id,rainfall_mm,avg_temp_c,min_temp_c,max_temp_c,soil_ph,
             nitrogen_kg_ha,phosphorus_kg_ha,potassium_kg_ha,fertilizer_kg_ha,irrigation_type,season,
             rice_variety,region,predicted_yield,date_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (session["user_id"], form_data["rainfall_mm"], form_data["avg_temp_c"], form_data["min_temp_c"],
              form_data["max_temp_c"], form_data["soil_ph"], form_data["nitrogen_kg_ha"],
              form_data["phosphorus_kg_ha"], form_data["potassium_kg_ha"], form_data["fertilizer_kg_ha"],
              form_data["irrigation_type"], form_data["season"], form_data["rice_variety"],
              form_data["region"], pred, now))
        conn.commit()
        conn.close()

        if pred >= 6:     rating = {"label": "Excellent", "color": "success", "icon": "🏆", "stars": 5}
        elif pred >= 4.5: rating = {"label": "Good", "color": "primary", "icon": "👍", "stars": 4}
        elif pred >= 3:   rating = {"label": "Average", "color": "warning", "icon": "📊", "stars": 3}
        else:             rating = {"label": "Below Average", "color": "danger", "icon": "⚠️", "stars": 2}

        result = {"yield": pred, "rating": rating, "form_data": form_data}

    return render_template("yield.html", result=result, form_data=form_data)


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    disease_dist  = dict(conn.execute("SELECT predicted_class, COUNT(*) FROM disease_predictions GROUP BY predicted_class").fetchall())
    yield_history = conn.execute("SELECT date_time, predicted_yield, rice_variety FROM yield_predictions ORDER BY id DESC LIMIT 15").fetchall()
    daily_disease = conn.execute("SELECT substr(date_time,1,10) day, COUNT(*) count FROM disease_predictions GROUP BY day ORDER BY day DESC LIMIT 7").fetchall()
    daily_yield   = conn.execute("SELECT substr(date_time,1,10) day, COUNT(*) count FROM yield_predictions GROUP BY day ORDER BY day DESC LIMIT 7").fetchall()
    td = conn.execute("SELECT COUNT(*) FROM disease_predictions").fetchone()[0]
    ty = conn.execute("SELECT COUNT(*) FROM yield_predictions").fetchone()[0]
    ay = conn.execute("SELECT AVG(predicted_yield) FROM yield_predictions").fetchone()[0]
    ac = conn.execute("SELECT AVG(confidence) FROM disease_predictions").fetchone()[0]
    conn.close()
    return render_template("dashboard.html",
        disease_dist=disease_dist, yield_history=list(yield_history),
        daily_disease=list(daily_disease), daily_yield=list(daily_yield),
        total_disease=td, total_yield=ty,
        avg_yield=round(ay, 2) if ay else 0,
        avg_conf=round(ac, 1) if ac else 0)


@app.route("/history")
@login_required
def history():
    conn = get_db()
    dr = conn.execute("SELECT * FROM disease_predictions ORDER BY id DESC LIMIT 50").fetchall()
    yr = conn.execute("SELECT * FROM yield_predictions ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return render_template("history.html", disease_records=dr, yield_records=yr)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/api/stats")
@login_required
def api_stats():
    conn = get_db()
    dd = dict(conn.execute("SELECT predicted_class, COUNT(*) FROM disease_predictions GROUP BY predicted_class").fetchall())
    yd = conn.execute("SELECT predicted_yield, date_time FROM yield_predictions ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return jsonify({"disease_distribution": dd, "yield_history": [{"yield": r[0], "date": r[1]} for r in yd]})



@app.errorhandler(500)
def internal_error(error):
    import traceback
    return f"Internal Server Error: {error}<br><pre>{traceback.format_exc()}</pre>", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)