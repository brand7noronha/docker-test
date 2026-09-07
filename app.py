from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

# Secret key is used for Flask sessions
app.secret_key = "my-secret-key"

# Database location
DATABASE = os.path.join("instance", "ecommerce.db")


# ---------------------------------------------------
# DATABASE FUNCTIONS
# ---------------------------------------------------

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    # Make sure the instance folder exists
    os.makedirs("instance", exist_ok=True)

    connection = get_db_connection()

    # Create products table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image TEXT NOT NULL
        )
    """)

    # Check whether products already exist
    product_count = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    # Insert some sample products only when database is empty
    if product_count == 0:

        products = [
            (
                "Laptop",
                "Basic laptop suitable for students and everyday work.",
                55000,
                "https://images.unsplash.com/photo-1496181133206-80ce9b88a853"
            ),
            (
                "Smartphone",
                "Modern smartphone with a large display and good camera.",
                25000,
                "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9"
            ),
            (
                "Headphones",
                "Wireless headphones with comfortable ear cushions.",
                3000,
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e"
            ),
            (
                "Smart Watch",
                "Smart watch for fitness tracking and notifications.",
                5000,
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30"
            )
        ]

        connection.executemany("""
            INSERT INTO products
            (name, description, price, image)
            VALUES (?, ?, ?, ?)
        """, products)

    connection.commit()
    connection.close()


# ---------------------------------------------------
# HOME / PRODUCT LIST
# ---------------------------------------------------

@app.route("/")
def index():

    search = request.args.get("search", "")

    connection = get_db_connection()

    if search:
        products = connection.execute("""
            SELECT * FROM products
            WHERE name LIKE ?
            OR description LIKE ?
        """, (
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:
        products = connection.execute(
            "SELECT * FROM products"
        ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        products=products,
        search=search
    )


# ---------------------------------------------------
# PRODUCT DETAILS
# ---------------------------------------------------

@app.route("/product/<int:product_id>")
def product(product_id):

    connection = get_db_connection()

    product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    connection.close()

    if product is None:
        return "Product not found", 404

    return render_template(
        "product.html",
        product=product
    )


# ---------------------------------------------------
# ADD TO CART
# ---------------------------------------------------

@app.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):

    cart = session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    session["cart"] = cart

    return redirect(url_for("cart"))


# ---------------------------------------------------
# CART
# ---------------------------------------------------

@app.route("/cart")
def cart():

    cart = session.get("cart", {})

    products = []

    connection = get_db_connection()

    total = 0

    for product_id, quantity in cart.items():

        product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if product:

            subtotal = product["price"] * quantity

            products.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal
            })

            total += subtotal

    connection.close()

    return render_template(
        "cart.html",
        products=products,
        total=total
    )


# ---------------------------------------------------
# CHECKOUT
# ---------------------------------------------------

@app.route("/checkout")
def checkout():

    cart = session.get("cart", {})

    if not cart:
        return redirect(url_for("cart"))

    connection = get_db_connection()

    total = 0

    for product_id, quantity in cart.items():

        product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if product:
            total += product["price"] * quantity

    connection.close()

    return render_template(
        "checkout.html",
        total=total
    )


# ---------------------------------------------------
# PAYMENT
# ---------------------------------------------------

@app.route("/payment", methods=["POST"])
def payment():

    name = request.form.get("name")
    email = request.form.get("email")

    cart = session.get("cart", {})

    if not cart:
        return redirect(url_for("cart"))

    # For this beginner project we are using
    # mock payment instead of a real payment gateway.

    session["cart"] = {}

    return f"""
        <h1>Payment Successful!</h1>

        <p>Thank you, {name}.</p>
        <p>Confirmation email: {email}</p>

        <a href="{url_for('index')}">
            Continue Shopping
        </a>
    """


# ---------------------------------------------------
# APPLICATION START
# ---------------------------------------------------

if __name__ == "__main__":

    initialize_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
