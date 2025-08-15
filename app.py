from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, SECRET_KEY
from werkzeug.security import check_password_hash
from datetime import date
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = SECRET_KEY

# -------------------- DB Connection --------------------
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# -------------------- HOME --------------------
@app.route("/")
def home():
    return render_template("home.html")

# -------------------- ADMIN LOGIN --------------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE username=%s", (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["user_id"] = admin["id"]
            session["username"] = admin["username"]
            session["role"] = "admin"
            flash("✅ Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("❌ Invalid admin username or password!", "danger")

    return render_template("admin_login.html")
# -------------------- TEACHER LOGIN --------------------
@app.route("/teacher_login", methods=["GET", "POST"])
def teacher_login():
    # Always load teacher list for the dropdown
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, username FROM teachers ORDER BY name")
    teacher_rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if request.method == "POST":
        # value will be the username now (no mapping needed)
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM teachers WHERE username=%s", (username,))
        teacher = cursor.fetchone()
        cursor.close()
        conn.close()

        if teacher and check_password_hash(teacher["password"], password):
            session["user_id"] = teacher["id"]
            session["username"] = teacher["username"]
            session["role"] = "teacher"
            session["class_assigned"] = teacher["class_assigned"]
            flash("✅ Teacher login successful!", "success")
            return redirect(url_for("teacher_dashboard"))
        else:
            flash("❌ Invalid teacher username or password!", "danger")

    # GET: render with DB teachers list
    return render_template("teacher_login.html", teachers=teacher_rows)

# -------------------- DASHBOARDS --------------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html", username=session["username"])

@app.route("/teacher_dashboard")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect(url_for("teacher_login"))
    return render_template("teacher_dashboard.html", username=session["username"], classes=session["class_assigned"])

# -------------------- BACK URL HELPER --------------------
def get_back_url():
    if session.get("role") == "admin":
        return url_for("admin_dashboard")
    elif session.get("role") == "teacher":
        return url_for("teacher_dashboard")
    return url_for("home")

# -------------------- MARK ATTENDANCE --------------------
@app.route("/mark", methods=["GET", "POST"])
def mark_attendance():
    if "role" not in session:
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get classes list based on role
    if session["role"] == "admin":
        cursor.execute("SELECT * FROM classes ORDER BY id")
        classes = cursor.fetchall()
    else:
        assigned_ids = [int(c.strip()) for c in session["class_assigned"].split(",")]
        placeholders = ",".join(["%s"] * len(assigned_ids))
        cursor.execute(f"SELECT * FROM classes WHERE id IN ({placeholders}) ORDER BY id", tuple(assigned_ids))
        classes = cursor.fetchall()

    selected_class_id = request.args.get("class_id")

    # POST: handle marking attendance
    if request.method == "POST":
        student_id = request.form["student_id"]
        att_date = request.form["date"]
        status = request.form["status"]

        try:
            cursor.execute("""
                INSERT INTO attendance (student_id, date, status, marked_by)
                VALUES (%s, %s, %s, %s)
            """, (student_id, att_date, status, session["username"]))
            conn.commit()
            flash("✅ Attendance marked successfully!", "success")
        except mysql.connector.Error as e:
            if e.errno == 1062:  # Duplicate entry error
                flash("⚠ Attendance already marked for this student on this date.", "warning")
            else:
                flash(f"❌ Database error: {e}", "danger")

        cursor.close()
        conn.close()
        # Redirect so flash message shows instantly without resubmitting form
        return redirect(url_for("mark_attendance", class_id=selected_class_id))

    # GET: fetch students list if class is selected
    students = []
    if selected_class_id:
        cursor.execute("""
            SELECT s.id, s.name, s.roll_no
            FROM students s
            WHERE s.class_id = %s
            ORDER BY s.name
        """, (selected_class_id,))
        students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "mark_attendance.html",
        classes=classes,
        students=students,
        selected_class_id=selected_class_id,
        today=date.today().isoformat(),
        back_url=get_back_url()
    )

# -------------------- VIEW ATTENDANCE --------------------
@app.route("/view", methods=["GET"])
def view_attendance():
    if "role" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if session["role"] == "admin":
        cursor.execute("SELECT * FROM classes ORDER BY id")
        classes = cursor.fetchall()
    else:
        assigned_ids = [int(c.strip()) for c in session["class_assigned"].split(",")]
        placeholders = ",".join(["%s"] * len(assigned_ids))
        cursor.execute(f"SELECT * FROM classes WHERE id IN ({placeholders}) ORDER BY id", tuple(assigned_ids))
        classes = cursor.fetchall()

    selected_class_id = request.args.get("class_id")
    records = []

    if selected_class_id:
        cursor.execute("""
            SELECT a.id, s.name, s.roll_no, c.class_name, a.date, a.status, a.marked_by
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN classes c ON s.class_id = c.id
            WHERE c.id = %s
            ORDER BY a.date DESC
        """, (selected_class_id,))
        records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "view_attendance.html",
        records=records,
        classes=classes,
        selected_class_id=selected_class_id,
        back_url=get_back_url()
    )

# -------------------- DOWNLOAD CSV --------------------
# Select Class for CSV Download
@app.route("/download_select", methods=["GET", "POST"])
def download_select():
    if "role" not in session:
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Classes based on role
    if session["role"] == "admin":
        cursor.execute("SELECT * FROM classes ORDER BY id")
        classes = cursor.fetchall()
    else:
        assigned_ids = [int(c.strip()) for c in session["class_assigned"].split(",")]
        placeholders = ",".join(["%s"] * len(assigned_ids))
        cursor.execute(f"SELECT * FROM classes WHERE id IN ({placeholders}) ORDER BY id", tuple(assigned_ids))
        classes = cursor.fetchall()

    cursor.close()
    conn.close()

    if request.method == "POST":
        class_id = request.form["class_id"]
        return redirect(url_for("download_csv", class_id=class_id))

    return render_template("download_select.html", classes=classes)


# Actual CSV Download
@app.route("/download_csv")
def download_csv():
    if "role" not in session:
        return redirect(url_for("home"))

    class_id = request.args.get("class_id")
    conn = get_db_connection()

    query = """
        SELECT s.name AS Student, s.roll_no AS RollNo, c.class_name AS Class,
               a.date AS Date, a.status AS Status, a.marked_by AS MarkedBy
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN classes c ON s.class_id = c.id
    """
    params = []
    if class_id:
        query += " WHERE c.id = %s"
        params.append(class_id)
    query += " ORDER BY a.date DESC"

    df = pd.read_sql(query, conn, params=params)
    conn.close()

    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="attendance_report.csv")

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    role = session.get("role")  # logout ke pehle role store kar lo
    session.clear()
    flash("ℹ️ Logged out successfully", "info")

    if role == "admin":
        return redirect(url_for("admin_login"))
    elif role == "teacher":
        return redirect(url_for("teacher_login"))
    else:
        return redirect(url_for("home"))


# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)
