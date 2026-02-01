from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# ==============================
# Database Configuration
# ==============================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password",
    database="opportunity_connect"
)

cursor = db.cursor(dictionary=True)

# ==============================
# Home Route
# ==============================
@app.route("/")
def home():
    return jsonify({"message": "Opportunity Connect Backend Running"})

# ==============================
# User Registration
# ==============================
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    full_name = data["full_name"]
    email = data["email"]
    password = generate_password_hash(data["password"])
    location = data.get("location")
    skills = data.get("skills")
    interests = data.get("interests")

    query = """
    INSERT INTO users (full_name, email, password, location, skills, interests)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (full_name, email, password, location, skills, interests))
        db.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except:
        return jsonify({"error": "Email already exists"}), 400

# ==============================
# User Login
# ==============================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user["password"], password):
        return jsonify({
            "message": "Login successful",
            "user_id": user["user_id"],
            "role": user["role"]
        })
    return jsonify({"error": "Invalid credentials"}), 401

# ==============================
# Add Opportunity (Admin)
# ==============================
@app.route("/add-opportunity", methods=["POST"])
def add_opportunity():
    data = request.json
    query = """
    INSERT INTO opportunities
    (title, description, category, eligibility, organization, location, deadline, apply_link)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cursor.execute(query, (
        data["title"],
        data["description"],
        data["category"],
        data.get("eligibility"),
        data.get("organization"),
        data.get("location"),
        data.get("deadline"),
        data.get("apply_link")
    ))
    db.commit()
    return jsonify({"message": "Opportunity added successfully"})

# ==============================
# Get All Opportunities
# ==============================
@app.route("/opportunities", methods=["GET"])
def get_opportunities():
    cursor.execute("SELECT * FROM opportunities ORDER BY created_at DESC")
    return jsonify(cursor.fetchall())

# ==============================
# Apply for Opportunity
# ==============================
@app.route("/apply", methods=["POST"])
def apply():
    data = request.json
    query = """
    INSERT INTO applications (user_id, opportunity_id)
    VALUES (%s, %s)
    """
    cursor.execute(query, (data["user_id"], data["opportunity_id"]))
    db.commit()
    return jsonify({"message": "Application submitted"})

# ==============================
# Save Opportunity
# ==============================
@app.route("/save", methods=["POST"])
def save_opportunity():
    data = request.json
    query = """
    INSERT INTO saved_opportunities (user_id, opportunity_id)
    VALUES (%s, %s)
    """
    cursor.execute(query, (data["user_id"], data["opportunity_id"]))
    db.commit()
    return jsonify({"message": "Opportunity saved"})

# ==============================
# Get User Applications
# ==============================
@app.route("/my-applications/<int:user_id>")
def my_applications(user_id):
    query = """
    SELECT o.title, o.category, a.status, a.applied_at
    FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.opportunity_id
    WHERE a.user_id = %s
    """
    cursor.execute(query, (user_id,))
    return jsonify(cursor.fetchall())

# ==============================
# Basic Recommendation Logic
# ==============================
@app.route("/recommendations/<int:user_id>")
def recommend(user_id):
    cursor.execute("SELECT skills, interests, location FROM users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()

    query = """
    SELECT * FROM opportunities
    WHERE location=%s OR eligibility LIKE %s
    LIMIT 5
    """
    cursor.execute(query, (user["location"], f"%{user['skills']}%"))
    return jsonify(cursor.fetchall())

# ==============================
# Run Server
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
