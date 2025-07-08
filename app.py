from flask import Flask, render_template, request, redirect, url_for, flash, session 
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import boto3
import smtplib
import logging
import uuid
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
users = {}


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY='simple_secure_key_9472',
    THEME_COLOR="#ffb6c1"
)

# -------------------- Logger Setup --------------------
log_folder = 'logs'
os.makedirs(log_folder, exist_ok=True)
log_file = os.path.join(log_folder, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -------------------- AWS Setup --------------------
AWS_REGION = 'us-east-1'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:216989138822:homemadepickles'

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
orders_table = dynamodb.Table('PickleOrders')
users_table = dynamodb.Table('users')
sns = boto3.client('sns', region_name=AWS_REGION)

# Email settings
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

@app.context_processor
def inject_theme():
    return {"color": app.config["THEME_COLOR"], "year": datetime.now().year}

# -------------------- Product Inventory --------------------
products = {
    "mango": {"name": "Mango Pickle", "price": 200, "stock": 10, "image": "mango pickle.webp"},
    "tomato": {"name": "Tomato Pickle", "price": 150, "stock": 7, "image": "Tomato pickle.webp"},
    "lemon": {"name": "Lemon Pickle", "price": 180, "stock": 8, "image": "Lemon pickle.jpg"},
    "chicken": {"name": "Chicken Pickle", "price": 250, "stock": 9, "image": "chicken pickle.webp"},
    "fish": {"name": "Fish Pickle", "price": 250, "stock": 6, "image": "Fish pickle.webp"},
    "mutton": {"name": "Mutton Pickle", "price": 300, "stock": 7, "image": "Mutton pickle.webp"},
    "banana_chips": {"name": "Banana Chips", "price": 100, "stock": 8, "image": "Banana Chips.jpg"},
    "ama_papad": {"name": "Ama Papad", "price": 80, "stock": 8, "image": "Aam papad.jpg"},
    "chekka_pakodi": {"name": "Chekka Pakodi", "price": 110, "stock": 5, "image": "Chekka Pakodi.jpg"}
}

def get_products(prefix=None):
    if not prefix:
        return products
    return {k: v for k, v in products.items() if k.startswith(prefix)}

# -------------------- Routes --------------------

@app.route('/')
def home():
    user = session.get('user')  # ✅ FIXED: get user safely
    if user:
        return render_template('home.html', user=user)
    return redirect(url_for('login'))
@app.route('/index.html')
def index():
    return render_template("index.html")


@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = users.get(email)
        if user and user['password'] == password:
            session['user'] = email
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid email or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route("/veg-pickles.html")
def veg_pickles():
    return render_template("veg-pickles.html", items={
        k: v for k, v in products.items() if k in ["mango", "tomato", "lemon"]
    })

@app.route("/nonveg-pickles.html")
def nonveg_pickles():
    return render_template("nonveg-pickles.html", items={
        k: v for k, v in products.items() if k in ["chicken", "fish", "mutton"]
    })

@app.route("/snacks.html")
def snacks():
    return render_template("snacks.html", items={
        k: v for k, v in products.items() if k in ["banana_chips", "chekka_pakodi", "ama_papad"]
    })

@app.route("/cart.html")
def cart():
    return render_template("cart.html")

@app.route("/add/<pid>")
def add_to_cart(pid):
    if pid not in products:
        flash("Invalid product", "danger")
        return redirect(request.referrer or url_for("home"))
    if products[pid]["stock"] <= 0:
        flash("Out of stock", "warning")
    else:
        products[pid]["stock"] -= 1
        cart = session.setdefault("cart", {})
        cart[pid] = cart.get(pid, 0) + 1
        session.modified = True
        flash("Added to cart!", "success")
    return redirect(request.referrer or url_for("home"))

@app.route("/clear-cart")
def clear_cart():
    session.pop("cart", None)
    flash("Cart cleared", "info")
    return redirect(url_for("home"))

@app.route('/checkout.html', methods=['GET', 'POST'])
def checkout():
    if 'user' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        notes = request.form.get('notes')
        payment = request.form.get('payment')

        if not name or not email or not phone or not address or not payment:
            flash('All fields including payment method are required!', 'danger')
            return redirect(url_for('checkout'))

        order_id = str(uuid.uuid4())[:8].upper()
        session['cart'] = []

        flash(f'Order #{order_id} placed successfully!', 'success')
        return redirect(url_for('success'))

    return render_template('checkout.html')


@app.route('/success.html')
def success():
    return render_template('success.html')

@app.route("/signup.html", methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            return render_template('signup.html', error="Passwords do not match!")

        # Save user to dictionary (in real app, use database)
        users[email] = {
            'name': name,
            'password': password  # For security, use hashing (next step)
        }

        flash("Signup successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route("/about.html")
def about():
    return render_template("about.html")

@app.route("/contact.html", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Message sent!", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
