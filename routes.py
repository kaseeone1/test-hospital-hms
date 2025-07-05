import os
import json
from datetime import datetime, date, timedelta
from functools import wraps
from io import BytesIO
import calendar

from flask import render_template, request, redirect, url_for, flash, jsonify, g, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, desc, or_
from werkzeug.security import check_password_hash, generate_password_hash

from app import app
from extensions import db
from models import User, Role, Patient, PatientVisit, Prescription, PrescriptionItem, Medicine
from models import MedicineSale, ServiceCharge, Receipt, Payment, ActivityLog, Attendance
from utils import log_activity, require_role, generate_report_pdf
from security import security_manager, log_security_event, sanitize_input

# Context processor to add common data to all templates
@app.context_processor
def inject_data():
    return {
        'app_name': 'Bluwik HMS',
        'hospital_name': 'Test Hospital',
        'year': datetime.now().year,
        'datetime': datetime,
        'timedelta': timedelta,
        'date': date
    }

# Helper function to check if user is currently checked in
def is_checked_in():
    if current_user.is_authenticated:
        attendance = Attendance.query.filter_by(
            user_id=current_user.id, 
            check_out=None
        ).first()
        return attendance is not None
    return False

# Add is_checked_in to all templates
@app.context_processor
def inject_attendance():
    return {'is_checked_in': is_checked_in}

# Root route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', '').strip())
        password = request.form.get('password', '')
        client_ip = request.remote_addr
        
        # Check if account is locked
        if security_manager.is_account_locked(username, client_ip):
            flash('Account is temporarily locked due to multiple failed attempts. Please try again later.', 'danger')
            log_security_event('ACCOUNT_LOCKED', f'Login attempt for locked account: {username}', None, client_ip)
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Account is disabled. Please contact administrator.', 'danger')
                log_security_event('LOGIN_DISABLED_ACCOUNT', f'Login attempt for disabled account: {username}', user.id, client_ip)
                return redirect(url_for('login'))
            
            # Clear failed attempts on successful login
            security_manager.clear_failed_attempts(username, client_ip)
            
            login_user(user)
            user.last_login = datetime.now()
            db.session.commit()
            
            log_activity('User Login', f'User {user.username} logged in')
            log_security_event('LOGIN_SUCCESS', f'Successful login: {username}', user.id, client_ip)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            # Record failed login attempt
            is_locked = security_manager.record_failed_login(username, client_ip)
            if is_locked:
                flash('Account has been locked due to multiple failed attempts. Please try again later.', 'danger')
        else:
            flash('Invalid username or password', 'danger')
            
            log_security_event('LOGIN_FAILED', f'Failed login attempt: {username}', None, client_ip)
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    # Auto check-out if user is checked in
    attendance = Attendance.query.filter_by(
        user_id=current_user.id, 
        check_out=None
    ).first()
    
    if attendance:
        attendance.check_out = datetime.now()
        db.session.commit()
        log_activity('Attendance', f'User {current_user.username} checked out')
    
    log_activity('User Logout', f'User {current_user.username} logged out')
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    # Get today's date
    today = date.today()
    
    # Statistics for dashboard
    total_patients = Patient.query.count()
    
    # Today's visits
    today_visits = PatientVisit.query.filter(
        func.date(PatientVisit.visit_date) == today
    ).count()
    
    # Low stock medicines
    low_stock = Medicine.query.filter(Medicine.stock_quantity <= 10).count()
    
    # Today's revenue
    today_revenue = db.session.query(func.sum(Receipt.total_amount)).filter(
        func.date(Receipt.created_at) == today
    ).scalar() or 0
    
    # Revenue this month
    first_day_of_month = date(today.year, today.month, 1)
    revenue_this_month = db.session.query(func.sum(Receipt.total_amount)).filter(
        func.date(Receipt.created_at) >= first_day_of_month,
        func.date(Receipt.created_at) <= today
    ).scalar() or 0
    
    # Recent patients (5)
    recent_patients = PatientVisit.query.join(Patient).filter(
        func.date(PatientVisit.visit_date) == today
    ).order_by(PatientVisit.visit_date.desc()).limit(5).all()
    
    # Recent activities (10)
    recent_activities = ActivityLog.query.order_by(
        ActivityLog.timestamp.desc()
    ).limit(10).all()
    
    # For doctors: their patients today
    doctor_patients = []
    if current_user.role.can_prescribe:
        # Get patients assigned to this doctor
        assigned_patients = Patient.query.filter(
            Patient.doctor_id == current_user.id,
            ~Patient.visits.any(PatientVisit.is_completed == True)  # No completed visits today
        ).all()
        
        # Create visits for assigned patients if they don't have one today
        for patient in assigned_patients:
            existing_visit = PatientVisit.query.filter(
                PatientVisit.patient_id == patient.id,
                func.date(PatientVisit.visit_date) == today,
                PatientVisit.doctor_id == current_user.id
            ).first()
            
            if not existing_visit:
                new_visit = PatientVisit(
                    patient_id=patient.id,
                    doctor_id=current_user.id,
                    visit_date=datetime.now()
                )
                db.session.add(new_visit)
                db.session.commit()
        
        # Get all patients for today (including newly created visits)
        doctor_patients = PatientVisit.query.join(Patient).filter(
            PatientVisit.doctor_id == current_user.id,
            func.date(PatientVisit.visit_date) == today
        ).order_by(PatientVisit.visit_date.asc()).all()
    
    # Get staff currently checked in
    staff_checked_in = User.query.join(
        Attendance, 
        User.id == Attendance.user_id
    ).filter(
        Attendance.check_out == None
    ).all()
    
    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        today_visits=today_visits,
        low_stock=low_stock,
        today_revenue=today_revenue,
        revenue_this_month=revenue_this_month,
        recent_patients=recent_patients,
        recent_activities=recent_activities,
        doctor_patients=doctor_patients,
        staff_checked_in=staff_checked_in
    )

# Attendance check-in/out
@app.route('/attendance/check-in', methods=['POST'])
@login_required
def check_in():
    # Check if already checked in
    active_attendance = Attendance.query.filter_by(
        user_id=current_user.id, 
        check_out=None
    ).first()
    
    if active_attendance:
        flash('You are already checked in', 'warning')
    else:
        # Create new attendance record
        attendance = Attendance(user_id=current_user.id)
        db.session.add(attendance)
        db.session.commit()
        
        log_activity('Attendance', f'User {current_user.username} checked in')
        flash('You have checked in successfully', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/attendance/check-out', methods=['POST'])
@login_required
def check_out():
    # Find active attendance record
    attendance = Attendance.query.filter_by(
        user_id=current_user.id, 
        check_out=None
    ).first()
    
    if attendance:
        attendance.check_out = datetime.now()
        db.session.commit()
        
        log_activity('Attendance', f'User {current_user.username} checked out')
        flash('You have checked out successfully', 'success')
    else:
        flash('No active check-in found', 'warning')
    
    return redirect(url_for('dashboard'))

# Patient Routes
@app.route('/patients')
@login_required
@require_role('can_view_patients')
def patients_list():
    # Get query parameters for filtering
    search = request.args.get('search', '')
    
    # Base query
    query = Patient.query
    
    # Apply search filter if provided
    if search:
        query = query.filter(
            or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.phone.ilike(f'%{search}%')
            )
        )
    
    # Order by and paginate results
    patients = query.order_by(Patient.created_at.desc()).all()
    
    return render_template('patients/index.html', patients=patients, search=search)

@app.route('/patients/register', methods=['GET', 'POST'])
@login_required
@require_role('can_add_patients')
def register_patient():
    if request.method == 'POST':
        # Extract form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        gender = request.form.get('gender')
        dob_str = request.form.get('date_of_birth')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        # Next of Kin Information
        next_of_kin_name = request.form.get('next_of_kin_name')
        next_of_kin_relationship = request.form.get('next_of_kin_relationship')
        next_of_kin_phone = request.form.get('next_of_kin_phone')
        next_of_kin_address = request.form.get('next_of_kin_address')
        
        # Doctor Assignment
        doctor_id = request.form.get('doctor_id')
        
        # Validate required fields
        if not first_name or not last_name or not gender:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('register_patient'))
        
        # Parse date of birth if provided
        date_of_birth = None
        if dob_str:
            try:
                date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for date of birth', 'danger')
                return redirect(url_for('register_patient'))
        
        # Create new patient
        new_patient = Patient(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            phone=phone,
            email=email,
            address=address,
            next_of_kin_name=next_of_kin_name,
            next_of_kin_relationship=next_of_kin_relationship,
            next_of_kin_phone=next_of_kin_phone,
            next_of_kin_address=next_of_kin_address,
            registered_by=current_user.id,
            doctor_id=doctor_id if doctor_id else None
        )
        
        db.session.add(new_patient)
        db.session.commit()
        
        # Create a visit if a doctor is assigned
        if doctor_id:
            new_visit = PatientVisit(
                patient_id=new_patient.id,
                doctor_id=doctor_id,
                visit_date=datetime.now()
            )
            db.session.add(new_visit)
            db.session.commit()
            
            log_activity('Patient Registration', f'Registered new patient: {new_patient.get_full_name()} and assigned to doctor')
        else:
            log_activity('Patient Registration', f'Registered new patient: {new_patient.get_full_name()}')
        
        flash(f'Patient {new_patient.get_full_name()} registered successfully', 'success')
        return redirect(url_for('patients_list'))
    
    # Fetch list of doctors for the dropdown
    doctors = User.query.filter_by(role_id=2).all()  # Assuming role_id 2 is for doctors
    return render_template('patients/register.html', doctors=doctors)

