// Pharmacy module JavaScript functions

document.addEventListener('DOMContentLoaded', function() {
    // Medicine search functionality
    const medicineSearchInput = document.getElementById('medicineSearch');
    if (medicineSearchInput) {
        medicineSearchInput.addEventListener('input', function() {
            filterMedicines();
        });
    }
    
    // Medicine selection in quick sale or prescription filling
    const addMedicineBtn = document.getElementById('addMedicineBtn');
    if (addMedicineBtn) {
        addMedicineBtn.addEventListener('click', function() {
            const medicineSelect = document.getElementById('medicineSelectTemplate').innerHTML;
            
            const template = `
                <div class="form-field-container border p-3 mb-3 rounded">
                    <div class="row g-2">
                        <div class="col-md-5">
                            <label for="medicine_id[]" class="form-label required-field">Medicine</label>
                            ${medicineSelect}
                        </div>
                        <div class="col-md-2">
                            <label for="quantity[]" class="form-label required-field">Quantity</label>
                            <input type="number" class="form-control" name="quantity[]" min="1" value="1" required onchange="updateMedicineTotal(this)">
                        </div>
                        <div class="col-md-3">
                            <label for="price[]" class="form-label required-field">Price</label>
                            <input type="number" class="form-control currency-input" name="price[]" step="0.01" min="0" required onchange="updateMedicineTotal(this)">
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="button" class="btn btn-danger" onclick="removeFormField(this); recalculateTotal();">
                                <i class="fas fa-trash"></i> Remove
                            </button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-8">
                            <span class="text-muted medicine-details"></span>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="fw-bold">Total: $<span class="item-total">0.00</span></span>
                        </div>
                    </div>
                </div>
            `;
            
            // Add medicine form field
            addFormField('medicineItemsContainer', template);
        });
    }
    
    // Medicine selection in prescription filling
    setupPrescriptionItems();
    
    // Setup select2 for enhanced selects if the library is available
    if (typeof $.fn.select2 !== 'undefined') {
        $('.medicine-select').select2({
            theme: 'bootstrap4',
            placeholder: 'Select a medicine',
            allowClear: true
        });
    }
    
    // Initialize medicine price fetch on medicine selection
    const medicineSelects = document.querySelectorAll('select[name="medicine_id[]"]');
    medicineSelects.forEach(select => {
        select.addEventListener('change', function() {
            updateMedicinePrice(this);
        });
    });
});

// Filter medicines in inventory table
function filterMedicines() {
    const input = document.getElementById('medicineSearch');
    const filter = input.value.toUpperCase();
    const table = document.getElementById('medicinesTable');
    if (!table) return;
    
    const tr = table.getElementsByTagName('tr');
    
    for (let i = 1; i < tr.length; i++) { // Start from 1 to skip header row
        const tdName = tr[i].getElementsByTagName('td')[0]; // Name column
        const tdGeneric = tr[i].getElementsByTagName('td')[1]; // Generic name column
        
        if (tdName && tdGeneric) {
            const nameValue = tdName.textContent || tdName.innerText;
            const genericValue = tdGeneric.textContent || tdGeneric.innerText;
            
            if (nameValue.toUpperCase().indexOf(filter) > -1 || genericValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = '';
            } else {
                tr[i].style.display = 'none';
            }
        }
    }
}

// Update medicine price based on selection
function updateMedicinePrice(selectElement) {
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const itemContainer = selectElement.closest('.form-field-container');
    const priceInput = itemContainer.querySelector('input[name="price[]"]');
    const medicineDetails = itemContainer.querySelector('.medicine-details');
    
    if (selectedOption && selectedOption.value) {
        const price = selectedOption.getAttribute('data-price');
        const minPrice = selectedOption.getAttribute('data-min-price');
        const stock = selectedOption.getAttribute('data-stock');
        
        if (priceInput && price) {
            priceInput.value = price;
            priceInput.min = minPrice || 0;
            
            // Update medicine details display
            if (medicineDetails) {
                medicineDetails.innerHTML = `Stock: ${stock || 0} | Min Price: $${minPrice || '0.00'}`;
            }
            
            // Update total
            updateMedicineTotal(priceInput);
        }
    } else {
        if (priceInput) {
            priceInput.value = '';
            priceInput.min = 0;
        }
        if (medicineDetails) {
            medicineDetails.innerHTML = '';
        }
    }
}

// Update total for a medicine item
function updateMedicineTotal(inputElement) {
    const itemContainer = inputElement.closest('.form-field-container');
    const quantityInput = itemContainer.querySelector('input[name="quantity[]"]');
    const priceInput = itemContainer.querySelector('input[name="price[]"]');
    const totalSpan = itemContainer.querySelector('.item-total');
    
    if (quantityInput && priceInput && totalSpan) {
        const quantity = parseFloat(quantityInput.value) || 0;
        const price = parseFloat(priceInput.value) || 0;
        const total = quantity * price;
        
        totalSpan.textContent = total.toFixed(2);
    }
    
    // Recalculate grand total
    recalculateTotal();
}

// Recalculate grand total for all items
function recalculateTotal() {
    const totalSpans = document.querySelectorAll('.item-total');
    let grandTotal = 0;
    
    totalSpans.forEach(span => {
        grandTotal += parseFloat(span.textContent) || 0;
    });
    
    const grandTotalElement = document.getElementById('grandTotal');
    if (grandTotalElement) {
        grandTotalElement.textContent = grandTotal.toFixed(2);
    }
}

// Setup prescription items from existing data
function setupPrescriptionItems() {
    const prescriptionItems = document.querySelectorAll('.prescription-item');
    prescriptionItems.forEach(item => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        const quantityInput = item.querySelector('input[name="quantity[]"]');
        const priceInput = item.querySelector('input[name="price[]"]');
        
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                const itemRow = this.closest('tr');
                const quantityCell = itemRow.querySelector('.quantity-cell');
                const priceCell = itemRow.querySelector('.price-cell');
                
                if (this.checked) {
                    quantityCell.classList.remove('d-none');
                    priceCell.classList.remove('d-none');
                } else {
                    quantityCell.classList.add('d-none');
                    priceCell.classList.add('d-none');
                }
                
                recalculateTotal();
            });
        }
        
        if (quantityInput || priceInput) {
            quantityInput?.addEventListener('input', function() {
                updateMedicineTotal(this);
            });
            
            priceInput?.addEventListener('input', function() {
                updateMedicineTotal(this);
            });
        }
    });
}

// Show restock medicine modal
function showRestockModal(medicineId, medicineName, currentStock) {
    const modal = document.getElementById('restockModal');
    const modalTitle = modal.querySelector('.modal-title');
    const medicineIdInput = document.getElementById('restock_medicine_id');
    const currentStockSpan = document.getElementById('current_stock');
    
    modalTitle.textContent = `Restock: ${medicineName}`;
    medicineIdInput.value = medicineId;
    currentStockSpan.textContent = currentStock;
    
    // Clear previous input
    document.getElementById('restock_quantity').value = '';
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}
