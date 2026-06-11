from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ajshop-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ajshop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'jwt-secret-ajshop-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# =====================
# DATABASE MODELS
# =====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')  # admin, moderator, member, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    members = db.relationship('Member', backref='user', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Member(db.Model):
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    membership_type = db.Column(db.String(50))  # gold, silver, bronze, free
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.username,
            'membership_type': self.membership_type,
            'status': self.status,
            'join_date': self.join_date.isoformat(),
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'points': self.points,
            'created_at': self.created_at.isoformat()
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.username,
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }

# =====================
# AUTHENTICATION ROUTES
# =====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({'message': 'Account is inactive'}), 401
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log activity
        activity = Activity(
            user_id=user.id,
            action='LOGIN',
            description=f'User {username} logged in',
            ip_address=request.remote_addr
        )
        db.session.add(activity)
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    
    if not username or not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 409
    
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role='user'
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201

@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    activity = Activity(
        user_id=user_id,
        action='LOGOUT',
        description=f'User {user.username} logged out',
        ip_address=request.remote_addr
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'message': 'Logout successful'}), 200

# =====================
# DASHBOARD ROUTES
# =====================

@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role not in ['admin', 'moderator']:
        return redirect(url_for('login_page'))
    
    return render_template('dashboard.html', user=user)

@app.route('/api/dashboard/stats')
@jwt_required()
def dashboard_stats():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'moderator']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    stats = {
        'total_users': User.query.count(),
        'total_members': Member.query.count(),
        'total_products': Product.query.count(),
        'active_members': Member.query.filter_by(status='active').count(),
        'total_revenue': sum([p.price * (max(0, p.stock)) for p in Product.query.all()]),
        'recent_activities': [a.to_dict() for a in Activity.query.order_by(Activity.created_at.desc()).limit(10).all()]
    }
    
    return jsonify(stats), 200

# =====================
# MEMBERS MANAGEMENT
# =====================

@app.route('/api/members', methods=['GET'])
@jwt_required()
def get_members():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'moderator']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    members = Member.query.all()
    return jsonify([m.to_dict() for m in members]), 200

@app.route('/api/members/create', methods=['POST'])
@jwt_required()
def create_member():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can create members'}), 403
    
    data = request.get_json()
    target_user_id = data.get('user_id')
    membership_type = data.get('membership_type', 'free')
    
    if not target_user_id:
        return jsonify({'message': 'Missing user_id'}), 400
    
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'message': 'User not found'}), 404
    
    member = Member(
        user_id=target_user_id,
        membership_type=membership_type,
        status='active'
    )
    
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'message': 'Member created', 'member': member.to_dict()}), 201

@app.route('/api/members/<int:member_id>', methods=['PUT'])
@jwt_required()
def update_member(member_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can update members'}), 403
    
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404
    
    data = request.get_json()
    if 'membership_type' in data:
        member.membership_type = data['membership_type']
    if 'status' in data:
        member.status = data['status']
    if 'points' in data:
        member.points = data['points']
    
    member.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Member updated', 'member': member.to_dict()}), 200

@app.route('/api/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def delete_member(member_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can delete members'}), 403
    
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404
    
    db.session.delete(member)
    db.session.commit()
    
    return jsonify({'message': 'Member deleted'}), 200

# =====================
# USERS MANAGEMENT
# =====================

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@app.route('/api/users/create', methods=['POST'])
@jwt_required()
def create_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can create users'}), 403
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'user')
    
    if not username or not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409
    
    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=role
    )
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created', 'user': new_user.to_dict()}), 201

@app.route('/api/users/<int:target_user_id>', methods=['PUT'])
@jwt_required()
def update_user(target_user_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can update users'}), 403
    
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    if 'email' in data:
        target_user.email = data['email']
    if 'full_name' in data:
        target_user.full_name = data['full_name']
    if 'role' in data and user.id != target_user_id:
        target_user.role = data['role']
    if 'is_active' in data:
        target_user.is_active = data['is_active']
    
    target_user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'User updated', 'user': target_user.to_dict()}), 200

@app.route('/api/users/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(target_user_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can delete users'}), 403
    
    if user_id == target_user_id:
        return jsonify({'message': 'Cannot delete your own account'}), 400
    
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'message': 'User not found'}), 404
    
    db.session.delete(target_user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted'}), 200

# =====================
# PRODUCTS MANAGEMENT
# =====================

@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_products():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'moderator']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products]), 200

@app.route('/api/products/create', methods=['POST'])
@jwt_required()
def create_product():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can create products'}), 403
    
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    
    if not name or not price:
        return jsonify({'message': 'Missing required fields'}), 400
    
    product = Product(
        name=name,
        description=data.get('description'),
        price=price,
        stock=data.get('stock', 0),
        category=data.get('category')
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'message': 'Product created', 'product': product.to_dict()}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can update products'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    data = request.get_json()
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = data['price']
    if 'stock' in data:
        product.stock = data['stock']
    if 'category' in data:
        product.category = data['category']
    if 'is_active' in data:
        product.is_active = data['is_active']
    
    product.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Product updated', 'product': product.to_dict()}), 200

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Only admins can delete products'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'message': 'Product deleted'}), 200

# =====================
# ERROR HANDLERS
# =====================

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'message': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'message': 'Forbidden'}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
