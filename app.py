import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Janaalaa2005",
        database="todo_db",
        port=3307
    )

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('todos'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('todos'))
        else:
            return render_template('login.html', error="Invalid email or password.")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match.")

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            db.close()
            return render_template('register.html', error="Email is already registered.")

        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/todos')
def todos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    filter_type = request.args.get('filter', 'all')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if filter_type == 'open':
        cursor.execute("SELECT * FROM todos WHERE user_id = %s AND completed = FALSE ORDER BY id DESC", (user_id,))
    elif filter_type == 'done':
        cursor.execute("SELECT * FROM todos WHERE user_id = %s AND completed = TRUE ORDER BY id DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM todos WHERE user_id = %s ORDER BY id DESC", (user_id,))
    
    tasks = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS open_count FROM todos WHERE user_id = %s AND completed = FALSE", (user_id,))
    open_count = cursor.fetchone()['open_count']

    cursor.close()
    db.close()

    return render_template('todos.html', tasks=tasks, open_count=open_count, current_filter=filter_type)

@app.route('/add', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task_title = request.form.get('task')
    if task_title:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (%s, %s, FALSE)", (session['user_id'], task_title))
        db.commit()
        cursor.close()
        db.close()

    return redirect(url_for('todos'))

@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_todo(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE todos SET completed = NOT completed WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('todos'))

@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_todo(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    new_task_title = request.form.get('task')
    if new_task_title:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE todos SET task = %s WHERE id = %s AND user_id = %s", (new_task_title, task_id, session['user_id']))
        db.commit()
        cursor.close()
        db.close()

    return redirect(url_for('todos'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_todo(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM todos WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('todos'))

if __name__ == '__main__':
    app.run(debug=True)