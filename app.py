from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return render_template("home.html")

# Signup page
@app.route('/signup.html', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        # Save user to database or session here (mocked for now)
        return redirect(url_for('login'))
    return render_template("signup.html")

# Login page
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get data from form
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        dummy_user = {
            'name': 'Deepika',
            'email': 'deepika@gmail.com',
            'password': 'Deepika@123'
        }

        if email == dummy_user['email']:
            if name == dummy_user['name'] and password == dummy_user['password']:
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error="❌ Incorrect name or password")
        else:
            return render_template('login.html', error="❌ Email not found")

    # If GET request, just show form
    return render_template('login.html')

    # If GET request, just show form
    return render_template('login.html')
#Index page
@app.route('/index.html')
def index():
    return render_template("index.html")

# Veg Pickles page
@app.route('/veg-pickles.html')
def veg_pickles():
    return render_template("veg-pickles.html")

# Non-Veg Pickles page
@app.route('/nonveg-pickles.html')
def nonveg_pickles():
    return render_template("nonveg-pickles.html")

# Snacks page
@app.route('/snacks.html')
def snacks():
    return render_template("snacks.html")

# Cart page
@app.route('/cart.html')
def cart():
    return render_template("cart.html")

# Checkout page
@app.route('/checkout.html')
def checkout():
    return render_template("checkout.html")

# Contact page
@app.route('/contact.html')
def contact():
    return render_template("contact.html")

# About page
@app.route('/about.html')
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.run(debug=True)