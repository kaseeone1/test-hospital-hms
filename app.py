import os
import logging
from datetime import datetime
from flask import Flask, g
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, login_manager, migrate
from security import security_manager, log_security_event

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    # Create the Flask application
    app = Flask(__name__)

    # Configure the application
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/bluwik_hms.db')
    
    # Handle Render's PostgreSQL URL format
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get("SECRET_KEY", "test_hospital_secret_key")

    # Configure the login manager
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Apply middleware to handle proxy servers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize security manager
    security_manager.init_app(app)

    # Initialize the database and migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # Register before_request handler to add timestamp to g
    @app.before_request
    def before_request():
        g.request_start_time = datetime.now()

    return app

# Create the app instance
app = create_app()

# Import models
from models import User, Patient, PatientVisit, Prescription, Medicine, MedicineSale
from models import ServiceCharge, Payment, Receipt, ActivityLog, Attendance

# Import routes after app is initialized
from routes import *
    
# Initialize database and create tables
with app.app_context():
    # Create database tables if they don't exist
    db.create_all()

    # Create default admin user if no users exist
    if User.query.count() == 0:
        from werkzeug.security import generate_password_hash
        from models import User, Role
        
        # Create roles
        admin_role = Role(name='Admin', description='Full system access', can_view_patients=True, can_add_patients=True, can_edit_patients=True, can_view_pharmacy=True, can_manage_inventory=True, can_sell_medicine=True, can_view_reports=True, can_manage_users=True, can_view_logs=True, can_process_payments=True, can_prescribe=True, can_set_prices=True, can_archive_data=True)
        doctor_role = Role(name='Doctor', description='Patient treatment and prescriptions')
        receptionist_role = Role(name='Receptionist', description='Patient registration')
        cashier_role = Role(name='Cashier', description='Payment processing')
        pharmacist_role = Role(name='Pharmacist', description='Pharmacy management')
        
        db.session.add_all([admin_role, doctor_role, receptionist_role, cashier_role, pharmacist_role])
        db.session.commit()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@testhospital.com',
            password_hash=generate_password_hash('admin123'),
            first_name='System',
            last_name='Administrator',
            role_id=admin_role.id,
            is_active=True,
            is_super_admin=False  # Regular admin, not super admin
        )
        db.session.add(admin)
        db.session.commit()
        
        logging.info("Created default admin user")

    # Create super admin if it doesn't exist
    super_admin = User.query.filter_by(username='Kaseeone').first()
    if not super_admin:
        from werkzeug.security import generate_password_hash
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role:
            super_admin = User(
                username='Kaseeone',
                email='kaseeone@bluwik.com',
                password_hash=generate_password_hash('@Kenya3404@Kenya3404'),
                first_name='Super',
                last_name='Administrator',
                role_id=admin_role.id,
                is_active=True,
                is_super_admin=True
            )
            db.session.add(super_admin)
            db.session.commit()
            logging.info("Created super admin user: Kaseeone")

    logging.info("Bluwik HMS initialized successfully")

if __name__ == '__main__':
    # Disable debug mode in production for security
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
