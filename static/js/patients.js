// Patients module JavaScript functions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize datepickers
    const datepickers = document.querySelectorAll('.datepicker');
    datepickers.forEach(function(input) {
        // Simple date input enhancement - relies on HTML5 date input
        input.addEventListener('focus', function() {
            if (!this.value) {
                // Set default to today for appropriate fields
                if (this.classList.contains('default-today')) {
                    this.valueAsDate = new Date();
                }
            }
        });
    });

    // Calculate and display age when date of birth changes
    const dobInput = document.getElementById('date_of_birth');
    const ageDisplay = document.getElementById('calculated_age');
    
    if (dobInput && ageDisplay) {
        dobInput.addEventListener('change', function() {
            if (this.value) {
                const dob = new Date(this.value);
                const age = calculateAge(dob);
                ageDisplay.textContent = age ? `${age} years` : '';
            } else {
                ageDisplay.textContent = '';
            }
        });
        
        // Trigger on load if value exists
        if (dobInput.value) {
            const dob = new Date(dobInput.value);
            const age = calculateAge(dob);
            ageDisplay.textContent = age ? `${age} years` : '';
        }
    }
    
    // Patient search functionality
    const patientSearchInput = document.getElementById('patientSearch');
    if (patientSearchInput) {
        patientSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const patientRows = document.querySelectorAll('tr.patient-row');
            
            patientRows.forEach(function(row) {
                const patientName = row.querySelector('.patient-name').textContent.toLowerCase();
                const patientPhone = row.querySelector('.patient-phone').textContent.toLowerCase();
                
                if (patientName.includes(searchTerm) || patientPhone.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Treatment page - add service charge
    const addServiceBtn = document.getElementById('addServiceBtn');
    if (addServiceBtn) {
        addServiceBtn.addEventListener('click', function() {
            const template = `
                <div class="form-field-container border p-3 mb-3 rounded">
                    <div class="row g-2">
                        <div class="col-md-5">
                            <label for="service_name" class="form-label required-field">Service Name</label>
                            <input type="text" class="form-control" name="service_name" required>
                        </div>
                        <div class="col-md-5">
                            <label for="charge_amount" class="form-label required-field">Charge Amount</label>
                            <input type="number" class="form-control currency-input" name="charge_amount" step="0.01" min="0" required>
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="button" class="btn btn-danger" onclick="removeFormField(this)">
                                <i class="fas fa-trash"></i> Remove
                            </button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-12">
                            <label for="description" class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="2"></textarea>
                        </div>
                    </div>
                </div>
            `;
            
            // Add service form field
            addFormField('serviceChargesContainer', template);
        });
    }
    
    // Treatment page - add prescription
    const addPrescriptionItemBtn = document.getElementById('addPrescriptionItemBtn');
    if (addPrescriptionItemBtn) {
        addPrescriptionItemBtn.addEventListener('click', function() {
            const medicineSelect = document.getElementById('medicineSelectTemplate').innerHTML;
            
            const template = `
                <div class="form-field-container border p-3 mb-3 rounded">
                    <div class="row g-2">
                        <div class="col-md-5">
                            <label for="medicine_id[]" class="form-label required-field">Medicine</label>
                            ${medicineSelect}
                        </div>
                        <div class="col-md-3">
                            <label for="quantity[]" class="form-label required-field">Quantity</label>
                            <input type="number" class="form-control" name="quantity[]" min="1" value="1" required>
                        </div>
                        <div class="col-md-2">
                            <label for="dosage[]" class="form-label">Dosage</label>
                            <input type="text" class="form-control" name="dosage[]" placeholder="e.g., 1-0-1">
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="button" class="btn btn-danger" onclick="removeFormField(this)">
                                <i class="fas fa-trash"></i> Remove
                            </button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <label for="duration[]" class="form-label">Duration</label>
                            <input type="text" class="form-control" name="duration[]" placeholder="e.g., 7 days">
                        </div>
                        <div class="col-md-6">
                            <label for="instructions[]" class="form-label">Instructions</label>
                            <input type="text" class="form-control" name="instructions[]" placeholder="e.g., After meals">
                        </div>
                    </div>
                </div>
            `;
            
            // Add prescription item form field
            addFormField('prescriptionItemsContainer', template);
        });
    }
    
    // Patient visit history - view toggle
    const toggleHistoryBtn = document.getElementById('toggleHistoryBtn');
    if (toggleHistoryBtn) {
        toggleHistoryBtn.addEventListener('click', function() {
            const historySection = document.getElementById('patientHistorySection');
            historySection.classList.toggle('d-none');
            
            // Update button text
            if (historySection.classList.contains('d-none')) {
                this.innerHTML = '<i class="fas fa-history"></i> Show History';
            } else {
                this.innerHTML = '<i class="fas fa-times"></i> Hide History';
            }
        });
    }
});

// Function to filter patients table
function filterPatients() {
    const input = document.getElementById('patientSearch');
    const filter = input.value.toUpperCase();
    const table = document.getElementById('patientsTable');
    const tr = table.getElementsByTagName('tr');
    
    for (let i = 1; i < tr.length; i++) { // Start from 1 to skip header row
        const tdName = tr[i].getElementsByTagName('td')[1]; // Name column
        const tdPhone = tr[i].getElementsByTagName('td')[3]; // Phone column
        
        if (tdName && tdPhone) {
            const nameValue = tdName.textContent || tdName.innerText;
            const phoneValue = tdPhone.textContent || tdPhone.innerText;
            
            if (nameValue.toUpperCase().indexOf(filter) > -1 || phoneValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = '';
            } else {
                tr[i].style.display = 'none';
            }
        }
    }
}
