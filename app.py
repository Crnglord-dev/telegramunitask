import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import os

# -----------------------------------------------------------------------------
# Создание приложения Flask и настройка параметров
# -----------------------------------------------------------------------------
app = Flask(__name__, instance_relative_config=True)

# Указываем путь к базе данных (SQLite) и секретный ключ для шифрования сессий.
# Используем app.instance_path для хранения базы данных.
db_path = os.path.join(app.instance_path, 'data.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SECRET_KEY'] = 'SAWw7ptVAUtR'

# Убедимся, что папка instance существует.
os.makedirs(app.instance_path, exist_ok=True)

# -----------------------------------------------------------------------------
# Инициализируем SQLAlchemy для работы с базой данных
# -----------------------------------------------------------------------------
db = SQLAlchemy(app)

# -----------------------------------------------------------------------------
# Настройка Flask-Login
# -----------------------------------------------------------------------------
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -----------------------------------------------------------------------------
# Словарь пользователей
# -----------------------------------------------------------------------------
users = {
    "admin": {"password": "12345", "role": "admin"},
    "user":  {"password": "54321",  "role": "user"}
}

# -----------------------------------------------------------------------------
# Модель пользователя (для Flask-Login)
# -----------------------------------------------------------------------------
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.role = users[username]["role"]

@login_manager.user_loader
def load_user(username):
    if username in users:
        return User(username)
    return None

# -----------------------------------------------------------------------------
# Маршруты приложения
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Неправильное имя пользователя или пароль', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/statistics', methods=['GET'])
@login_required
def statistics():
    if current_user.role != 'admin':
        return '''
        <html>
            <body style="text-align: center; padding: 50px;">
                <h1 style="color: red; font-size: 36px;">Доступно только администратору!</h1>
                <p style="font-size: 20px;">У вас нет необходимых прав для доступа к этой странице.</p>
            </body>
        </html>
        ''', 403

    # Подключаемся к базе данных в папке instance
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM message_log")
    data = cursor.fetchall()
    conn.close()

    return render_template('stat.html', data=data)

# -----------------------------------------------------------------------------
# Функция инициализации базы данных
# -----------------------------------------------------------------------------
def init_db():
    with app.app_context():
        db.create_all()

# -----------------------------------------------------------------------------
# Точка входа
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