@app.route('/patients/<int:patient_id>')
@login_required
@require_role('can_view_patients')
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Get patient's visits
    visits = PatientVisit.query.filter_by(patient_id=patient_id).order_by(PatientVisit.visit_date.desc()).all()
    
    # Get patient's prescriptions
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.prescription_date.desc()).all()
    
    return render_template('patients/view.html', patient=patient, visits=visits, prescriptions=prescriptions)

@app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('can_edit_patients')
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Extract form data
        patient.first_name = request.form.get('first_name')
        patient.last_name = request.form.get('last_name')
        patient.gender = request.form.get('gender')
        dob_str = request.form.get('date_of_birth')
        patient.phone = request.form.get('phone')
        patient.email = request.form.get('email')
        patient.address = request.form.get('address')
        
        # Next of Kin Information
        patient.next_of_kin_name = request.form.get('next_of_kin_name')
        patient.next_of_kin_relationship = request.form.get('next_of_kin_relationship')
        patient.next_of_kin_phone = request.form.get('next_of_kin_phone')
        patient.next_of_kin_address = request.form.get('next_of_kin_address')
        
        # Validate required fields
        if not patient.first_name or not patient.last_name or not patient.gender:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('edit_patient', patient_id=patient_id))
        
        # Parse date of birth if provided
        if dob_str:
            try:
                patient.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for date of birth', 'danger')
                return redirect(url_for('edit_patient', patient_id=patient_id))
        
        db.session.commit()
        
        log_activity('Patient Update', f'Updated patient information: {patient.get_full_name()}')
        
        flash(f'Patient {patient.get_full_name()} updated successfully', 'success')
        return redirect(url_for('view_patient', patient_id=patient_id))
    
    return render_template('patients/register.html', patient=patient, edit_mode=True)

