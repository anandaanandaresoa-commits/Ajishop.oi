from app import app, db, User, Member, Product, Activity
from datetime import datetime, timedelta

def init_database():
    """Initialize database with sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print('✓ Database tables created')
        
        # Check if admin already exists
        admin = User.query.filter_by(username='Ajipang').first()
        if not admin:
            # Create admin user
            admin = User(
                username='Ajipang',
                email='admin@ajshop.oi',
                full_name='Admin AJSHOP',
                role='admin',
                is_active=True
            )
            admin.set_password('775')
            db.session.add(admin)
            print('✓ Admin user created (Ajipang:775)')
        
        # Create sample users
        sample_users = [
            {'username': 'john_doe', 'email': 'john@ajshop.oi', 'name': 'John Doe', 'role': 'moderator'},
            {'username': 'jane_smith', 'email': 'jane@ajshop.oi', 'name': 'Jane Smith', 'role': 'user'},
            {'username': 'bob_wilson', 'email': 'bob@ajshop.oi', 'name': 'Bob Wilson', 'role': 'user'},
        ]
        
        for user_data in sample_users:
            if not User.query.filter_by(username=user_data['username']).first():
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    full_name=user_data['name'],
                    role=user_data['role'],
                    is_active=True
                )
                user.set_password('password123')
                db.session.add(user)
        
        db.session.commit()
        print('✓ Sample users created')
        
        # Create sample products
        sample_products = [
            {'name': 'Premium Package', 'price': 99.99, 'stock': 50, 'category': 'Subscription'},
            {'name': 'Standard Package', 'price': 49.99, 'stock': 100, 'category': 'Subscription'},
            {'name': 'Starter Package', 'price': 9.99, 'stock': 200, 'category': 'Subscription'},
            {'name': 'VIP Membership', 'price': 199.99, 'stock': 20, 'category': 'Membership'},
        ]
        
        for prod_data in sample_products:
            if not Product.query.filter_by(name=prod_data['name']).first():
                product = Product(
                    name=prod_data['name'],
                    description=f'Description for {prod_data["name"]}',
                    price=prod_data['price'],
                    stock=prod_data['stock'],
                    category=prod_data['category'],
                    is_active=True
                )
                db.session.add(product)
        
        db.session.commit()
        print('✓ Sample products created')
        
        # Create sample members
        users = User.query.filter(User.username != 'Ajipang').all()
        for user in users:
            if not Member.query.filter_by(user_id=user.id).first():
                member = Member(
                    user_id=user.id,
                    membership_type='gold',
                    status='active',
                    join_date=datetime.utcnow(),
                    expiry_date=datetime.utcnow() + timedelta(days=365),
                    points=100
                )
                db.session.add(member)
        
        db.session.commit()
        print('✓ Sample members created')
        
        print('\n✅ Database initialization complete!')
        print('\n📝 Default Admin Credentials:')
        print('   Username: Ajipang')
        print('   Password: 775')
        print('\n🚀 Start the application with: python app.py')

if __name__ == '__main__':
    init_database()
