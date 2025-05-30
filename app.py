from flask import Flask, request, redirect, url_for, render_template, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from route_optimizer import optimize_delivery_route, RouteOptimizer

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_for_development')

# Get Google Maps API key from environment
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not GOOGLE_MAPS_API_KEY:
    raise ValueError("Google Maps API key not found in environment variables")

# Database setup (SQLite for simplicity)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///delivery_boys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration (Gmail as an example)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Initialize database, mail, and login manager
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# DeliveryBoy model (Database schema)
class DeliveryBoy(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Increased length for hashed passwords
    verification_code = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship with deliveries
    deliveries = db.relationship('Delivery', backref='delivery_boy', lazy=True)

# Delivery Location model
class DeliveryLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship with deliveries
    deliveries = db.relationship('Delivery', backref='location', lazy=True)

# Delivery model (assigns delivery boys to locations)
class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    delivery_boy_id = db.Column(db.Integer, db.ForeignKey('delivery_boy.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('delivery_location.id'), nullable=False)
    status = db.Column(db.String(50), default="Pending")  # Pending, In Progress, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    order_number = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)

# Add this new model for depot locations
class DeliveryDepot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Add this new model for assignments
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    delivery_boy_id = db.Column(db.Integer, db.ForeignKey('delivery_boy.id'), nullable=False)
    source_lat = db.Column(db.Float, nullable=False)
    source_lng = db.Column(db.Float, nullable=False)
    dest_lat = db.Column(db.Float, nullable=False)
    dest_lng = db.Column(db.Float, nullable=False)
    waypoints = db.Column(db.Text, nullable=True)  # "lat1,lng1;lat2,lng2"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Active")
    delivery_boy = db.relationship('DeliveryBoy', backref='assignments')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return DeliveryBoy.query.get(int(user_id))

# Helper function to generate a random verification code
def generate_verification_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Helper function to generate a random order number
def generate_order_number():
    return f"ORD-{random.randint(1000, 9999)}"

# Route to register a new delivery boy
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    # Generate a verification code
    verification_code = generate_verification_code()

    # Check if the email already exists in the database
    existing_delivery_boy = DeliveryBoy.query.filter_by(email=email).first()
    if existing_delivery_boy:
        flash('Email already registered. Please log in or use another email.', 'danger')
        return redirect(url_for('register'))

    # Hash the password
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    try:
        # Create a new delivery boy record
        new_delivery_boy = DeliveryBoy(
            name=name, 
            email=email, 
            password=hashed_password, 
            verification_code=verification_code,
            status="Pending"
        )

        # Add to the database
        db.session.add(new_delivery_boy)
        db.session.commit()

        # Send verification email
        verification_url = url_for('confirm_email', code=verification_code, _external=True)
        msg = Message(
            "Please verify your email - DeliveryMS",
            recipients=[email],
            body=f"""
Hello {name},

Thank you for registering with DeliveryMS. Please click the link below to verify your email address:

{verification_url}

If you did not register for this account, please ignore this email.

Best regards,
DeliveryMS Team
            """
        )
        mail.send(msg)
        flash('Registration successful! Please check your email for verification link. Check your spam folder if not found.', 'success')
        print(f"Verification email sent to {email} with code {verification_code}")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {str(e)}")
        flash('An error occurred during registration. Please try again or contact support.', 'danger')
        return redirect(url_for('register'))

    return redirect(url_for('login'))

@app.route("/confirm/<code>")
def confirm_email(code):
    try:
        # Query the delivery boy by the verification code
        delivery_boy = DeliveryBoy.query.filter_by(verification_code=code).first()

        if delivery_boy:
            if delivery_boy.status == "Confirmed":
                flash('Email already verified. Please login.', 'info')
            else:
                # Update the status to confirmed
                delivery_boy.status = "Confirmed"
                db.session.commit()
                flash(f'Email confirmed! Welcome, {delivery_boy.name}!', 'success')
                print(f"User {delivery_boy.email} verified successfully")
        else:
            flash('Invalid verification code.', 'danger')
            print(f"Invalid verification code attempted: {code}")
            
    except Exception as e:
        print(f"Error during email confirmation: {str(e)}")
        flash('An error occurred during email verification. Please try again or contact support.', 'danger')
    
    return redirect(url_for('login'))

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
        
    email = request.form["email"]
    password = request.form["password"]
    remember = True if request.form.get("remember") else False

    # Find user by email
    user = DeliveryBoy.query.filter_by(email=email).first()

    # Check if user exists and password is correct
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.', 'danger')
        return redirect(url_for('login'))
    
    # Check if user is verified
    if user.status != "Confirmed":
        flash('Your account is not verified yet. Please check your email for verification link.', 'warning')
        return redirect(url_for('login'))

    # Log in the user
    login_user(user, remember=remember)
    
    # Redirect to dashboard
    return redirect(url_for('dashboard'))

# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route("/delivery-boys")
@login_required
def show_delivery_boys():
    delivery_boys = DeliveryBoy.query.all()
    return render_template("delivery_boys.html", delivery_boys=delivery_boys)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register-form")
def register_form():
    return render_template("register.html")

@app.route("/login-form")
def login_form():
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    # Get current time and date for the dashboard
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%A, %B %d, %Y")
    
    # Get user's deliveries
    user_deliveries = Delivery.query.filter_by(delivery_boy_id=current_user.id).all()
    
    # Count deliveries by status
    total_deliveries = len(user_deliveries)
    active_deliveries = len([d for d in user_deliveries if d.status == "In Progress"])
    pending_orders = len([d for d in user_deliveries if d.status == "Pending"])
    completed_deliveries = len([d for d in user_deliveries if d.status == "Completed"])
    
    # Calculate earnings (example: $10 per delivery)
    total_earnings = completed_deliveries * 10
    
    # Get recent deliveries
    recent_deliveries = Delivery.query.filter_by(delivery_boy_id=current_user.id).order_by(Delivery.created_at.desc()).limit(5).all()
    
    return render_template(
        "dashboard.html", 
        current_user=current_user,
        current_time=current_time,
        current_date=current_date,
        total_deliveries=total_deliveries,
        active_deliveries=active_deliveries,
        pending_orders=pending_orders,
        total_earnings=total_earnings,
        recent_deliveries=recent_deliveries
    )

# Admin routes for managing deliveries
@app.route("/admin/locations", methods=["GET", "POST"])
@login_required
def manage_locations():
    if request.method == "POST":
        address = request.form.get("address")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        new_location = DeliveryLocation(address=address, latitude=latitude, longitude=longitude)
        db.session.add(new_location)
        db.session.commit()
        return redirect(url_for("manage_locations"))
    locations = DeliveryLocation.query.all()
    locations_dicts = [
        {
            'id': loc.id,
            'address': loc.address,
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'created_at': loc.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for loc in locations
    ]
    delivery_boys = DeliveryBoy.query.filter_by(status="Confirmed").all()
    return render_template(
        "admin/locations.html",
        locations=locations_dicts,
        delivery_boys=delivery_boys,
        google_maps_api_key=GOOGLE_MAPS_API_KEY
    )

@app.route("/admin/locations/<int:location_id>", methods=["DELETE"])
@login_required
def delete_location(location_id):
    location = DeliveryLocation.query.get_or_404(location_id)
    
    # Check if location has any associated deliveries
    if location.deliveries:
        return jsonify({"success": False, "message": "Cannot delete location with active deliveries"})
    
    db.session.delete(location)
    db.session.commit()
    
    return jsonify({"success": True})

@app.route("/admin/assign-delivery", methods=["GET", "POST"])
@login_required
def assign_delivery():
    if request.method == "POST":
        delivery_boy_id = int(request.form["delivery_boy_id"])
        location_id = int(request.form["location_id"])
        order_number = request.form["order_number"]
        customer_name = request.form["customer_name"]
        customer_phone = request.form["customer_phone"]
        notes = request.form.get("notes")
        
        # Create new delivery
        new_delivery = Delivery(
            delivery_boy_id=delivery_boy_id,
            location_id=location_id,
            order_number=order_number,
            customer_name=customer_name,
            customer_phone=customer_phone,
            notes=notes,
            status="pending"
        )
        
        db.session.add(new_delivery)
        db.session.commit()
        
        flash('Delivery assigned successfully!', 'success')
        return redirect(url_for('assign_delivery'))
    
    # Get active delivery boys and locations for the form
    delivery_boys = DeliveryBoy.query.filter_by(status="Confirmed").all()
    locations = DeliveryLocation.query.all()
    deliveries = Delivery.query.order_by(Delivery.created_at.desc()).all()
    
    return render_template("admin/assign_delivery.html",
                         delivery_boys=delivery_boys,
                         locations=locations,
                         deliveries=deliveries)

@app.route("/admin/deliveries/<int:delivery_id>", methods=["GET"])
@login_required
def get_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    
    return jsonify({
        "id": delivery.id,
        "order_number": delivery.order_number,
        "delivery_boy": {
            "id": delivery.delivery_boy.id,
            "name": delivery.delivery_boy.name
        },
        "location": {
            "id": delivery.location.id,
            "address": delivery.location.address
        },
        "customer_name": delivery.customer_name,
        "customer_phone": delivery.customer_phone,
        "status": delivery.status,
        "created_at": delivery.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "notes": delivery.notes
    })

@app.route("/admin/deliveries/<int:delivery_id>", methods=["DELETE"])
@login_required
def delete_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    
    db.session.delete(delivery)
    db.session.commit()
    
    return jsonify({"success": True})

@app.route("/admin/deliveries/<int:delivery_id>/status", methods=["POST"])
@login_required
def update_delivery_status(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    new_status = request.json.get("status")
    
    if new_status not in ["pending", "in_progress", "completed"]:
        return jsonify({"success": False, "message": "Invalid status"})
    
    delivery.status = new_status
    if new_status == "completed":
        delivery.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({"success": True})

@app.route("/admin/optimize-route", methods=["GET", "POST"])
@login_required
def optimize_route():
    # Get all available locations
    delivery_locations = DeliveryLocation.query.all()
    
    # For now, use the same locations as depots (you can add proper depot management later)
    depot_locations = DeliveryLocation.query.all()
    
    if request.method == "POST":
        start_location_id = int(request.form["start_location"])
        delivery_points = request.form.getlist("delivery_points")
        algorithm = request.form["algorithm"]
        return_to_depot = bool(request.form.get("return_to_depot", True))
        
        # Convert delivery points to integers
        delivery_points = [int(point_id) for point_id in delivery_points]
        
        # Get location objects for all selected points
        selected_locations = DeliveryLocation.query.filter(DeliveryLocation.id.in_(delivery_points)).all()
        start_location = DeliveryLocation.query.get(start_location_id)
        
        # Convert locations to dictionary format for the optimizer
        locations_data = [
            {
                'id': start_location.id,
                'latitude': start_location.latitude,
                'longitude': start_location.longitude,
                'address': start_location.address,
                'is_depot': True
            }
        ]
        
        # Add delivery points
        locations_data.extend([
            {
                'id': loc.id,
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'address': loc.address,
                'is_depot': False
            }
            for loc in selected_locations
        ])
        
        # If return to depot is enabled, add the depot as the final destination
        if return_to_depot:
            locations_data.append({
                'id': start_location.id,
                'latitude': start_location.latitude,
                'longitude': start_location.longitude,
                'address': start_location.address,
                'is_depot': True
            })
        
        # Create optimizer instance and get optimized route
        optimizer = RouteOptimizer(locations_data)
        optimized_route = optimizer.optimize_route(start_location_id, algorithm)
        optimized_route['return_to_depot'] = return_to_depot
        
        return render_template(
            "admin/optimize_route.html",
            delivery_locations=delivery_locations,
            depot_locations=depot_locations,
            optimized_route=optimized_route,
            google_maps_api_key=GOOGLE_MAPS_API_KEY
        )
        
    return render_template(
        "admin/optimize_route.html",
        delivery_locations=delivery_locations,
        depot_locations=depot_locations,
        google_maps_api_key=GOOGLE_MAPS_API_KEY
    )

@app.route("/admin/view-route/<int:assignment_id>")
@login_required
def view_route(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    waypoints = []
    if assignment.waypoints:
        for wp in assignment.waypoints.split(";"):
            lat, lng = map(float, wp.split(","))
            waypoints.append({"lat": lat, "lng": lng})
    return render_template(
        "admin/view_route.html",
        assignment=assignment,
        waypoints=waypoints,
        google_maps_api_key=GOOGLE_MAPS_API_KEY
    )

@app.route("/admin/assign-route", methods=["GET", "POST"])
@login_required
def assign_route():
    if request.method == "POST":
        delivery_boy_id = request.form.get("delivery_boy_id")
        source_lat = float(request.form.get("source_lat"))
        source_lng = float(request.form.get("source_lng"))
        dest_lat = float(request.form.get("dest_lat"))
        dest_lng = float(request.form.get("dest_lng"))
        waypoints = request.form.get("waypoints")  # e.g., "lat1,lng1;lat2,lng2"
        new_assignment = Assignment(
            delivery_boy_id=delivery_boy_id,
            source_lat=source_lat,
            source_lng=source_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            waypoints=waypoints
        )
        db.session.add(new_assignment)
        db.session.commit()
        flash("Route assigned!", "success")
        return redirect(url_for("view_route", assignment_id=new_assignment.id))
    delivery_boys = DeliveryBoy.query.filter_by(status="Confirmed").all()
    return render_template("admin/assign_route.html", delivery_boys=delivery_boys, google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route("/admin/save-assignment", methods=["POST"])
@login_required
def save_assignment():
    data = request.get_json()
    try:
        assignment = Assignment(
            delivery_boy_id=int(data['delivery_boy_id']),
            source_lat=float(data['source_lat']),
            source_lng=float(data['source_lng']),
            dest_lat=float(data['dest_lat']),
            dest_lng=float(data['dest_lng']),
            waypoints=data['waypoints']
        )
        db.session.add(assignment)
        db.session.commit()
        return jsonify({"success": True, "assignment_id": assignment.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

@app.route("/admin/route-planner")
@login_required
def route_planner():
    delivery_boys = DeliveryBoy.query.filter_by(status="Confirmed").all()
    return render_template(
        "admin/route_planner.html",
        delivery_boys=delivery_boys,
        google_maps_api_key=GOOGLE_MAPS_API_KEY
    )

# Run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
