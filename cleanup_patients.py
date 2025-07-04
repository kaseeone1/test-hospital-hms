from app import app, db
from models import Patient, PatientVisit, Prescription, PrescriptionItem, ServiceCharge, Receipt, Payment, MedicineSale

def cleanup_patient_data():
    with app.app_context():
        try:
            # Delete service charges
            ServiceCharge.query.delete()
            print("Deleted service charges")

            # Delete prescription items
            PrescriptionItem.query.delete()
            print("Deleted prescription items")

            # Delete prescriptions
            Prescription.query.delete()
            print("Deleted prescriptions")

            # Delete patient visits
            PatientVisit.query.delete()
            print("Deleted patient visits")

            # Delete medicine sales
            MedicineSale.query.delete()
            print("Deleted medicine sales")

            # Delete payments
            Payment.query.delete()
            print("Deleted payments")

            # Delete receipts
            Receipt.query.delete()
            print("Deleted receipts")

            # Finally, delete patients
            Patient.query.delete()
            print("Deleted patients")

            # Commit all changes
            db.session.commit()
            print("Successfully cleaned up all patient data")

        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {str(e)}")

if __name__ == '__main__':
    cleanup_patient_data() 