@app.route('/patients/<int:patient_id>/visit', methods=['GET', 'POST'])
@login_required
@require_role('can_prescribe')
def new_patient_visit(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Check for existing active visit
        existing_visit = PatientVisit.query.filter(
            PatientVisit.patient_id == patient_id,
            PatientVisit.doctor_id == current_user.id,
            PatientVisit.is_completed == False
        ).first()
        
        if existing_visit:
            # Update existing visit instead of creating a new one
            existing_visit.symptoms = request.form.get('symptoms')
            existing_visit.diagnosis = request.form.get('diagnosis')
            existing_visit.notes = request.form.get('notes')
            
            follow_up_str = request.form.get('follow_up_date')
            if follow_up_str:
                try:
                    existing_visit.follow_up_date = datetime.strptime(follow_up_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format for follow-up date', 'danger')
                    return redirect(url_for('new_patient_visit', patient_id=patient_id))
            
            db.session.commit()
            log_activity('Patient Visit', f'Updated visit for patient: {patient.get_full_name()}')
            flash(f'Visit for {patient.get_full_name()} updated successfully', 'success')
            return redirect(url_for('patient_treatment', visit_id=existing_visit.id))
        
        # If no existing visit, create new one
        symptoms = request.form.get('symptoms')
        diagnosis = request.form.get('diagnosis')
        notes = request.form.get('notes')
        follow_up_str = request.form.get('follow_up_date')
        
        # Parse follow-up date if provided
        follow_up_date = None
        if follow_up_str:
            try:
                follow_up_date = datetime.strptime(follow_up_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for follow-up date', 'danger')
                return redirect(url_for('new_patient_visit', patient_id=patient_id))
        
        # Create new visit
        new_visit = PatientVisit(
            patient_id=patient_id,
            doctor_id=current_user.id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            notes=notes,
            follow_up_date=follow_up_date
        )
        
        db.session.add(new_visit)
        db.session.commit()
        
        log_activity('Patient Visit', f'Created new visit for patient: {patient.get_full_name()}')
        
        flash(f'Visit for {patient.get_full_name()} recorded successfully', 'success')
        return redirect(url_for('patient_treatment', visit_id=new_visit.id))
    
    return render_template('patients/treatment.html', patient=patient, visit_mode=True)

@app.route('/visits/<int:visit_id>/treatment', methods=['GET', 'POST'])
@login_required
@require_role('can_prescribe')
def patient_treatment(visit_id):
    visit = PatientVisit.query.get_or_404(visit_id)
    patient = Patient.query.get_or_404(visit.patient_id)
    
    # Check if initial assessment is completed
    if not visit.symptoms or not visit.diagnosis:
        flash('Please complete the initial assessment first', 'warning')
        return redirect(url_for('new_patient_visit', patient_id=patient.id))
    
    # Get current services and prescriptions
    services = ServiceCharge.query.filter_by(visit_id=visit_id).all()
    prescriptions = Prescription.query.filter_by(visit_id=visit_id).all()
    
    # Get available medicines for prescription
    medicines = Medicine.query.filter(Medicine.stock_quantity > 0).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_service':
            # Add new service charge
            service_name = request.form.get('service_name')
            description = request.form.get('description')
            charge_amount = request.form.get('charge_amount')
            
            if not service_name or not charge_amount:
                flash('Service name and charge amount are required', 'danger')
                return redirect(url_for('patient_treatment', visit_id=visit_id))
            
            try:
                charge_amount = float(charge_amount)
            except ValueError:
                flash('Charge amount must be a valid number', 'danger')
                return redirect(url_for('patient_treatment', visit_id=visit_id))
            
            service = ServiceCharge(
                visit_id=visit_id,
                service_name=service_name,
                description=description,
                charge_amount=charge_amount,
                created_by=current_user.id
            )
            
            db.session.add(service)
            db.session.commit()
            
            log_activity('Service Charge', f'Added service charge: {service_name} for patient: {patient.get_full_name()}')
            
            flash(f'Service charge added successfully', 'success')
            
        elif action == 'add_prescription':
            # Add new prescription
            notes = request.form.get('prescription_notes')
            
            # Create prescription
            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=current_user.id,
                visit_id=visit_id,
                notes=notes
            )
            
            db.session.add(prescription)
            db.session.commit()
            
            # Process prescription items
            medicine_ids = request.form.getlist('medicine_id[]')
            dosages = request.form.getlist('dosage[]')
            durations = request.form.getlist('duration[]')
            instructions_list = request.form.getlist('instructions[]')
            quantities = request.form.getlist('quantity[]')
            
            for i in range(len(medicine_ids)):
                if medicine_ids[i]:
                    try:
                        medicine_id = int(medicine_ids[i])
                        quantity = int(quantities[i])
                        
                        # Verify medicine exists and has enough stock
                        medicine = Medicine.query.get(medicine_id)
                        if not medicine:
                            continue
                        
                        # Add prescription item
                        item = PrescriptionItem(
                            prescription_id=prescription.id,
                            medicine_id=medicine_id,
                            dosage=dosages[i] if i < len(dosages) else None,
                            duration=durations[i] if i < len(durations) else None,
                            instructions=instructions_list[i] if i < len(instructions_list) else None,
                            quantity=quantity
                        )
                        
                        db.session.add(item)
                    except (ValueError, IndexError):
                        continue
            
            db.session.commit()
            
            log_activity('Prescription', f'Created prescription for patient: {patient.get_full_name()}')
            
            flash('Prescription added successfully', 'success')
            
        elif action == 'complete_visit':
            # Mark visit as completed
            visit.is_completed = True
            db.session.commit()
            
            log_activity('Visit Completed', f'Completed visit for patient: {patient.get_full_name()}')
            
            flash('Visit marked as completed', 'success')
            return redirect(url_for('view_patient', patient_id=patient.id))
        
        return redirect(url_for('patient_treatment', visit_id=visit_id))
    
    return render_template(
        'patients/treatment.html',
        patient=patient,
        visit=visit,
        services=services,
        prescriptions=prescriptions,
        medicines=medicines
    )

# Pharmacy Routes
@app.route('/pharmacy')
@login_required
@require_role('can_view_pharmacy')
def pharmacy_dashboard():
    # Get low stock medicines
    low_stock = Medicine.query.filter(Medicine.stock_quantity <= 10).all()
    
    # Get expiring medicines (within 90 days)
    today = date.today()
    expiry_threshold = today + timedelta(days=90)
    expiring_soon = Medicine.query.filter(
        Medicine.expiry_date.isnot(None),
        Medicine.expiry_date <= expiry_threshold,
        Medicine.expiry_date >= today,
        Medicine.stock_quantity > 0
    ).all()
    
    # Recent sales
    recent_sales = MedicineSale.query.filter_by(is_cancelled=False).order_by(
        MedicineSale.sale_date.desc()
    ).limit(10).all()
    
    # Get unfilled prescriptions
    unfilled_prescriptions = Prescription.query.filter_by(is_filled=False).order_by(
        Prescription.prescription_date.desc()
    ).limit(10).all()
    
    return render_template(
        'pharmacy/index.html',
        low_stock=low_stock,
        expiring_soon=expiring_soon,
        recent_sales=recent_sales,
        unfilled_prescriptions=unfilled_prescriptions,
        today=today
    )

@app.route('/pharmacy/inventory')
@login_required
@require_role('can_view_pharmacy')
def pharmacy_inventory():
    # Get query parameters
    search = request.args.get('search', '')
    
    # Base query
    query = Medicine.query
    
    # Apply search filter if provided
    if search:
        query = query.filter(
            or_(
                Medicine.name.ilike(f'%{search}%'),
                Medicine.generic_name.ilike(f'%{search}%')
            )
        )
    
    # Get all medicines
    medicines = query.order_by(Medicine.name).all()
    
    return render_template('pharmacy/inventory.html', medicines=medicines, search=search)

@app.route('/pharmacy/inventory/add', methods=['GET', 'POST'])
@login_required
@require_role('can_manage_inventory')
def add_medicine():
    if request.method == 'POST':
        # Extract form data
        name = request.form.get('name')
        generic_name = request.form.get('generic_name')
        medicine_type = request.form.get('medicine_type')
        manufacturer = request.form.get('manufacturer')
        description = request.form.get('description')
        purchase_price = request.form.get('purchase_price')
        selling_price = request.form.get('selling_price')
        min_selling_price = request.form.get('min_selling_price')
        stock_quantity = request.form.get('stock_quantity')
        expiry_date_str = request.form.get('expiry_date')
        
        # Validate required fields
        if not name or not purchase_price or not selling_price or not min_selling_price or not stock_quantity:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('add_medicine'))
        
        # Parse numeric fields
        try:
            purchase_price = float(purchase_price)
            selling_price = float(selling_price)
            min_selling_price = float(min_selling_price)
            stock_quantity = int(stock_quantity)
        except ValueError:
            flash('Invalid numeric values provided', 'danger')
            return redirect(url_for('add_medicine'))
        
        # Validate selling price >= min_selling_price >= purchase_price
        if not (selling_price >= min_selling_price >= purchase_price):
            flash('Selling price must be >= minimum selling price >= purchase price', 'danger')
            return redirect(url_for('add_medicine'))
        
        # Parse expiry date if provided
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for expiry date', 'danger')
                return redirect(url_for('add_medicine'))
        
        # Create new medicine
        medicine = Medicine(
            name=name,
            generic_name=generic_name,
            medicine_type=medicine_type,
            manufacturer=manufacturer,
            description=description,
            purchase_price=purchase_price,
            selling_price=selling_price,
            min_selling_price=min_selling_price,
            stock_quantity=stock_quantity,
            expiry_date=expiry_date,
            created_by=current_user.id
        )
        
        db.session.add(medicine)
        db.session.commit()
        
        log_activity('Medicine Added', f'Added new medicine: {name} to inventory')
        
        flash(f'Medicine {name} added successfully', 'success')
        return redirect(url_for('pharmacy_inventory'))
    
    return render_template('pharmacy/inventory.html', add_mode=True)

@app.route('/pharmacy/inventory/<int:medicine_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('can_manage_inventory')
def edit_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    
    if request.method == 'POST':
        # Extract form data
        medicine.name = request.form.get('name')
        medicine.generic_name = request.form.get('generic_name')
        medicine.medicine_type = request.form.get('medicine_type')
        medicine.manufacturer = request.form.get('manufacturer')
        medicine.description = request.form.get('description')
        
        # Parse numeric fields
        try:
            medicine.purchase_price = float(request.form.get('purchase_price'))
            medicine.selling_price = float(request.form.get('selling_price'))
            medicine.min_selling_price = float(request.form.get('min_selling_price'))
            
            # Only admin can update stock directly
            if current_user.is_admin():
                medicine.stock_quantity = int(request.form.get('stock_quantity'))
        except ValueError:
            flash('Invalid numeric values provided', 'danger')
            return redirect(url_for('edit_medicine', medicine_id=medicine_id))
        
        # Validate selling price >= min_selling_price >= purchase_price
        if not (medicine.selling_price >= medicine.min_selling_price >= medicine.purchase_price):
            flash('Selling price must be >= minimum selling price >= purchase price', 'danger')
            return redirect(url_for('edit_medicine', medicine_id=medicine_id))
        
        # Parse expiry date if provided
        expiry_date_str = request.form.get('expiry_date')
        if expiry_date_str:
            try:
                medicine.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for expiry date', 'danger')
                return redirect(url_for('edit_medicine', medicine_id=medicine_id))
        
        db.session.commit()
        
        log_activity('Medicine Updated', f'Updated medicine: {medicine.name} in inventory')
        
        flash(f'Medicine {medicine.name} updated successfully', 'success')
        return redirect(url_for('pharmacy_inventory'))
    
    return render_template('pharmacy/inventory.html', medicine=medicine, edit_mode=True)

@app.route('/pharmacy/inventory/<int:medicine_id>/restock', methods=['POST'])
@login_required
@require_role('can_manage_inventory')
def restock_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    
    # Extract form data
    quantity = request.form.get('quantity')
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            flash('Quantity must be positive', 'danger')
            return redirect(url_for('pharmacy_inventory'))
    except ValueError:
        flash('Invalid quantity', 'danger')
        return redirect(url_for('pharmacy_inventory'))
    
    # Update stock
    original_stock = medicine.stock_quantity
    medicine.stock_quantity += quantity
    db.session.commit()
    
    log_activity(
        'Medicine Restocked', 
        f'Restocked {quantity} units of {medicine.name}. Previous: {original_stock}, New: {medicine.stock_quantity}'
    )
    
    flash(f'Successfully added {quantity} units of {medicine.name} to inventory', 'success')
    return redirect(url_for('pharmacy_inventory'))

@app.route('/pharmacy/sales')
@login_required
@require_role('can_sell_medicine')
def pharmacy_sales():
    # Get query parameters
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    
    # Parse dates if provided
    date_from = None
    date_to = None
    
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid from date format', 'danger')
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid to date format', 'danger')
    
    # Base query
    query = MedicineSale.query.filter_by(is_cancelled=False)
    
    # Apply date filters if provided
    if date_from:
        query = query.filter(func.date(MedicineSale.sale_date) >= date_from)
    
    if date_to:
        query = query.filter(func.date(MedicineSale.sale_date) <= date_to)
    
    # Get sales
    sales = query.order_by(MedicineSale.sale_date.desc()).all()
    
    # Calculate total sales amount
    total_sales = sum(sale.total_amount for sale in sales)
    
    return render_template(
        'pharmacy/sales.html',
        sales=sales,
        total_sales=total_sales,
        date_from=date_from_str,
        date_to=date_to_str
    )

@app.route('/pharmacy/prescriptions')
@login_required
@require_role('can_sell_medicine')
def unfilled_prescriptions():
    # Get unfilled prescriptions
    prescriptions = Prescription.query.filter_by(is_filled=False).order_by(
        Prescription.prescription_date.desc()
    ).all()
    
    return render_template('pharmacy/prescriptions.html', prescriptions=prescriptions)

@app.route('/pharmacy/prescriptions/<int:prescription_id>/fill', methods=['GET', 'POST'])
@login_required
@require_role('can_sell_medicine')
def fill_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    patient = Patient.query.get_or_404(prescription.patient_id)
    
    if prescription.is_filled:
        flash('This prescription has already been filled', 'warning')
        return redirect(url_for('unfilled_prescriptions'))
    
    if request.method == 'POST':
        # Extract form data
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        
        # Validate items
        if not item_ids:
            flash('No items selected', 'danger')
            return redirect(url_for('fill_prescription', prescription_id=prescription_id))
        
        # Create receipt
        receipt = Receipt(
            patient_id=patient.id,
            visit_id=prescription.visit_id,
            total_amount=0,
            is_pharmacy_receipt=True,
            created_by=current_user.id
        )
        
        db.session.add(receipt)
        db.session.commit()
        
        # Process each item
        total_amount = 0
        
        for i in range(len(item_ids)):
            try:
                item_id = int(item_ids[i])
                quantity = int(quantities[i])
                price = float(prices[i])
                
                # Get prescription item
                item = PrescriptionItem.query.get(item_id)
                if not item or item.prescription_id != prescription.id:
                    continue
                
                # Get medicine
                medicine = Medicine.query.get(item.medicine_id)
                if not medicine:
                    continue
                
                # Check if medicine price is valid (>= min_selling_price)
                if price < medicine.min_selling_price:
                    flash(f'Price for {medicine.name} cannot be below minimum selling price', 'danger')
                    db.session.delete(receipt)
                    db.session.commit()
                    return redirect(url_for('fill_prescription', prescription_id=prescription_id))
                
                # Check if enough stock
                if medicine.stock_quantity < quantity:
                    flash(f'Not enough stock for {medicine.name}', 'danger')
                    db.session.delete(receipt)
                    db.session.commit()
                    return redirect(url_for('fill_prescription', prescription_id=prescription_id))
                
                # Calculate total
                item_total = price * quantity
                total_amount += item_total
                
                # Create sale record
                sale = MedicineSale(
                    medicine_id=medicine.id,
                    prescription_item_id=item.id,
                    quantity=quantity,
                    selling_price=price,
                    total_amount=item_total,
                    sold_by=current_user.id,
                    receipt_id=receipt.id
                )
                
                db.session.add(sale)
                
                # Update medicine stock
                medicine.stock_quantity -= quantity
            except (ValueError, IndexError):
                continue
        
        # Update receipt total
        receipt.total_amount = total_amount
        
        # Mark prescription as filled
        prescription.is_filled = True
        
        db.session.commit()
        
        log_activity('Prescription Filled', f'Filled prescription for patient: {patient.get_full_name()}')
        
        flash('Prescription filled successfully', 'success')
        return redirect(url_for('cashier_receipt', receipt_id=receipt.id))
    
    return render_template('pharmacy/fill_prescription.html', prescription=prescription, patient=patient)

@app.route('/pharmacy/quick-sale', methods=['GET', 'POST'])
@login_required
@require_role('can_sell_medicine')
def quick_sale():
    # Get all medicines for selection
    medicines = Medicine.query.filter(Medicine.stock_quantity > 0).order_by(Medicine.name).all()
    
    if request.method == 'POST':
        # Extract form data
        medicine_ids = request.form.getlist('medicine_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        customer_name = request.form.get('customer_name', 'Walk-in Customer')
        
        # Validate items
        if not medicine_ids:
            flash('No items selected', 'danger')
            return redirect(url_for('quick_sale'))
        
        # Create receipt (without patient)
        receipt = Receipt(
            total_amount=0,
            is_pharmacy_receipt=True,
            created_by=current_user.id
        )
        
        db.session.add(receipt)
        db.session.commit()
        
        # Process each item
        total_amount = 0
        
        for i in range(len(medicine_ids)):
            try:
                medicine_id = int(medicine_ids[i])
                quantity = int(quantities[i])
                price = float(prices[i])
                
                # Get medicine
                medicine = Medicine.query.get(medicine_id)
                if not medicine:
                    continue
                
                # Check if medicine price is valid (>= min_selling_price)
                if price < medicine.min_selling_price:
                    flash(f'Price for {medicine.name} cannot be below minimum selling price', 'danger')
                    db.session.delete(receipt)
                    db.session.commit()
                    return redirect(url_for('quick_sale'))
                
                # Check if enough stock
                if medicine.stock_quantity < quantity:
                    flash(f'Not enough stock for {medicine.name}', 'danger')
                    db.session.delete(receipt)
                    db.session.commit()
                    return redirect(url_for('quick_sale'))
                
                # Calculate total
                item_total = price * quantity
                total_amount += item_total
                
                # Create sale record
                sale = MedicineSale(
                    medicine_id=medicine.id,
                    quantity=quantity,
                    selling_price=price,
                    total_amount=item_total,
                    sold_by=current_user.id,
                    receipt_id=receipt.id
                )
                
                db.session.add(sale)
                
                # Update medicine stock
                medicine.stock_quantity -= quantity
            except (ValueError, IndexError):
                continue
        
        # Update receipt total
        receipt.total_amount = total_amount
        
        db.session.commit()
        
        log_activity('Quick Sale', f'Processed quick sale for: {customer_name}')
        
        flash('Quick sale processed successfully', 'success')
        return redirect(url_for('cashier_receipt', receipt_id=receipt.id))
    
    return render_template('pharmacy/quick_sale.html', medicines=medicines)

# Cashier Routes
@app.route('/cashier')
@login_required
@require_role('can_process_payments')
def cashier_dashboard():
    # Get today's unpaid service charges
    today = date.today()
    unpaid_services = ServiceCharge.query.filter(
        func.date(ServiceCharge.created_at) == today,
        ServiceCharge.is_paid == False
    ).all()
    
    # Group by visit/patient
    visits_with_charges = {}
    
    for service in unpaid_services:
        visit = PatientVisit.query.get(service.visit_id)
        if visit:
            if visit.id not in visits_with_charges:
                patient = Patient.query.get(visit.patient_id)
                visits_with_charges[visit.id] = {
                    'visit': visit,
                    'patient': patient,
                    'services': [],
                    'total': 0
                }
            
            visits_with_charges[visit.id]['services'].append(service)
            visits_with_charges[visit.id]['total'] += service.charge_amount
    
    # Recent receipts
    recent_receipts = Receipt.query.order_by(Receipt.created_at.desc()).limit(10).all()
    
    return render_template(
        'cashier/index.html', 
        visits_with_charges=visits_with_charges,
        recent_receipts=recent_receipts
    )

@app.route('/cashier/visit/<int:visit_id>/payment', methods=['GET', 'POST'])
@login_required
@require_role('can_process_payments')
def process_service_payment(visit_id):
    visit = PatientVisit.query.get_or_404(visit_id)
    patient = Patient.query.get_or_404(visit.patient_id)
    
    # Get unpaid services
    unpaid_services = ServiceCharge.query.filter_by(
        visit_id=visit_id,
        is_paid=False
    ).all()
    
    if not unpaid_services:
        flash('No unpaid services found for this visit', 'warning')
        return redirect(url_for('cashier_dashboard'))
    
    if request.method == 'POST':
        # Extract form data
        payment_method = request.form.get('payment_method', 'Cash')
        
        # Calculate total
        total_amount = sum(service.charge_amount for service in unpaid_services)
        
        # Create receipt
        receipt = Receipt(
            patient_id=patient.id,
            visit_id=visit_id,
            total_amount=total_amount,
            is_pharmacy_receipt=False,
            created_by=current_user.id
        )
        
        db.session.add(receipt)
        db.session.commit()
        
        # Create payment
        payment = Payment(
            amount=total_amount,
            payment_method=payment_method,
            received_by=current_user.id,
            receipt_id=receipt.id
        )
        
        db.session.add(payment)
        
        # Mark services as paid
        for service in unpaid_services:
            service.is_paid = True
        
        db.session.commit()
        
        log_activity('Payment Processed', f'Processed service payment for patient: {patient.get_full_name()}')
        
        flash('Payment processed successfully', 'success')
        return redirect(url_for('cashier_receipt', receipt_id=receipt.id))
    
    # Calculate total
    total_amount = sum(service.charge_amount for service in unpaid_services)
    
    return render_template(
        'cashier/process_payment.html',
        visit=visit,
        patient=patient,
        services=unpaid_services,
        total_amount=total_amount
    )

@app.route('/cashier/receipts/<int:receipt_id>')
@login_required
def cashier_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    
    # Get patient info if available
    patient = None
    if receipt.patient_id:
        patient = Patient.query.get(receipt.patient_id)
    
    # Get payments
    payments = Payment.query.filter_by(receipt_id=receipt_id).all()
    
    # Get medicine sales if it's a pharmacy receipt
    medicine_sales = []
    if receipt.is_pharmacy_receipt:
        medicine_sales = MedicineSale.query.filter_by(
            receipt_id=receipt_id,
            is_cancelled=False
        ).all()
    
    # Get service charges if it's a service receipt
    service_charges = []
    if not receipt.is_pharmacy_receipt and receipt.visit_id:
        service_charges = ServiceCharge.query.filter_by(
            visit_id=receipt.visit_id,
            is_paid=True
        ).all()
    
    return render_template(
        'cashier/receipt.html',
        receipt=receipt,
        patient=patient,
        payments=payments,
        medicine_sales=medicine_sales,
        service_charges=service_charges
    )

@app.route('/cashier/receipts/<int:receipt_id>/print')
@login_required
def print_receipt(receipt_id):
    # This route just returns the receipt page with a print view flag
    # The actual printing is handled by JavaScript in the template
    receipt = Receipt.query.get_or_404(receipt_id)
    
    # Get patient info if available
    patient = None
    if receipt.patient_id:
        patient = Patient.query.get(receipt.patient_id)
    
    # Get payments
    payments = Payment.query.filter_by(receipt_id=receipt_id).all()
    
    # Get medicine sales if it's a pharmacy receipt
    medicine_sales = []
    if receipt.is_pharmacy_receipt:
        medicine_sales = MedicineSale.query.filter_by(
            receipt_id=receipt_id,
            is_cancelled=False
        ).all()
    
    # Get service charges if it's a service receipt
    service_charges = []
    if not receipt.is_pharmacy_receipt and receipt.visit_id:
        service_charges = ServiceCharge.query.filter_by(
            visit_id=receipt.visit_id,
            is_paid=True
        ).all()
    
    return render_template(
        'cashier/receipt.html',
        receipt=receipt,
        patient=patient,
        payments=payments,
        medicine_sales=medicine_sales,
        service_charges=service_charges,
        print_view=True
    )

# Reports Routes
@app.route('/reports')
@login_required
@require_role('can_view_reports')
def reports_dashboard():
    return render_template('reports/index.html')

@app.route('/reports/generate', methods=['POST'])
@login_required
@require_role('can_view_reports')
def generate_report():
    report_type = request.form.get('report_type')
    period = request.form.get('period', 'this_month')
    date_from_str = request.form.get('date_from')
    date_to_str = request.form.get('date_to')
    
    # Set date range based on period
    today = datetime.now().date()
    if period == 'today':
        date_from = today
        date_to = today
    elif period == 'yesterday':
        date_from = today - timedelta(days=1)
        date_to = date_from
    elif period == 'this_week':
        date_from = today - timedelta(days=today.weekday())
        date_to = today
    elif period == 'last_week':
        date_from = today - timedelta(days=today.weekday() + 7)
        date_to = date_from + timedelta(days=6)
    elif period == 'this_month':
        date_from = today.replace(day=1)
        date_to = today
    elif period == 'last_month':
        date_from = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        date_to = today.replace(day=1) - timedelta(days=1)
    elif period == 'this_year':
        date_from = today.replace(month=1, day=1)
        date_to = today
    elif period == 'custom':
        if date_from_str and date_to_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        else:
            flash('Please provide both start and end dates for custom range', 'danger')
            return redirect(url_for('reports_dashboard'))
    else:
        flash('Invalid date range', 'danger')
        return redirect(url_for('reports_dashboard'))
    
    # Generate report data based on type
    if report_type == 'sales':
        # Generate sales report
        report_title = f"Sales Report ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"
        
        # Get pharmacy sales
        pharmacy_sales = db.session.query(
            func.date(MedicineSale.sale_date).label('sale_date'),
            func.sum(MedicineSale.total_amount).label('total')
        ).filter(
            func.date(MedicineSale.sale_date) >= date_from,
            func.date(MedicineSale.sale_date) <= date_to,
            MedicineSale.is_cancelled == False
        ).group_by(func.date(MedicineSale.sale_date)).all()
        
        # Get service revenue
        service_revenue = db.session.query(
            func.date(Receipt.created_at).label('receipt_date'),
            func.sum(Receipt.total_amount).label('total')
        ).filter(
            func.date(Receipt.created_at) >= date_from,
            func.date(Receipt.created_at) <= date_to,
            Receipt.is_pharmacy_receipt == False
        ).group_by(func.date(Receipt.created_at)).all()
        
        # Combine data for charts
        dates = set()
        for sale in pharmacy_sales:
            dates.add(sale.sale_date)
        for receipt in service_revenue:
            dates.add(receipt.receipt_date)
        
        dates = sorted(list(dates))
        
        pharmacy_data = {sale.sale_date: sale.total for sale in pharmacy_sales}
        service_data = {receipt.receipt_date: receipt.total for receipt in service_revenue}
        
        chart_data = {
            'labels': [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d) for d in dates],
            'pharmacy': [pharmacy_data.get(d, 0) for d in dates],
            'services': [service_data.get(d, 0) for d in dates]
        }
        
        # Calculate totals
        total_pharmacy = sum(pharmacy_data.values())
        total_services = sum(service_data.values())
        total_revenue = total_pharmacy + total_services
        
        # Generate PDF report
        pdf_data = {
            'title': report_title,
            'period': period.capitalize(),
            'date_from': date_from,
            'date_to': date_to,
            'pharmacy_sales': pharmacy_sales,
            'service_revenue': service_revenue,
            'total_pharmacy': total_pharmacy,
            'total_services': total_services,
            'total_revenue': total_revenue
        }
        
        pdf_bytes = generate_report_pdf('sales', pdf_data)
        if pdf_bytes:
            # Save PDF to temporary file
            import tempfile
            import os
            temp_dir = os.path.join(app.root_path, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, suffix='.pdf', delete=False)
            temp_file.write(pdf_bytes.getvalue())
            temp_file.close()
            pdf_filename = os.path.basename(temp_file.name)
        else:
            pdf_filename = None
        
        return render_template(
            'reports/view_report.html',
            report_title=report_title,
            chart_data=json.dumps(chart_data),
            pdf_filename=pdf_filename,
            report_type='sales',
            date_from=date_from_str,
            date_to=date_to_str,
            pharmacy_sales=pharmacy_sales,
            service_revenue=service_revenue,
            total_pharmacy=total_pharmacy,
            total_services=total_services,
            total_revenue=total_revenue,
            now=datetime.now
        )
    
    elif report_type == 'patients':
        # Generate patient statistics report
        report_title = f"Patient Statistics Report ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"
        
        # Get new patient registrations
        new_patients = db.session.query(
            func.date(Patient.created_at).label('reg_date'),
            func.count(Patient.id).label('count')
        ).filter(
            func.date(Patient.created_at) >= date_from,
            func.date(Patient.created_at) <= date_to
        ).group_by(func.date(Patient.created_at)).all()
        
        # Get patient visits
        patient_visits = db.session.query(
            func.date(PatientVisit.visit_date).label('visit_date'),
            func.count(PatientVisit.id).label('count')
        ).filter(
            func.date(PatientVisit.visit_date) >= date_from,
            func.date(PatientVisit.visit_date) <= date_to
        ).group_by(func.date(PatientVisit.visit_date)).all()
        
        # Combine data for charts
        dates = set()
        for reg in new_patients:
            dates.add(reg.reg_date)
        for visit in patient_visits:
            dates.add(visit.visit_date)
        
        dates = sorted(list(dates))
        
        reg_data = {reg.reg_date: reg.count for reg in new_patients}
        visit_data = {visit.visit_date: visit.count for visit in patient_visits}
        
        chart_data = {
            'labels': [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d) for d in dates],
            'new_patients': [reg_data.get(d, 0) for d in dates],
            'visits': [visit_data.get(d, 0) for d in dates]
        }
        
        # Calculate totals
        total_new_patients = sum(reg_data.values())
        total_visits = sum(visit_data.values())
        
        # Generate PDF report
        pdf_data = {
            'title': report_title,
            'period': period.capitalize(),
            'date_from': date_from,
            'date_to': date_to,
            'new_patients': new_patients,
            'patient_visits': patient_visits,
            'total_new_patients': total_new_patients,
            'total_visits': total_visits
        }
        
        pdf_bytes = generate_report_pdf('patients', pdf_data)
        if pdf_bytes:
            # Save PDF to temporary file
            import tempfile
            import os
            temp_dir = os.path.join(app.root_path, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, suffix='.pdf', delete=False)
            temp_file.write(pdf_bytes.getvalue())
            temp_file.close()
            pdf_filename = os.path.basename(temp_file.name)
        else:
            pdf_filename = None
        
        return render_template(
            'reports/view_report.html',
            report_title=report_title,
            chart_data=json.dumps(chart_data),
            pdf_filename=pdf_filename,
            report_type='patients',
            date_from=date_from_str,
            date_to=date_to_str,
            new_patients=new_patients,
            patient_visits=patient_visits,
            total_new_patients=total_new_patients,
            total_visits=total_visits,
            now=datetime.now
        )
    
    elif report_type == 'inventory':
        # Generate inventory report
        report_title = f"Inventory Report ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"
        
        # Get medicine sales
        medicine_sales = db.session.query(
            Medicine.id,
            Medicine.name,
            func.sum(MedicineSale.quantity).label('sold_quantity'),
            func.sum(MedicineSale.total_amount).label('revenue'),
            func.sum(MedicineSale.quantity * Medicine.purchase_price).label('cost')
        ).join(
            MedicineSale, Medicine.id == MedicineSale.medicine_id
        ).filter(
            func.date(MedicineSale.sale_date) >= date_from,
            func.date(MedicineSale.sale_date) <= date_to,
            MedicineSale.is_cancelled == False
        ).group_by(Medicine.id, Medicine.name).all()
        
        # Calculate profit for each medicine
        medicine_profit = []
        for sale in medicine_sales:
            profit = sale.revenue - sale.cost
            profit_margin = (profit / sale.revenue) * 100 if sale.revenue > 0 else 0
            
            medicine_profit.append({
                'id': sale.id,
                'name': sale.name,
                'sold_quantity': sale.sold_quantity,
                'revenue': sale.revenue,
                'cost': sale.cost,
                'profit': profit,
                'profit_margin': profit_margin
            })
        
        # Sort by profit descending
        medicine_profit.sort(key=lambda x: x['profit'], reverse=True)
        
        # Calculate totals
        total_sold = sum(sale.sold_quantity for sale in medicine_sales)
        total_revenue = sum(sale.revenue for sale in medicine_sales)
        total_cost = sum(sale.cost for sale in medicine_sales)
        total_profit = total_revenue - total_cost
        
        # Top selling medicines for chart
        top_medicines = medicine_profit[:10]
        
        chart_data = {
            'labels': [m['name'] for m in top_medicines],
            'quantities': [m['sold_quantity'] for m in top_medicines],
            'revenues': [m['revenue'] for m in top_medicines],
            'profits': [m['profit'] for m in top_medicines]
        }
        
        # Add current stock information
        current_stock = Medicine.query.all()
        
        # Calculate total stock value
        total_stock_value = sum(medicine.stock_quantity * medicine.purchase_price for medicine in current_stock)
        
        # Generate PDF report
        pdf_data = {
            'title': report_title,
            'period': period.capitalize(),
            'date_from': date_from,
            'date_to': date_to,
            'medicine_profit': medicine_profit,
            'total_sold': total_sold,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_profit': total_profit,
            'current_stock': current_stock
        }
        
        pdf_bytes = generate_report_pdf('inventory', pdf_data)
        if pdf_bytes:
            # Save PDF to temporary file
            import tempfile
            import os
            temp_dir = os.path.join(app.root_path, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, suffix='.pdf', delete=False)
            temp_file.write(pdf_bytes.getvalue())
            temp_file.close()
            pdf_filename = os.path.basename(temp_file.name)
        else:
            pdf_filename = None
        
        return render_template(
            'reports/view_report.html',
            report_title=report_title,
            chart_data=json.dumps(chart_data),
            pdf_filename=pdf_filename,
            report_type='inventory',
            date_from=date_from_str,
            date_to=date_to_str,
            medicine_profit=medicine_profit,
            total_sold=total_sold,
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_profit=total_profit,
            current_stock=current_stock,
            total_stock_value=total_stock_value,
            now=datetime.now
        )
    
    elif report_type == 'staff':
        # Generate staff performance report
        report_title = f"Staff Performance Report ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"
        
        # Get staff attendance data
        staff_attendance = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            User.role_id,
            func.count(Attendance.id).label('check_ins'),
            func.avg(func.extract('epoch', Attendance.check_out - Attendance.check_in)/3600).label('avg_hours')
        ).join(
            Attendance, User.id == Attendance.user_id
        ).filter(
            func.date(Attendance.check_in) >= date_from,
            func.date(Attendance.check_in) <= date_to
        ).group_by(User.id, User.first_name, User.last_name, User.role_id).all()
        
        # Get staff activity data
        staff_activities = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            func.count(ActivityLog.id).label('activities')
        ).join(
            ActivityLog, User.id == ActivityLog.user_id
        ).filter(
            func.date(ActivityLog.timestamp) >= date_from,
            func.date(ActivityLog.timestamp) <= date_to
        ).group_by(User.id, User.first_name, User.last_name).all()
        
        # Combine data
        staff_performance = []
        for staff in staff_attendance:
            activities = next((a.activities for a in staff_activities if a.id == staff.id), 0)
            staff_performance.append({
                'id': staff.id,
                'name': f"{staff.first_name} {staff.last_name}",
                'role': Role.query.get(staff.role_id).name if staff.role_id else 'Unknown',
                'check_ins': staff.check_ins,
                'avg_hours': round(staff.avg_hours, 2) if staff.avg_hours else 0,
                'activities': activities
            })
        
        # Sort by activities descending
        staff_performance.sort(key=lambda x: x['activities'], reverse=True)
        
        chart_data = {
            'labels': [s['name'] for s in staff_performance[:10]],
            'activities': [s['activities'] for s in staff_performance[:10]],
            'check_ins': [s['check_ins'] for s in staff_performance[:10]],
            'avg_hours': [s['avg_hours'] for s in staff_performance[:10]]
        }
        
        return render_template(
            'reports/view_report.html',
            report_title=report_title,
            chart_data=json.dumps(chart_data),
            pdf_filename=None,
            report_type='staff',
            date_from=date_from_str,
            date_to=date_to_str,
            staff_performance=staff_performance,
            now=datetime.now
        )
    
    elif report_type == 'medicine':
        # Generate medicine analysis report
        report_title = f"Medicine Analysis Report ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"
        
        # Get medicine sales analysis
        medicine_analysis = db.session.query(
            Medicine.id,
            Medicine.name,
            Medicine.medicine_type,
            func.sum(MedicineSale.quantity).label('total_sold'),
            func.sum(MedicineSale.total_amount).label('total_revenue'),
            func.avg(MedicineSale.selling_price).label('avg_price')
        ).join(
            MedicineSale, Medicine.id == MedicineSale.medicine_id
        ).filter(
            func.date(MedicineSale.sale_date) >= date_from,
            func.date(MedicineSale.sale_date) <= date_to,
            MedicineSale.is_cancelled == False
        ).group_by(Medicine.id, Medicine.name, Medicine.medicine_type).all()
        
        # Get prescription patterns
        prescription_patterns = db.session.query(
            Medicine.name,
            func.count(PrescriptionItem.id).label('prescription_count')
        ).join(
            PrescriptionItem, Medicine.id == PrescriptionItem.medicine_id
        ).join(
            Prescription, PrescriptionItem.prescription_id == Prescription.id
        ).filter(
            func.date(Prescription.prescription_date) >= date_from,
            func.date(Prescription.prescription_date) <= date_to
        ).group_by(Medicine.name).all()
        
        # Combine data
        medicine_data = []
        for med in medicine_analysis:
            prescription_count = next((p.prescription_count for p in prescription_patterns if p.name == med.name), 0)
            medicine_data.append({
                'id': med.id,
                'name': med.name,
                'type': med.medicine_type.value if med.medicine_type else 'Unknown',
                'total_sold': med.total_sold,
                'total_revenue': med.total_revenue,
                'avg_price': round(med.avg_price, 2) if med.avg_price else 0,
                'prescription_count': prescription_count
            })
        
        # Sort by total sold descending
        medicine_data.sort(key=lambda x: x['total_sold'], reverse=True)
        
        chart_data = {
            'labels': [m['name'] for m in medicine_data[:10]],
            'quantities': [m['total_sold'] for m in medicine_data[:10]],
            'revenues': [m['total_revenue'] for m in medicine_data[:10]],
            'prescriptions': [m['prescription_count'] for m in medicine_data[:10]]
        }
        
        return render_template(
            'reports/view_report.html',
            report_title=report_title,
            chart_data=json.dumps(chart_data),
            pdf_filename=None,
            report_type='medicine',
            date_from=date_from_str,
            date_to=date_to_str,
            medicine_data=medicine_data,
            now=datetime.now
        )
    
    elif report_type == 'financial':
        # Generate comprehensive financial report
        report_title = f"Financial Summary Report ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"
        
        # Get all revenue sources
        pharmacy_revenue = db.session.query(func.sum(MedicineSale.total_amount)).filter(
            func.date(MedicineSale.sale_date) >= date_from,
            func.date(MedicineSale.sale_date) <= date_to,
            MedicineSale.is_cancelled == False
        ).scalar() or 0
        
        service_revenue = db.session.query(func.sum(Receipt.total_amount)).filter(
            func.date(Receipt.created_at) >= date_from,
            func.date(Receipt.created_at) <= date_to,
            Receipt.is_pharmacy_receipt == False
        ).scalar() or 0
        
        # Get costs
        pharmacy_costs = db.session.query(
            func.sum(MedicineSale.quantity * Medicine.purchase_price)
        ).join(
            Medicine, MedicineSale.medicine_id == Medicine.id
        ).filter(
            func.date(MedicineSale.sale_date) >= date_from,
            func.date(MedicineSale.sale_date) <= date_to,
            MedicineSale.is_cancelled == False
        ).scalar() or 0
        
        total_revenue = pharmacy_revenue + service_revenue
        total_costs = pharmacy_costs
        gross_profit = total_revenue - total_costs
        profit_margin = (gross_profit / total_revenue) * 100 if total_revenue > 0 else 0
        
        # Daily breakdown
        daily_revenue = db.session.query(
            func.date(Receipt.created_at).label('date'),
            func.sum(Receipt.total_amount).label('amount')
        ).filter(
            func.date(Receipt.created_at) >= date_from,
            func.date(Receipt.created_at) <= date_to
        ).group_by(func.date(Receipt.created_at)).all()
        
        chart_data = {
            'labels': [d.date.strftime('%Y-%m-%d') if hasattr(d.date, 'strftime') else str(d.date) for d in daily_revenue],
            'revenue': [d.amount for d in daily_revenue],
            'pharmacy_revenue': pharmacy_revenue,
            'service_revenue': service_revenue,
            'total_costs': total_costs,
            'gross_profit': gross_profit
        }
        
        return render_template(
            'reports/view_report.html',
            report_title=report_title,
            chart_data=json.dumps(chart_data),
            pdf_filename=None,
            report_type='financial',
            date_from=date_from_str,
            date_to=date_to_str,
            pharmacy_revenue=pharmacy_revenue,
            service_revenue=service_revenue,
            total_revenue=total_revenue,
            total_costs=total_costs,
            gross_profit=gross_profit,
            profit_margin=profit_margin,
            daily_revenue=daily_revenue,
            now=datetime.now
        )
    
    elif report_type == 'trends':
        # Generate trend analysis report
        report_title = f"Trend Analysis Report ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"
        
        # Get monthly trends for the last 12 months
        end_date = date_to
        start_date = end_date - timedelta(days=365)
        
        # Monthly revenue trends
        monthly_revenue = db.session.query(
            func.date_trunc('month', Receipt.created_at).label('month'),
            func.sum(Receipt.total_amount).label('amount')
        ).filter(
            func.date(Receipt.created_at) >= start_date,
            func.date(Receipt.created_at) <= end_date
        ).group_by(func.date_trunc('month', Receipt.created_at)).all()
        
        # Monthly patient trends
        monthly_patients = db.session.query(
            func.date_trunc('month', Patient.created_at).label('month'),
            func.count(Patient.id).label('count')
        ).filter(
            func.date(Patient.created_at) >= start_date,
            func.date(Patient.created_at) <= end_date
        ).group_by(func.date_trunc('month', Patient.created_at)).all()
        
        chart_data = {
            'labels': [m.month.strftime('%Y-%m') if hasattr(m.month, 'strftime') else str(m.month) for m in monthly_revenue],
            'revenue': [m.amount for m in monthly_revenue],
            'patients': [p.count for p in monthly_patients]
        }
        
        return render_template(
            'reports/view_report.html',
            report_title=report_title,
            chart_data=json.dumps(chart_data),
            pdf_filename=None,
            report_type='trends',
            date_from=date_from_str,
            date_to=date_to_str,
            monthly_revenue=monthly_revenue,
            monthly_patients=monthly_patients,
            now=datetime.now
        )
    
    elif report_type == 'comparative':
        # Generate comparative report
        report_title = f"Comparative Analysis Report ({date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')})"
        
        # Calculate period length
        period_length = (date_to - date_from).days + 1
        
        # Get previous period data for comparison
        prev_date_from = date_from - timedelta(days=period_length)
        prev_date_to = date_from - timedelta(days=1)
        
        # Current period data
        current_revenue = db.session.query(func.sum(Receipt.total_amount)).filter(
            func.date(Receipt.created_at) >= date_from,
            func.date(Receipt.created_at) <= date_to
        ).scalar() or 0
        
        current_patients = db.session.query(func.count(Patient.id)).filter(
            func.date(Patient.created_at) >= date_from,
            func.date(Patient.created_at) <= date_to
        ).scalar() or 0
        
        # Previous period data
        prev_revenue = db.session.query(func.sum(Receipt.total_amount)).filter(
            func.date(Receipt.created_at) >= prev_date_from,
            func.date(Receipt.created_at) <= prev_date_to
        ).scalar() or 0
        
        prev_patients = db.session.query(func.count(Patient.id)).filter(
            func.date(Patient.created_at) >= prev_date_from,
            func.date(Patient.created_at) <= prev_date_to
        ).scalar() or 0
        
        # Calculate changes
        revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        patient_change = ((current_patients - prev_patients) / prev_patients * 100) if prev_patients > 0 else 0
        
        chart_data = {
            'labels': ['Current Period', 'Previous Period'],
            'revenue': [current_revenue, prev_revenue],
            'patients': [current_patients, prev_patients]
        }
        
        return render_template(
            'reports/view_report.html',
            report_title=report_title,
            chart_data=json.dumps(chart_data),
            pdf_filename=None,
            report_type='comparative',
            date_from=date_from_str,
            date_to=date_to_str,
            current_revenue=current_revenue,
            current_patients=current_patients,
            prev_revenue=prev_revenue,
            prev_patients=prev_patients,
            revenue_change=revenue_change,
            patient_change=patient_change,
            now=datetime.now
        )
    
    flash('Invalid report type', 'danger')
    return redirect(url_for('reports_dashboard'))

