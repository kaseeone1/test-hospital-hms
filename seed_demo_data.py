import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app, db
from models import (
    User, Role, Patient, PatientVisit, Medicine, MedicineSale, 
    ServiceCharge, Payment, Receipt, Prescription, PrescriptionItem,
    ActivityLog, Attendance
)

def generate_demo_data():
    """Generate comprehensive demo data for the HMS."""
    
    with app.app_context():
        print("🌱 Starting demo data generation...")
        
        # Clear existing data (except users and roles)
        print("🧹 Clearing existing demo data...")
        MedicineSale.query.delete()
        ServiceCharge.query.delete()
        Payment.query.delete()
        Receipt.query.delete()
        PrescriptionItem.query.delete()
        Prescription.query.delete()
        PatientVisit.query.delete()
        Patient.query.delete()
        Medicine.query.delete()
        ActivityLog.query.delete()
        Attendance.query.delete()
        db.session.commit()
        
        # Get existing roles and users
        admin_role = Role.query.filter_by(name='Admin').first()
        doctor_role = Role.query.filter_by(name='Doctor').first()
        receptionist_role = Role.query.filter_by(name='Receptionist').first()
        cashier_role = Role.query.filter_by(name='Cashier').first()
        pharmacist_role = Role.query.filter_by(name='Pharmacist').first()
        
        # Create additional staff users if they don't exist
        staff_users = []
        
        # Doctors
        doctors = [
            {'username': 'dr.smith', 'email': 'smith@testhospital.com', 'first_name': 'Dr. John', 'last_name': 'Smith', 'role': doctor_role},
            {'username': 'dr.johnson', 'email': 'johnson@testhospital.com', 'first_name': 'Dr. Sarah', 'last_name': 'Johnson', 'role': doctor_role},
            {'username': 'dr.williams', 'email': 'williams@testhospital.com', 'first_name': 'Dr. Michael', 'last_name': 'Williams', 'role': doctor_role},
        ]
        
        # Receptionists
        receptionists = [
            {'username': 'reception1', 'email': 'reception1@testhospital.com', 'first_name': 'Mary', 'last_name': 'Davis', 'role': receptionist_role},
            {'username': 'reception2', 'email': 'reception2@testhospital.com', 'first_name': 'Lisa', 'last_name': 'Brown', 'role': receptionist_role},
        ]
        
        # Cashiers
        cashiers = [
            {'username': 'cashier1', 'email': 'cashier1@testhospital.com', 'first_name': 'Robert', 'last_name': 'Wilson', 'role': cashier_role},
            {'username': 'cashier2', 'email': 'cashier2@testhospital.com', 'first_name': 'Jennifer', 'last_name': 'Taylor', 'role': cashier_role},
        ]
        
        # Pharmacists
        pharmacists = [
            {'username': 'pharmacist1', 'email': 'pharmacist1@testhospital.com', 'first_name': 'David', 'last_name': 'Anderson', 'role': pharmacist_role},
            {'username': 'pharmacist2', 'email': 'pharmacist2@testhospital.com', 'first_name': 'Emily', 'last_name': 'Thomas', 'role': pharmacist_role},
        ]
        
        all_staff = doctors + receptionists + cashiers + pharmacists
        
        for staff_data in all_staff:
            existing_user = User.query.filter_by(username=staff_data['username']).first()
            if not existing_user:
                user = User(
                    username=staff_data['username'],
                    email=staff_data['email'],
                    password_hash=generate_password_hash('password123'),
                    first_name=staff_data['first_name'],
                    last_name=staff_data['last_name'],
                    role_id=staff_data['role'].id,
                    is_active=True
                )
                db.session.add(user)
                staff_users.append(user)
            else:
                staff_users.append(existing_user)
        
        db.session.commit()
        print(f"✅ Created {len(staff_users)} staff users")
        
        # Create medicines
        print("💊 Creating medicines...")
        medicines_data = [
            {'name': 'Paracetamol 500mg', 'generic_name': 'Acetaminophen', 'purchase_price': 0.50, 'selling_price': 2.00, 'min_selling_price': 1.50, 'stock_quantity': 500, 'manufacturer': 'Generic Pharma'},
            {'name': 'Amoxicillin 250mg', 'generic_name': 'Amoxicillin', 'purchase_price': 1.20, 'selling_price': 4.50, 'min_selling_price': 3.00, 'stock_quantity': 200, 'manufacturer': 'Antibiotic Corp'},
            {'name': 'Ibuprofen 400mg', 'generic_name': 'Ibuprofen', 'purchase_price': 0.80, 'selling_price': 3.00, 'min_selling_price': 2.00, 'stock_quantity': 300, 'manufacturer': 'Pain Relief Inc'},
            {'name': 'Omeprazole 20mg', 'generic_name': 'Omeprazole', 'purchase_price': 2.50, 'selling_price': 8.00, 'min_selling_price': 6.00, 'stock_quantity': 150, 'manufacturer': 'Gastro Health'},
            {'name': 'Metformin 500mg', 'generic_name': 'Metformin', 'purchase_price': 1.80, 'selling_price': 6.00, 'min_selling_price': 4.50, 'stock_quantity': 100, 'manufacturer': 'Diabetes Care'},
            {'name': 'Amlodipine 5mg', 'generic_name': 'Amlodipine', 'purchase_price': 2.20, 'selling_price': 7.50, 'min_selling_price': 5.50, 'stock_quantity': 120, 'manufacturer': 'Cardio Pharma'},
            {'name': 'Cetirizine 10mg', 'generic_name': 'Cetirizine', 'purchase_price': 0.60, 'selling_price': 2.50, 'min_selling_price': 1.80, 'stock_quantity': 400, 'manufacturer': 'Allergy Relief'},
            {'name': 'Loratadine 10mg', 'generic_name': 'Loratadine', 'purchase_price': 0.70, 'selling_price': 3.20, 'min_selling_price': 2.20, 'stock_quantity': 350, 'manufacturer': 'Allergy Relief'},
            {'name': 'Ranitidine 150mg', 'generic_name': 'Ranitidine', 'purchase_price': 1.50, 'selling_price': 5.00, 'min_selling_price': 3.50, 'stock_quantity': 180, 'manufacturer': 'Gastro Health'},
            {'name': 'Diclofenac 50mg', 'generic_name': 'Diclofenac', 'purchase_price': 1.00, 'selling_price': 4.00, 'min_selling_price': 2.80, 'stock_quantity': 250, 'manufacturer': 'Pain Relief Inc'},
        ]
        
        medicines = []
        for med_data in medicines_data:
            medicine = Medicine(
                name=med_data['name'],
                generic_name=med_data['generic_name'],
                purchase_price=med_data['purchase_price'],
                selling_price=med_data['selling_price'],
                min_selling_price=med_data['min_selling_price'],
                stock_quantity=med_data['stock_quantity'],
                manufacturer=med_data['manufacturer'],
                description=f"Standard {med_data['generic_name']} medication",
                created_by=random.choice(staff_users).id
            )
            db.session.add(medicine)
            medicines.append(medicine)
        
        db.session.commit()
        print(f"✅ Created {len(medicines)} medicines")
        
        # Create patients
        print("👥 Creating patients...")
        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Christopher', 'Karen', 'Charles', 'Nancy', 'Daniel', 'Lisa', 'Matthew', 'Betty', 'Anthony', 'Helen', 'Mark', 'Sandra', 'Donald', 'Donna', 'Steven', 'Carol', 'Paul', 'Ruth', 'Andrew', 'Sharon', 'Joshua', 'Michelle', 'Kenneth', 'Laura', 'Kevin', 'Emily', 'Brian', 'Kimberly', 'George', 'Deborah', 'Edward', 'Dorothy', 'Ronald', 'Lisa', 'Timothy', 'Nancy', 'Jason', 'Karen', 'Jeffrey', 'Betty', 'Ryan', 'Helen', 'Jacob', 'Sandra', 'Gary', 'Donna', 'Nicholas', 'Carol', 'Eric', 'Ruth', 'Jonathan', 'Sharon', 'Stephen', 'Michelle', 'Larry', 'Laura', 'Justin', 'Emily', 'Scott', 'Kimberly', 'Brandon', 'Deborah', 'Benjamin', 'Dorothy', 'Samuel', 'Lisa', 'Frank', 'Nancy', 'Gregory', 'Karen', 'Raymond', 'Betty', 'Alexander', 'Helen', 'Patrick', 'Sandra', 'Jack', 'Donna', 'Dennis', 'Carol', 'Jerry', 'Ruth']
        
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker', 'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy', 'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Bailey', 'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson', 'Watson', 'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray', 'Mendoza', 'Ruiz', 'Hughes', 'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers', 'Long', 'Ross', 'Foster', 'Jimenez']
        
        patients = []
        start_date = datetime.now() - timedelta(days=365)
        
        for i in range(150):  # Create 150 patients
            registration_date = start_date + timedelta(days=random.randint(0, 365))
            patient = Patient(
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                gender=random.choice(['Male', 'Female']),
                date_of_birth=datetime.now() - timedelta(days=random.randint(6570, 29200)),  # 18-80 years old
                phone=f"+2547{random.randint(10000000, 99999999)}",
                email=f"patient{i+1}@example.com",
                address=f"{random.randint(1, 999)} {random.choice(['Street', 'Avenue', 'Road', 'Lane'])}",
                registered_by=random.choice(staff_users).id,
                created_at=registration_date,
                next_of_kin_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                next_of_kin_relationship=random.choice(['Spouse', 'Parent', 'Sibling', 'Child', 'Friend']),
                next_of_kin_phone=f"+2547{random.randint(10000000, 99999999)}",
                next_of_kin_address=f"{random.randint(1, 999)} {random.choice(['Street', 'Avenue', 'Road', 'Lane'])}"
            )
            db.session.add(patient)
            patients.append(patient)
        
        db.session.commit()
        print(f"✅ Created {len(patients)} patients")
        
        # Create patient visits
        print("🏥 Creating patient visits...")
        symptoms_list = [
            'Fever and cough', 'Headache', 'Chest pain', 'Abdominal pain', 'Back pain',
            'Joint pain', 'Shortness of breath', 'Dizziness', 'Nausea and vomiting',
            'Fatigue', 'Insomnia', 'Anxiety', 'Depression', 'High blood pressure',
            'Diabetes symptoms', 'Allergic reactions', 'Skin rash', 'Eye problems',
            'Ear pain', 'Throat soreness', 'Dental pain', 'Urinary problems'
        ]
        
        diagnoses_list = [
            'Upper respiratory infection', 'Hypertension', 'Type 2 Diabetes', 'Anxiety disorder',
            'Depression', 'Migraine', 'Gastritis', 'Back strain', 'Arthritis',
            'Asthma', 'Allergic rhinitis', 'Dermatitis', 'Conjunctivitis', 'Otitis media',
            'Pharyngitis', 'Dental caries', 'Urinary tract infection', 'Anemia',
            'Hyperlipidemia', 'Osteoporosis', 'Chronic kidney disease', 'Heart disease'
        ]
        
        visits = []
        doctors = [u for u in staff_users if u.role.name == 'Doctor']
        
        for patient in patients:
            # Each patient has 1-5 visits
            num_visits = random.randint(1, 5)
            for visit_num in range(num_visits):
                visit_date = patient.created_at + timedelta(days=random.randint(1, 365))
                if visit_date > datetime.now():
                    visit_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                visit = PatientVisit(
                    patient_id=patient.id,
                    doctor_id=random.choice(doctors).id,
                    visit_date=visit_date,
                    symptoms=random.choice(symptoms_list),
                    diagnosis=random.choice(diagnoses_list),
                    notes=f"Patient reported {random.choice(symptoms_list).lower()}. Prescribed appropriate medication.",
                    follow_up_date=visit_date + timedelta(days=random.randint(7, 90)) if random.random() > 0.3 else None,
                    is_completed=random.random() > 0.1  # 90% completed
                )
                db.session.add(visit)
                visits.append(visit)
        
        db.session.commit()
        print(f"✅ Created {len(visits)} patient visits")
        
        # Create service charges
        print("💰 Creating service charges...")
        services = [
            {'name': 'Consultation', 'amount': 50.0},
            {'name': 'Laboratory Test', 'amount': 150.0},
            {'name': 'X-Ray', 'amount': 200.0},
            {'name': 'ECG', 'amount': 100.0},
            {'name': 'Ultrasound', 'amount': 300.0},
            {'name': 'Minor Surgery', 'amount': 500.0},
            {'name': 'Dental Cleaning', 'amount': 80.0},
            {'name': 'Physical Therapy', 'amount': 120.0},
            {'name': 'Vaccination', 'amount': 60.0},
            {'name': 'Emergency Care', 'amount': 400.0}
        ]
        
        service_charges = []
        for visit in visits:
            if random.random() > 0.2:  # 80% of visits have service charges
                num_services = random.randint(1, 3)
                for _ in range(num_services):
                    service = random.choice(services)
                    service_charge = ServiceCharge(
                        visit_id=visit.id,
                        service_name=service['name'],
                        description=f"Standard {service['name'].lower()} service",
                        charge_amount=service['amount'],
                        created_by=random.choice(doctors).id,
                        is_paid=random.random() > 0.3  # 70% paid
                    )
                    db.session.add(service_charge)
                    service_charges.append(service_charge)
        
        db.session.commit()
        print(f"✅ Created {len(service_charges)} service charges")
        
        # Create prescriptions
        print("💊 Creating prescriptions...")
        prescriptions = []
        for visit in visits:
            if random.random() > 0.3:  # 70% of visits have prescriptions
                prescription = Prescription(
                    patient_id=visit.patient_id,
                    doctor_id=visit.doctor_id,
                    visit_id=visit.id,
                    prescription_date=visit.visit_date,
                    notes=f"Prescription for {visit.diagnosis}",
                    is_filled=random.random() > 0.2  # 80% filled
                )
                db.session.add(prescription)
                prescriptions.append(prescription)
        
        db.session.commit()
        print(f"✅ Created {len(prescriptions)} prescriptions")
        
        # Create prescription items
        print("📋 Creating prescription items...")
        prescription_items = []
        for prescription in prescriptions:
            num_medicines = random.randint(1, 3)
            for _ in range(num_medicines):
                medicine = random.choice(medicines)
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_id=medicine.id,
                    dosage=f"{random.randint(1, 2)} tablet{'s' if random.randint(1, 2) > 1 else ''}",
                    duration=f"{random.randint(5, 14)} days",
                    instructions="Take with food",
                    quantity=random.randint(10, 30)
                )
                db.session.add(item)
                prescription_items.append(item)
        
        db.session.commit()
        print(f"✅ Created {len(prescription_items)} prescription items")
        
        # Create medicine sales
        print("🛒 Creating medicine sales...")
        medicine_sales = []
        cashiers = [u for u in staff_users if u.role.name == 'Cashier']
        pharmacists = [u for u in staff_users if u.role.name == 'Pharmacist']
        
        # Sales from prescriptions
        for item in prescription_items:
            if random.random() > 0.3:  # 70% of prescription items are sold
                sale = MedicineSale(
                    medicine_id=item.medicine_id,
                    prescription_item_id=item.id,
                    quantity=item.quantity,
                    selling_price=item.medicine.selling_price,
                    total_amount=item.quantity * item.medicine.selling_price,
                    sold_by=random.choice(pharmacists).id,
                    sale_date=item.prescription.prescription_date + timedelta(hours=random.randint(1, 24))
                )
                db.session.add(sale)
                medicine_sales.append(sale)
        
        # Direct sales (without prescriptions)
        for _ in range(200):
            medicine = random.choice(medicines)
            quantity = random.randint(1, 5)
            sale = MedicineSale(
                medicine_id=medicine.id,
                quantity=quantity,
                selling_price=medicine.selling_price,
                total_amount=quantity * medicine.selling_price,
                sold_by=random.choice(pharmacists).id,
                sale_date=start_date + timedelta(days=random.randint(0, 365))
            )
            db.session.add(sale)
            medicine_sales.append(sale)
        
        db.session.commit()
        print(f"✅ Created {len(medicine_sales)} medicine sales")
        
        # Create receipts
        print("🧾 Creating receipts...")
        receipts = []
        
        # Pharmacy receipts
        for sale in medicine_sales:
            if random.random() > 0.1:  # 90% of sales have receipts
                patient_id = None
                if sale.prescription_item_id:
                    prescription_item = PrescriptionItem.query.get(sale.prescription_item_id)
                    if prescription_item:
                        patient_id = prescription_item.prescription.patient_id
                
                receipt = Receipt(
                    patient_id=patient_id,
                    total_amount=sale.total_amount,
                    is_pharmacy_receipt=True,
                    created_by=sale.sold_by,
                    created_at=sale.sale_date
                )
                db.session.add(receipt)
                receipts.append(receipt)
                sale.receipt_id = receipt.id
        
        # Service receipts
        for charge in service_charges:
            if charge.is_paid and random.random() > 0.2:  # 80% of paid services have receipts
                receipt = Receipt(
                    patient_id=charge.visit.patient_id,
                    visit_id=charge.visit_id,
                    total_amount=charge.charge_amount,
                    is_pharmacy_receipt=False,
                    created_by=random.choice(cashiers).id,
                    created_at=charge.created_at + timedelta(hours=random.randint(1, 24))
                )
                db.session.add(receipt)
                receipts.append(receipt)
        
        db.session.commit()
        print(f"✅ Created {len(receipts)} receipts")
        
        # Create payments
        print("💳 Creating payments...")
        payments = []
        payment_methods = ['Cash', 'M-Pesa', 'Card', 'Bank Transfer']
        
        for receipt in receipts:
            payment = Payment(
                amount=receipt.total_amount,
                payment_date=receipt.created_at,
                payment_method=random.choice(payment_methods),
                received_by=receipt.created_by,
                receipt_id=receipt.id
            )
            db.session.add(payment)
            payments.append(payment)
        
        db.session.commit()
        print(f"✅ Created {len(payments)} payments")
        
        # Create activity logs
        print("📝 Creating activity logs...")
        activities = [
            'User Login', 'User Logout', 'Patient Registered', 'Patient Updated',
            'Visit Created', 'Prescription Created', 'Medicine Sold', 'Payment Processed',
            'Report Generated', 'Inventory Updated', 'User Created', 'Role Updated'
        ]
        
        for _ in range(500):
            activity = ActivityLog(
                user_id=random.choice(staff_users).id,
                activity_type=random.choice(activities),
                description=f"Demo activity: {random.choice(activities)}",
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                timestamp=start_date + timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
            )
            db.session.add(activity)
        
        db.session.commit()
        print(f"✅ Created 500 activity logs")
        
        # Create attendance records
        print("⏰ Creating attendance records...")
        for user in staff_users:
            # Create attendance for the last 30 days
            for day in range(30):
                check_in = datetime.now() - timedelta(days=day, hours=random.randint(8, 10))
                check_out = check_in + timedelta(hours=random.randint(7, 9))
                
                attendance = Attendance(
                    user_id=user.id,
                    check_in=check_in,
                    check_out=check_out
                )
                db.session.add(attendance)
        
        db.session.commit()
        print(f"✅ Created attendance records for all staff")
        
        print("\n🎉 Demo data generation completed successfully!")
        print(f"📊 Summary:")
        print(f"   - {len(patients)} patients")
        print(f"   - {len(visits)} patient visits")
        print(f"   - {len(medicines)} medicines")
        print(f"   - {len(medicine_sales)} medicine sales")
        print(f"   - {len(receipts)} receipts")
        print(f"   - {len(payments)} payments")
        print(f"   - {len(service_charges)} service charges")
        print(f"   - {len(prescriptions)} prescriptions")
        print(f"   - 500 activity logs")
        print(f"   - Attendance records for all staff")
        
        print(f"\n🔑 Login Credentials:")
        print(f"   Super Admin: Kaseeone / @Kenya3404@Kenya3404")
        print(f"   Regular Admin: admin / admin123")
        print(f"   Staff Users: username / password123")

if __name__ == '__main__':
    generate_demo_data() 