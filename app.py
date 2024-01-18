from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    login_required,
    logout_user,
    current_user,
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "s4135w+r-0^+@**u8d1g*-3s%y)bk(b^a83v%m7udf1+f1abp^"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"

login_manager = LoginManager()
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = "login"

CORS(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    cart = db.relationship("Cart", backref="user", lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if "username" in data and "password" in data:
        user = User(username=data["username"], password=data["password"])
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Account created successfully"})

    return jsonify({"message": "Invalid data"}), 400


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get("username")).first()

    if user and data.get("password") == user.password:
        login_user(user)
        return jsonify({"message": "Logged in successfully"})

    return jsonify({"message": "Unauthorized. Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successfully"})


@app.route("/api/products/add", methods=["POST"])
@login_required
def add_product():
    data = request.json
    if "name" in data and "price" in data:
        product = Product(
            name=data["name"], price=data["price"], description=data.get("description", "")
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product added successfully"})

    return jsonify({"message": "Invalid product data"}), 400


@app.route("/api/products/delete/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully"})

    return jsonify({"message": "Product not found"}), 404


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "description": product.description,
            }
        )

    return jsonify({"message": "Product not found"}), 404


@app.route("/api/products/update/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    data = request.json
    if "name" in data:
        product.name = data["name"]

    if "price" in data:
        product.price = data["price"]

    if "description" in data:
        product.description = data["description"]

    db.session.commit()
    return jsonify({"message": "Product updated successfully"})


@app.route("/api/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    products_list = []

    if not products:
        return jsonify({"message": "No products found"}), 404

    for product in products:
        products_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        products_list.append(products_data)

    return jsonify(products_list)


@app.route("/api/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    user = User.query.get(int(current_user.id))
    product = Product.query.get(product_id)

    if user and product:
        cart = Cart(user_id=user.id, product_id=product.id)
        db.session.add(cart)
        db.session.commit()
        return jsonify({"message": "Added to the cart succesfully"})

    return jsonify({"message": "Failed to add item to the cart"}), 400


@app.route("/api/cart/remove/<int:product_id>", methods=["DELETE"])
@login_required
def remove_from_cart(product_id):
    cart = Cart.query.filter_by(user_id=int(current_user.id), product_id=product_id).first()

    if cart:
        db.session.delete(cart)
        db.session.commit()
        return jsonify({"message": "Item removed from the cart succesfully"})

    return jsonify({"message": "Failed to remove item from the cart"}), 400


@app.route("/api/cart", methods=["GET"])
@login_required
def view_cart():
    user = User.query.get(int(current_user.id))
    cart = user.cart
    cart_data = []

    if not cart:
        return jsonify({"message": "No products found in the cart"}), 404

    for item in cart:
        product = Product.query.get(item.product_id)
        cart_data.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
            }
        )

    return jsonify(cart_data)


@app.route("/api/cart/checkout", methods=["POST"])
@login_required
def checkout():
    user = User.query.get(int(current_user.id))
    cart = user.cart

    if not cart:
        return jsonify({"message": "No products found in the cart"}), 404

    for item in cart:
        db.session.delete(item)

    db.session.commit()
    return jsonify({"message": "Checkout successfull. Car has been cleared"})


if __name__ == "__main__":
    app.run(debug=True)