@app.route('/reports/download/<report_type>/<path:filename>')
@login_required
@require_role('can_view_reports')
def download_report(report_type, filename):
    # Return the PDF file for download
    return send_file(
        filename,
        download_name=f"{report_type}_report.pdf",
        as_attachment=True,
        mimetype='application/pdf'
    )

# Admin Routes
@app.route('/admin/users')
@login_required
@require_role('can_manage_users')
def admin_users():
    users = User.query.all()
    roles = Role.query.all()
    
    return render_template('admin/users.html', users=users, roles=roles)

@app.route('/admin/users/add', methods=['POST'])
@login_required
@require_role('can_manage_users')
def add_user():
    # Extract and sanitize form data
    username = sanitize_input(request.form.get('username', '').strip())
    email = sanitize_input(request.form.get('email', '').strip())
    password = request.form.get('password', '')
    first_name = sanitize_input(request.form.get('first_name', '').strip())
    last_name = sanitize_input(request.form.get('last_name', '').strip())
    role_id = request.form.get('role_id')
    
    # Validate required fields
    if not username or not email or not password or not first_name or not last_name or not role_id:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_users'))
    
    # Validate password strength
    is_valid, message = security_manager.validate_password(password)
    if not is_valid:
        flash(f'Password validation failed: {message}', 'danger')
        return redirect(url_for('admin_users'))
    
    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        flash('Username or email already in use', 'danger')
        return redirect(url_for('admin_users'))
    
    # Create new user
    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        role_id=role_id,
        is_active=True
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    log_activity('User Created', f'Created new user: {username}')
    log_security_event('USER_CREATED', f'New user created: {username}', current_user.id, request.remote_addr)
    
    flash(f'User {username} created successfully', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@require_role('can_manage_users')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Extract and sanitize form data
    user.email = sanitize_input(request.form.get('email', '').strip())
    user.first_name = sanitize_input(request.form.get('first_name', '').strip())
    user.last_name = sanitize_input(request.form.get('last_name', '').strip())
    new_role_id = request.form.get('role_id')
    
    # Check if role is being changed
    if new_role_id and int(new_role_id) != user.role_id:
        user.role_id = int(new_role_id)
        # If the edited user is the current user, refresh their session
        if user.id == current_user.id:
            logout_user()
            login_user(user)
    
    # Update password if provided
    password = request.form.get('password')
    if password:
        # Validate password strength
        is_valid, message = security_manager.validate_password(password)
        if not is_valid:
            flash(f'Password validation failed: {message}', 'danger')
            return redirect(url_for('admin_users'))
        
        user.password_hash = generate_password_hash(password)
        log_security_event('PASSWORD_CHANGED', f'Password changed for user: {user.username}', current_user.id, request.remote_addr)
    
    # Update active status
    is_active = request.form.get('is_active') == 'on'
    user.is_active = is_active
    
    db.session.commit()
    
    log_activity('User Updated', f'Updated user: {user.username}')
    log_security_event('USER_UPDATED', f'User updated: {user.username}', current_user.id, request.remote_addr)
    
    flash(f'User {user.username} updated successfully', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/roles')
@login_required
@require_role('can_manage_users')
def admin_roles():
    roles = Role.query.all()
    
    return render_template('admin/roles.html', roles=roles)

@app.route('/admin/roles/add', methods=['POST'])
@login_required
@require_role('can_manage_users')
def add_role():
    # Extract form data
    name = request.form.get('name')
    description = request.form.get('description')
    
    # Permission flags
    can_view_patients = request.form.get('can_view_patients') == 'on'
    can_add_patients = request.form.get('can_add_patients') == 'on'
    can_edit_patients = request.form.get('can_edit_patients') == 'on'
    can_view_pharmacy = request.form.get('can_view_pharmacy') == 'on'
    can_manage_inventory = request.form.get('can_manage_inventory') == 'on'
    can_sell_medicine = request.form.get('can_sell_medicine') == 'on'
    can_view_reports = request.form.get('can_view_reports') == 'on'
    can_manage_users = request.form.get('can_manage_users') == 'on'
    can_view_logs = request.form.get('can_view_logs') == 'on'
    can_process_payments = request.form.get('can_process_payments') == 'on'
    can_prescribe = request.form.get('can_prescribe') == 'on'
    can_set_prices = request.form.get('can_set_prices') == 'on'
    can_archive_data = request.form.get('can_archive_data') == 'on'
    
    # Validate required fields
    if not name:
        flash('Role name is required', 'danger')
        return redirect(url_for('admin_roles'))
    
    # Check if role already exists
    existing_role = Role.query.filter_by(name=name).first()
    if existing_role:
        flash('Role with this name already exists', 'danger')
        return redirect(url_for('admin_roles'))
    
    # Create new role
    new_role = Role(
        name=name,
        description=description,
        can_view_patients=can_view_patients,
        can_add_patients=can_add_patients,
        can_edit_patients=can_edit_patients,
        can_view_pharmacy=can_view_pharmacy,
        can_manage_inventory=can_manage_inventory,
        can_sell_medicine=can_sell_medicine,
        can_view_reports=can_view_reports,
        can_manage_users=can_manage_users,
        can_view_logs=can_view_logs,
        can_process_payments=can_process_payments,
        can_prescribe=can_prescribe,
        can_set_prices=can_set_prices,
        can_archive_data=can_archive_data
    )
    
    db.session.add(new_role)
    db.session.commit()
    
    log_activity('Role Created', f'Created new role: {name}')
    
    flash(f'Role {name} created successfully', 'success')
    return redirect(url_for('admin_roles'))

@app.route('/admin/roles/<int:role_id>/edit', methods=['POST'])
@login_required
@require_role('can_manage_users')
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    
    # Extract form data
    role.description = request.form.get('description')
    
    # Permission flags
    role.can_view_patients = request.form.get('can_view_patients') == 'on'
    role.can_add_patients = request.form.get('can_add_patients') == 'on'
    role.can_edit_patients = request.form.get('can_edit_patients') == 'on'
    role.can_view_pharmacy = request.form.get('can_view_pharmacy') == 'on'
    role.can_manage_inventory = request.form.get('can_manage_inventory') == 'on'
    role.can_sell_medicine = request.form.get('can_sell_medicine') == 'on'
    role.can_view_reports = request.form.get('can_view_reports') == 'on'
    role.can_manage_users = request.form.get('can_manage_users') == 'on'
    role.can_view_logs = request.form.get('can_view_logs') == 'on'
    role.can_process_payments = request.form.get('can_process_payments') == 'on'
    role.can_prescribe = request.form.get('can_prescribe') == 'on'
    role.can_set_prices = request.form.get('can_set_prices') == 'on'
    role.can_archive_data = request.form.get('can_archive_data') == 'on'
    
    db.session.commit()
    
    log_activity('Role Updated', f'Updated role: {role.name}')
    
    flash(f'Role {role.name} updated successfully', 'success')
    return redirect(url_for('admin_roles'))

@app.route('/admin/logs')
@login_required
@require_role('can_view_logs')
def admin_logs():
    # Get query parameters
    user_id = request.args.get('user_id')
    activity_type = request.args.get('activity_type')
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    
    # Parse dates if provided
    date_from = None
    date_to = None
    
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid from date format', 'danger')
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid to date format', 'danger')
    
    # Base query
    query = ActivityLog.query
    
    # Apply filters
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    if activity_type:
        query = query.filter(ActivityLog.activity_type == activity_type)
    
    if date_from:
        query = query.filter(func.date(ActivityLog.timestamp) >= date_from)
    
    if date_to:
        query = query.filter(func.date(ActivityLog.timestamp) <= date_to)
    
    # Get logs with pagination
    logs = query.order_by(ActivityLog.timestamp.desc()).all()
    
    # Get users for filter
    users = User.query.all()
    
    # Get unique activity types for filter
    activity_types = db.session.query(ActivityLog.activity_type).distinct().all()
    activity_types = [a[0] for a in activity_types]
    
    return render_template(
        'admin/logs.html',
        logs=logs,
        users=users,
        activity_types=activity_types,
        selected_user=user_id,
        selected_activity=activity_type,
        date_from=date_from_str,
        date_to=date_to_str
    )

@app.route('/admin/employees')
@login_required
@require_role('can_manage_users')
def admin_employees():
    # Get query parameters
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    
    # Parse dates if provided
    today = date.today()
    date_from = today
    date_to = today
    
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid from date format', 'danger')
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid to date format', 'danger')
    
    # Get all users
    users = User.query.filter_by(is_active=True).all()
    
    # Get attendance records for each user
    attendance_data = {}
    
    for user in users:
        attendance_records = Attendance.query.filter(
            Attendance.user_id == user.id,
            func.date(Attendance.check_in) >= date_from,
            func.date(Attendance.check_in) <= date_to
        ).order_by(Attendance.check_in).all()
        
        # Group by date
        by_date = {}
        for record in attendance_records:
            record_date = record.check_in.date()
            
            if record_date not in by_date:
                by_date[record_date] = []
            
            by_date[record_date].append(record)
        
        # Calculate hours worked for each day
        daily_hours = {}
        for day, records in by_date.items():
            total_seconds = 0
            
            for record in records:
                check_in = record.check_in
                check_out = record.check_out or datetime.now()
                
                duration = (check_out - check_in).total_seconds()
                total_seconds += duration
            
            hours_worked = total_seconds / 3600  # Convert seconds to hours
            daily_hours[day] = round(hours_worked, 2)
        
        # Calculate total hours for the period
        total_hours = sum(daily_hours.values())
        
        attendance_data[user.id] = {
            'records': attendance_records,
            'daily_hours': daily_hours,
            'total_hours': round(total_hours, 2)
        }
    
    return render_template(
        'admin/employees.html',
        users=users,
        attendance_data=attendance_data,
        date_from=date_from_str or today.strftime('%Y-%m-%d'),
        date_to=date_to_str or today.strftime('%Y-%m-%d'),
        now=datetime.now()
    )

@app.route('/admin/settings')
@login_required
@require_role('can_archive_data')
def admin_settings():
    # Get database statistics
    stats = {}
    
    # Count records in each table
    stats['patients'] = Patient.query.count()
    stats['visits'] = PatientVisit.query.count()
    stats['prescriptions'] = Prescription.query.count()
    stats['medicines'] = Medicine.query.count()
    stats['sales'] = MedicineSale.query.count()
    stats['receipts'] = Receipt.query.count()
    stats['logs'] = ActivityLog.query.count()
    stats['users'] = User.query.count()
    
    # Get oldest data
    oldest_patient = Patient.query.order_by(Patient.created_at).first()
    oldest_visit = PatientVisit.query.order_by(PatientVisit.visit_date).first()
    oldest_log = ActivityLog.query.order_by(ActivityLog.timestamp).first()
    
    stats['oldest_patient'] = oldest_patient.created_at if oldest_patient else None
    stats['oldest_visit'] = oldest_visit.visit_date if oldest_visit else None
    stats['oldest_log'] = oldest_log.timestamp if oldest_log else None
    
    # Get data by year/month
    monthly_data = {}
    
    current_year = datetime.now().year
    
    # Get visits by month for each year
    for year in range(current_year - 2, current_year + 1):
        monthly_data[year] = {}
        
        for month in range(1, 13):
            start_date = date(year, month, 1)
            
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Skip future months
            if start_date > date.today():
                continue
            
            # Count records for this month
            visit_count = PatientVisit.query.filter(
                func.date(PatientVisit.visit_date) >= start_date,
                func.date(PatientVisit.visit_date) <= end_date
            ).count()
            
            # Include only months with data
            if visit_count > 0:
                month_name = calendar.month_name[month]
                monthly_data[year][month_name] = visit_count
    
    return render_template('admin/settings.html', stats=stats, monthly_data=monthly_data)

@app.route('/admin/archive', methods=['POST'])
@login_required
@require_role('can_archive_data')
def archive_data():
    # Extract form data
    archive_before_str = request.form.get('archive_before')
    include_completed = request.form.get('include_completed') == 'on'
    
    # Validate input
    if not archive_before_str:
        flash('Archive date is required', 'danger')
        return redirect(url_for('admin_settings'))
    
    try:
        archive_date = datetime.strptime(archive_before_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format', 'danger')
        return redirect(url_for('admin_settings'))
    
    if archive_date >= date.today():
        flash('Archive date must be in the past', 'danger')
        return redirect(url_for('admin_settings'))
    
    # Build the query for visits to archive
    visits_query = PatientVisit.query.filter(
        func.date(PatientVisit.visit_date) < archive_date
    )
    
    # If include_completed is checked, only archive completed visits
    if include_completed:
        visits_query = visits_query.filter(PatientVisit.is_completed == True)
    
    # Get the visits to archive
    old_visits = visits_query.all()
    count = len(old_visits)
    
    if count == 0:
        flash('No visits found to archive for the selected criteria', 'warning')
        return redirect(url_for('admin_settings'))
    
    # In a real system, these would be moved to archive tables
    # For this implementation, we'll just log and delete
    for visit in old_visits:
        # Log details before deletion (in a real system, this would be backed up)
        log_activity(
            'Visit Archived', 
            f'Archived visit #{visit.id} for patient {visit.patient.get_full_name()} on {visit.visit_date}'
        )
        
        # Delete related service charges
        ServiceCharge.query.filter_by(visit_id=visit.id).delete()
        
        # Delete visit
        db.session.delete(visit)
    
    db.session.commit()
    
    log_activity('Data Archived', f'Archived {count} visits older than {archive_date}')
    flash(f'Successfully archived {count} visits', 'success')
    
    return redirect(url_for('admin_settings'))

@app.route('/api/roles/<int:role_id>')
@login_required
@require_role('can_manage_users')
def get_role(role_id):
    role = Role.query.get_or_404(role_id)
    return jsonify({
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'can_view_patients': role.can_view_patients,
        'can_add_patients': role.can_add_patients,
        'can_edit_patients': role.can_edit_patients,
        'can_view_pharmacy': role.can_view_pharmacy,
        'can_manage_inventory': role.can_manage_inventory,
        'can_sell_medicine': role.can_sell_medicine,
        'can_view_reports': role.can_view_reports,
        'can_manage_users': role.can_manage_users,
        'can_view_logs': role.can_view_logs,
        'can_process_payments': role.can_process_payments,
        'can_prescribe': role.can_prescribe,
        'can_set_prices': role.can_set_prices,
        'can_archive_data': role.can_archive_data
    })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code=403, error_message='Access forbidden'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500
