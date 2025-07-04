from app import app, db
from models import User, Role
from werkzeug.security import generate_password_hash
import os

def create_super_admin():
    with app.app_context():
        # Check if super admin already exists
        super_admin = User.query.filter_by(username='Kaseeone').first()
        if super_admin:
            print(f"Super admin already exists: {super_admin.username}")
            # Update password if needed
            super_admin.password_hash = generate_password_hash('@Kenya3404@Kenya3404')
            super_admin.is_super_admin = True
            db.session.commit()
            print("Super admin password updated!")
            return
        
        # Get admin role
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print("Admin role not found. Creating...")
            admin_role = Role(
                name='Admin', 
                description='Full system access',
                can_view_patients=True, can_add_patients=True, can_edit_patients=True,
                can_view_pharmacy=True, can_manage_inventory=True, can_sell_medicine=True,
                can_view_reports=True, can_manage_users=True, can_view_logs=True,
                can_process_payments=True, can_prescribe=True, can_set_prices=True,
                can_archive_data=True
            )
            db.session.add(admin_role)
            db.session.commit()
        
        # Create super admin user with your credentials
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
        
        print("Super admin created successfully!")
        print("Username: Kaseeone")
        print("Password: @Kenya3404@Kenya3404")
        print("Email: kaseeone@bluwik.com")

if __name__ == '__main__':
    create_super_admin() 