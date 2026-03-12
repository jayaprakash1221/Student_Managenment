from flask import Flask, render_template, request, redirect, flash, session, Response
import mysql.connector
import csv
from io import StringIO
from werkzeug.security import check_password_hash, generate_password_hash
import os


# -------- HELPER FUNCTIONS --------

def check_login():
    return "user" in session


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1221",
        database="students_db"
    )


# ✅ FIXED FLASK CONFIG (IMPORTANT CHANGE)
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

app.secret_key = "mysecretkey"


# -------- HOME ROUTE --------

@app.route("/")
def home():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template("index.html", total_students=total_students)


# -------- LOGIN SYSTEM --------

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login_check", methods=["POST"])
def login_check():

    username = request.form["username"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT username, password, role FROM users WHERE username=%s"

    cursor.execute(query, (username,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and check_password_hash(user[1], password):
        session["user"] = username
        session["role"] = user[2]
        flash("Login Successful!")
        return redirect("/view")
    else:
        flash("Invalid Username or Password")
        return redirect("/login")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged Out Successfully!")
    return redirect("/login")


# -------- USER REGISTRATION --------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        hashed = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hashed, "admin"))

        conn.commit()

        cursor.close()
        conn.close()

        flash("User Registered Successfully!")
        return redirect("/login")

    return render_template("register.html")


# -------- STUDENT MANAGEMENT ROUTES --------

@app.route("/add")
def add():

    if not check_login():
        return redirect("/login")

    return render_template("add_student.html")


@app.route("/view")
def view():

    if not check_login():
        return redirect("/login")

    page = request.args.get("page", 1, type=int)
    per_page = 5

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total = cursor.fetchone()[0]

    offset = (page - 1) * per_page

    cursor.execute("SELECT * FROM students LIMIT %s OFFSET %s", (per_page, offset))
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    total_pages = (total // per_page) + (1 if total % per_page != 0 else 0)

    return render_template(
        "view_students.html",
        students=students,
        page=page,
        total_pages=total_pages
    )


@app.route("/add_student", methods=["POST"])
def add_student():

    if not check_login():
        return redirect("/login")

    name = request.form["name"]
    course = request.form["course"]
    email = request.form["email"]
    phone = request.form["phone"]

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "INSERT INTO students (SNAME, COURSE, EMAIL, PHONE) VALUES (%s, %s, %s, %s)"
    values = (name, course, email, phone)

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

    flash("Student Added Successfully!")
    return redirect("/view")


@app.route("/delete/<int:id>")
def delete_student(id):

    if not check_login():
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "DELETE FROM students WHERE SID = %s"
    cursor.execute(query, (id,))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Student Deleted Successfully!")
    return redirect("/view")


@app.route("/edit/<int:id>")
def edit_student(id):

    if not check_login():
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE SID = %s", (id,))
    student = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_student.html", student=student)


@app.route("/update/<int:id>", methods=["POST"])
def update_student(id):

    if not check_login():
        return redirect("/login")

    name = request.form["name"]
    course = request.form["course"]
    email = request.form["email"]
    phone = request.form["phone"]

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    UPDATE students
    SET SNAME=%s, COURSE=%s, EMAIL=%s, PHONE=%s
    WHERE SID=%s
    """

    values = (name, course, email, phone, id)

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

    flash("Student Updated Successfully!")
    return redirect("/view")


@app.route("/search", methods=["GET"])
def search_student():

    if not check_login():
        return redirect("/login")

    keyword = request.args.get("keyword")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM students WHERE sname LIKE %s OR course LIKE %s"
    value = ("%" + keyword + "%", "%" + keyword + "%")

    cursor.execute(query, value)
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("view_students.html", students=students)


@app.route("/export")
def export_csv():

    if not check_login():
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)

    writer.writerow(["ID", "Name", "Course", "Email", "Phone"])

    for s in students:
        writer.writerow(s)

    output = si.getvalue()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=students.csv"}
    )


if __name__ == "__main__":
    app.run(debug=True)
