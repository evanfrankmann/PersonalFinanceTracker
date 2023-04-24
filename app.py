from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Dodecahedron0916!@localhost/personal_finance_tracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define your models here (Users, Accounts, Transactions, and Categories)
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    accounts = db.relationship('Account', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Numeric(15, 2), nullable=False)
    transactions = db.relationship('Transaction', backref='account', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.Enum('Income', 'Expense'), nullable=False)
    transactions = db.relationship('Transaction', backref='category', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)


# Define your routes and views here (register, login, dashboard, etc.)
from flask import render_template, request, redirect, url_for, flash, session

@app.route('/')
def home():
    return render_template('index.html')

from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email already exists. Please log in or use a different email.", "error")
            return redirect(url_for('register'))

        # Register user and add to the database
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Validate user and log in
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Log out user and redirect to the home page
    if 'user_id' in session:
        session.pop('user_id')
        flash("Logged out successfully.", "success")
    return redirect(url_for('home'))


from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    accounts = user.accounts
    transactions = Transaction.query.filter(Transaction.account_id.in_([a.id for a in accounts])).all()
    categories = user.categories

    return render_template('dashboard.html', accounts=accounts, transactions=transactions, categories=categories)

@app.route('/accounts')
@login_required
def accounts():
    user = User.query.get(session['user_id'])
    accounts = user.accounts

    return render_template('accounts.html', accounts=accounts)

@app.route('/transactions')
@login_required
def transactions():
    user = User.query.get(session['user_id'])
    accounts = user.accounts
    transactions = Transaction.query.filter(Transaction.account_id.in_([a.id for a in accounts])).all()

    return render_template('transactions.html', transactions=transactions)

@app.route('/categories')
@login_required
def categories():
    user = User.query.get(session['user_id'])
    categories = user.categories

    return render_template('categories.html', categories=categories)


@app.route('/add_account', methods=['POST'])
@login_required
def add_account():
    account_name = request.form['account_name']
    initial_balance = request.form['initial_balance']
    user_id = session['user_id']

    new_account = Account(name=account_name, balance=initial_balance, user_id=user_id)
    db.session.add(new_account)
    db.session.commit()

    flash("Account added successfully.", "success")
    return redirect(url_for('accounts'))

@app.route('/edit_account/<int:account_id>', methods=['GET', 'POST'])
@login_required
def edit_account(account_id):
    account = Account.query.get_or_404(account_id)
    if request.method == 'POST':
        account_name = request.form['account_name']
        account.name = account_name
        db.session.commit()

        flash("Account updated successfully.", "success")
        return redirect(url_for('accounts'))

    return render_template('edit_account.html', account=account)

@app.route('/delete_account/<int:account_id>')
@login_required
def delete_account(account_id):
    account = Account.query.get_or_404(account_id)
    db.session.delete(account)
    db.session.commit()

    flash("Account deleted successfully.", "success")
    return redirect(url_for('accounts'))


if __name__ == '__main__':
    app.run(debug=True)
