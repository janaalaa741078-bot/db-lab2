import os
import pymysql
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "registration"),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("todos_page"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("All fields are required", "error")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            db = get_db()
            with db.cursor() as cursor:
                query = "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s);"
                cursor.execute(query, (email, name, password_hash))
                db.commit()
                
                cursor.execute("SELECT user_id, name FROM users WHERE email = %s;", (email,))
                user = cursor.fetchone()
                session["user_id"] = user["user_id"]
                session["name"] = user["name"]
            db.close()
            return redirect(url_for("todos_page"))
        except pymysql.err.IntegrityError:
            flash("Email Already Exists", "error")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required", "error")
            return render_template("login.html")

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT user_id, name, password_hash FROM users WHERE email = %s;", (email,))
            user = cursor.fetchone()
        db.close()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            flash("Invalid email or password", "error")
            return render_template("login.html")

        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        return redirect(url_for("todos_page"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/todos", methods=["GET", "POST"])
def todos_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    db = get_db()

    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add":
            title = request.form.get("title", "").strip()
            if title and len(title) <= 200:
                with db.cursor() as cursor:
                    cursor.execute("INSERT INTO todos (user_id, title) VALUES (%s, %s);", (user_id, title))
                    db.commit()

        elif action == "edit":
            todo_id = request.form.get("todo_id")
            title = request.form.get("title", "").strip()
            if title and len(title) <= 200:
                with db.cursor() as cursor:
                    cursor.execute("UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s;", (title, todo_id, user_id))
                    db.commit()

        elif action == "toggle":
            todo_id = request.form.get("todo_id")
            is_done = request.form.get("is_done")
            new_status = 0 if is_done == "1" else 1
            with db.cursor() as cursor:
                cursor.execute("UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s;", (new_status, todo_id, user_id))
                db.commit()

        elif action == "delete":
            todo_id = request.form.get("todo_id")
            with db.cursor() as cursor:
                cursor.execute("DELETE FROM todos WHERE todo_id = %s AND user_id = %s;", (todo_id, user_id))
                db.commit()

    with db.cursor() as cursor:
        cursor.execute("SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC;", (user_id,))
        todos = cursor.fetchall()
    db.close()

    return render_template("todos.html", todos=todos, name=session.get("name"))

if __name__ == "__main__":
    app.run(debug=True)