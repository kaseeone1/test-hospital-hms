from app import app, db
from models import Role

def update_admin_permissions():
    with app.app_context():
        # Find the admin role
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role:
            # Update all permissions to True
            admin_role.can_view_patients = True
            admin_role.can_add_patients = True
            admin_role.can_edit_patients = True
            admin_role.can_view_pharmacy = True
            admin_role.can_manage_inventory = True
            admin_role.can_sell_medicine = True
            admin_role.can_view_reports = True
            admin_role.can_manage_users = True
            admin_role.can_view_logs = True
            admin_role.can_process_payments = True
            admin_role.can_prescribe = True
            admin_role.can_set_prices = True
            admin_role.can_archive_data = True
            
            # Commit the changes
            db.session.commit()
            print("Admin role permissions updated successfully!")
        else:
            print("Admin role not found!")

if __name__ == '__main__':
    update_admin_permissions() 