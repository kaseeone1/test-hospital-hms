from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager
import enum

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Enum for medicine types
class MedicineType(enum.Enum):
    TABLET = "Tablet"
    CAPSULE = "Capsule"
    SYRUP = "Syrup"
    INJECTION = "Injection"
    CREAM = "Cream"
    OINTMENT = "Ointment"
    OTHER = "Other"

# Role model for user roles
class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Role permissions (bit flags)
    can_view_patients = db.Column(db.Boolean, default=False)
    can_add_patients = db.Column(db.Boolean, default=False)
    can_edit_patients = db.Column(db.Boolean, default=False)
    can_view_pharmacy = db.Column(db.Boolean, default=False)
    can_manage_inventory = db.Column(db.Boolean, default=False)
    can_sell_medicine = db.Column(db.Boolean, default=False)
    can_view_reports = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_view_logs = db.Column(db.Boolean, default=False)
    can_process_payments = db.Column(db.Boolean, default=False)
    can_prescribe = db.Column(db.Boolean, default=False)
    can_set_prices = db.Column(db.Boolean, default=False)
    can_archive_data = db.Column(db.Boolean, default=False)
    
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f"<Role {self.name}>"

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_super_admin = db.Column(db.Boolean, default=False)  # New field
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    patient_visits = db.relationship('PatientVisit', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)
    attendances = db.relationship('Attendance', backref='user', lazy=True)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.username}>"
    
    # Permission checking methods
    def can_view_patients(self):
        return self.role.can_view_patients
    
    def can_add_patients(self):
        return self.role.can_add_patients
    
    def can_edit_patients(self):
        return self.role.can_edit_patients
    
    def can_view_pharmacy(self):
        return self.role.can_view_pharmacy
    
    def can_manage_inventory(self):
        return self.role.can_manage_inventory
    
    def can_sell_medicine(self):
        return self.role.can_sell_medicine
    
    def can_view_reports(self):
        return self.role.can_view_reports
    
    def can_manage_users(self):
        return self.role.can_manage_users
    
    def can_view_logs(self):
        return self.role.can_view_logs
    
    def can_process_payments(self):
        return self.role.can_process_payments
    
    def can_prescribe(self):
        return self.role.can_prescribe
    
    def can_set_prices(self):
        return self.role.can_set_prices
    
    def can_archive_data(self):
        return self.role.can_archive_data
    
    def is_super_admin_user(self):
        return self.is_super_admin
    
    def has_permission(self, permission):
        """Check if user has permission, super admin has all permissions"""
        if self.is_super_admin:
            return True
        return getattr(self.role, permission, False)
    
    # Update all permission methods to use the new has_permission method
    def can_view_patients(self):
        return self.has_permission('can_view_patients')
    
    def can_add_patients(self):
        return self.has_permission('can_add_patients')
    
    def can_edit_patients(self):
        return self.has_permission('can_edit_patients')
    
    def can_view_pharmacy(self):
        return self.has_permission('can_view_pharmacy')
    
    def can_manage_inventory(self):
        return self.has_permission('can_manage_inventory')
    
    def can_sell_medicine(self):
        return self.has_permission('can_sell_medicine')
    
    def can_view_reports(self):
        return self.has_permission('can_view_reports')
    
    def can_manage_users(self):
        return self.has_permission('can_manage_users')
    
    def can_view_logs(self):
        return self.has_permission('can_view_logs')
    
    def can_process_payments(self):
        return self.has_permission('can_process_payments')
    
    def can_prescribe(self):
        return self.has_permission('can_prescribe')
    
    def can_set_prices(self):
        return self.has_permission('can_set_prices')
    
    def can_archive_data(self):
        return self.has_permission('can_archive_data')
    
    def is_admin(self):
        return self.role.name == 'Admin' or self.is_super_admin

# Patient model
class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    registered_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Next of Kin Information
    next_of_kin_name = db.Column(db.String(128))
    next_of_kin_relationship = db.Column(db.String(64))
    next_of_kin_phone = db.Column(db.String(20))
    next_of_kin_address = db.Column(db.String(200))
    
    # Relationships
    visits = db.relationship('PatientVisit', backref='patient', lazy=True, cascade="all, delete-orphan")
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True, cascade="all, delete-orphan")
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        if self.date_of_birth:
            today = datetime.now().date()
            age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            return age
        return None
    
    def __repr__(self):
        return f"<Patient {self.get_full_name()}>"

# Patient Visit model
class PatientVisit(db.Model):
    __tablename__ = 'patient_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_date = db.Column(db.DateTime, default=datetime.now)
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    service_charges = db.relationship('ServiceCharge', backref='visit', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Visit {self.id} - Patient {self.patient_id}>"

# Service Charge model
class ServiceCharge(db.Model):
    __tablename__ = 'service_charges'
    
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('patient_visits.id'), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    charge_amount = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_paid = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Service {self.service_name} - ${self.charge_amount}>"

# Prescription model
class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('patient_visits.id'))
    prescription_date = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.Text)
    is_filled = db.Column(db.Boolean, default=False)
    
    # Relationships
    items = db.relationship('PrescriptionItem', backref='prescription', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Prescription {self.id} - Patient {self.patient_id}>"

# Prescription Item model
class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    dosage = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    instructions = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False)
    
    # Relationships
    medicine = db.relationship('Medicine')
    
    def __repr__(self):
        return f"<PrescriptionItem {self.id} - Med {self.medicine_id}>"

# Medicine model
class Medicine(db.Model):
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    generic_name = db.Column(db.String(100))
    medicine_type = db.Column(db.Enum(MedicineType), default=MedicineType.TABLET)
    manufacturer = db.Column(db.String(100))
    description = db.Column(db.Text)
    purchase_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    min_selling_price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    sales = db.relationship('MedicineSale', backref='medicine', lazy=True)
    
    def __repr__(self):
        return f"<Medicine {self.name} - Stock: {self.stock_quantity}>"
    
    def is_low_stock(self, threshold=10):
        return self.stock_quantity <= threshold

# Medicine Sale model
class MedicineSale(db.Model):
    __tablename__ = 'medicine_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    prescription_item_id = db.Column(db.Integer, db.ForeignKey('prescription_items.id'))
    quantity = db.Column(db.Integer, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    sold_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    sale_date = db.Column(db.DateTime, default=datetime.now)
    is_cancelled = db.Column(db.Boolean, default=False)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'))
    
    def __repr__(self):
        return f"<Sale {self.id} - Med {self.medicine_id} - Qty: {self.quantity}>"

# Payment model
class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    payment_method = db.Column(db.String(50), default='Cash')
    received_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'))
    
    def __repr__(self):
        return f"<Payment {self.id} - Amount: ${self.amount}>"

# Receipt model
class Receipt(db.Model):
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    visit_id = db.Column(db.Integer, db.ForeignKey('patient_visits.id'))
    total_amount = db.Column(db.Float, nullable=False)
    is_pharmacy_receipt = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    payments = db.relationship('Payment', backref='receipt', lazy=True)
    medicine_sales = db.relationship('MedicineSale', backref='receipt', lazy=True)
    
    def __repr__(self):
        return f"<Receipt {self.id} - Amount: ${self.total_amount}>"

# Activity Log model
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Log {self.id} - User {self.user_id} - {self.activity_type}>"

# Attendance model
class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_in = db.Column(db.DateTime, default=datetime.now)
    check_out = db.Column(db.DateTime)
    
    def __repr__(self):
        return f"<Attendance {self.id} - User {self.user_id}>"
