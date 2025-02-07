from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # "public" or "private"
    income = db.Column(db.Float, default=0.0)  # Product income
    products = db.relationship('Product', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Product {self.name}, ${self.price}>'


# Ensure database tables are created
with app.app_context():
    db.create_all()


# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        account_type = 'private' if int(age) < 18 else 'public'

        new_user = User(username=username, password=hashed_password, age=int(age), account_type=account_type)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


# Profile Route
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


# Upload Product Route
@app.route('/upload_product', methods=['GET', 'POST'])
@login_required
def upload_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])

        new_product = Product(name=name, price=price, user_id=current_user.id)
        current_user.income += price * 0.95  # 5% fee deducted

        db.session.add(new_product)
        db.session.commit()

        flash('Product uploaded successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('upload_product.html')


# Ad Payment Route
@app.route('/advertise', methods=['GET', 'POST'])
@login_required
def advertise():
    if request.method == 'POST':
        ad_amount = float(request.form['amount'])
        # Here you should integrate with a real payment gateway
        flash(f'Advertising payment of ${ad_amount:.2f} processed!', 'success')
        return redirect(url_for('profile'))

    return render_template('advertise.html')


# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


# Home Route
@app.route('/')
def home():
    return render_template('index.html')


# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)
