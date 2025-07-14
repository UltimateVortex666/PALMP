// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Form validation
function validatePhoneNumber(phone) {
    const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

function validateAmount(amount) {
    return !isNaN(amount) && parseFloat(amount) > 0;
}

// File upload handling
function handleFileUpload(input) {
    const file = input.files[0];
    if (file) {
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            showAlert('Please select a valid image file (JPEG, PNG, GIF)', 'danger');
            input.value = '';
            return false;
        }
        
        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            showAlert('File size must be less than 5MB', 'danger');
            input.value = '';
            return false;
        }
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('palm-preview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(file);
        return true;
    }
    return false;
}

// Add money functionality
function addMoney(amount, otp) {
    const amountInput = document.getElementById('amount');
    const otpInput = document.getElementById('otp');
    const formData = new FormData();
    formData.append('amount', amount);
    formData.append('otp', otp);
    fetch('/user/add_money', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            amountInput.value = '';
            otpInput.value = '';
            otpInput.style.display = 'none';
            document.getElementById('add-money-btn').disabled = true;
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.error || 'Failed to add money', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while adding money', 'danger');
    });
}

// Create payment request
function createPaymentRequest() {
    const amountInput = document.getElementById('payment-amount');
    const noteInput = document.getElementById('payment-note');
    const amount = parseFloat(amountInput.value);
    const note = noteInput.value.trim();
    
    if (!validateAmount(amount)) {
        showAlert('Please enter a valid amount', 'danger');
        return;
    }
    
    if (!note) {
        showAlert('Please enter a payment note', 'danger');
        return;
    }
    
    const formData = new FormData();
    formData.append('amount', amount);
    formData.append('note', note);
    
    fetch('/merchant/create_payment', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data && data.error) {
            showAlert(data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while creating payment request', 'danger');
    });
}

// Palm scan simulation
function simulatePalmScan() {
    const scanArea = document.querySelector('.palm-scan-area');
    const scanIcon = document.querySelector('.palm-scan-icon');
    const scanText = document.querySelector('.palm-scan-text');
    
    if (scanArea && scanIcon && scanText) {
        // Show scanning animation
        scanIcon.innerHTML = '🔄';
        scanText.textContent = 'Scanning palm...';
        scanArea.style.borderColor = '#28a745';
        scanArea.style.background = 'rgba(40, 167, 69, 0.1)';
        
        // Simulate scan delay
        setTimeout(() => {
            scanIcon.innerHTML = '✅';
            scanText.textContent = 'Palm scan successful!';
            scanArea.style.borderColor = '#28a745';
            scanArea.style.background = 'rgba(40, 167, 69, 0.1)';
            
            // Show user input form
            showUserInputForm();
        }, 2000);
    }
}

function showUserInputForm() {
    const scanContainer = document.querySelector('.palm-scan-container');
    if (scanContainer) {
        const userForm = `
            <div class="card">
                <h3>Enter User Phone Number</h3>
                <div class="form-group">
                    <label for="user-phone">Phone Number:</label>
                    <input type="tel" id="user-phone" class="form-control" placeholder="Enter user's phone number" required>
                </div>
                <button type="button" class="btn btn-primary" onclick="processPayment()">Process Payment</button>
            </div>
        `;
        scanContainer.innerHTML = userForm;
    }
}

function processPayment() {
    const userPhone = document.getElementById('user-phone').value.trim();
    
    if (!userPhone) {
        showAlert('Please enter a phone number', 'danger');
        return;
    }
    
    const formData = new FormData();
    formData.append('user_phone', userPhone);
    
    fetch('/payment/process', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => {
                window.location.href = '/merchant/dashboard';
            }, 2000);
        } else {
            showAlert(data.error || 'Payment failed', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while processing payment', 'danger');
    });
}

// Transaction history formatting
function formatTransactionHistory() {
    const transactionItems = document.querySelectorAll('.transaction-item');
    
    transactionItems.forEach(item => {
        const amountElement = item.querySelector('.transaction-amount');
        const dateElement = item.querySelector('.transaction-date');
        
        if (amountElement) {
            // Remove any non-numeric characters (like $) before parsing
            const amountText = amountElement.textContent.replace(/[^0-9.-]+/g, "");
            const amount = parseFloat(amountText);
            amountElement.textContent = formatCurrency(amount);
            
            if (amount > 0) {
                amountElement.classList.add('positive');
            } else {
                amountElement.classList.add('negative');
            }
        }
        
        if (dateElement) {
            const date = dateElement.textContent;
            dateElement.textContent = formatDate(date);
        }
    });
}

// OTP sending for User and Merchant Login
function sendOtp(endpoint, phoneInputSelector, buttonSelector) {
    const phoneInput = document.querySelector(phoneInputSelector);
    const button = document.querySelector(buttonSelector);
    if (!phoneInput || !button) return;
    button.addEventListener('click', function() {
        const phone = phoneInput.value.trim();
        if (!validatePhoneNumber(phone)) {
            showAlert('Please enter a valid phone number', 'danger');
            return;
        }
        button.disabled = true;
        button.textContent = 'Sending...';
        fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `phone_number=${encodeURIComponent(phone)}`
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
            } else {
                showAlert(data.error || 'Failed to send OTP', 'danger');
            }
        })
        .catch(() => {
            showAlert('An error occurred while sending OTP', 'danger');
        })
        .finally(() => {
            button.disabled = false;
            button.textContent = 'Send OTP';
        });
    });
}

// Initialize page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const phoneInputs = form.querySelectorAll('input[type="tel"]');
            phoneInputs.forEach(input => {
                if (input.value && !validatePhoneNumber(input.value)) {
                    e.preventDefault();
                    showAlert('Please enter a valid phone number', 'danger');
                    return;
                }
            });
        });
    });
    
    // Initialize file upload handlers
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            handleFileUpload(this);
        });
    });
    
    // Initialize payment request functionality
    const createPaymentBtn = document.getElementById('create-payment-btn');
    if (createPaymentBtn) {
        createPaymentBtn.addEventListener('click', createPaymentRequest);
    }
    
    // Initialize palm scan functionality
    const palmScanBtn = document.getElementById('palm-scan-btn');
    if (palmScanBtn) {
        palmScanBtn.addEventListener('click', simulatePalmScan);
    }
    
    // Format transaction history
    formatTransactionHistory();
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.remove();
        }, 5000);
    });

    // User Login OTP
    if (document.getElementById('user-otp-btn')) {
        sendOtp('/user/send_otp', '#phone_number', '#user-otp-btn');
    }
    // Merchant Login OTP
    if (document.getElementById('merchant-otp-btn')) {
        sendOtp('/merchant/send_otp', '#phone_number', '#merchant-otp-btn');
    }

    // Quick amount buttons
    if (document.querySelectorAll('.quick-amount-btn').length) {
        document.querySelectorAll('.quick-amount-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.getElementById('amount').value = this.dataset.amount;
            });
        });
    }

    // Declare OTP-related elements once at the top
    let sendOtpBtn = document.getElementById('send-otp-btn');
    let otpInput = document.getElementById('otp');
    let addMoneyBtn = document.getElementById('add-money-btn');
    let amountInput = document.getElementById('amount');

    // OTP logic for Add Money
    if (sendOtpBtn && otpInput && addMoneyBtn && amountInput) {
        sendOtpBtn.addEventListener('click', function() {
            const amount = parseFloat(amountInput.value);
            if (!validateAmount(amount)) {
                showAlert('Please enter a valid amount', 'danger');
                return;
            }
            fetch('/user/send_otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `phone_number=${encodeURIComponent(window.userPhoneNumber)}`
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('OTP sent to your phone', 'success');
                    otpInput.style.display = 'inline-block';
                    otpInput.value = '';
                    addMoneyBtn.disabled = false;
                } else {
                    showAlert(data.message || 'Failed to send OTP', 'danger');
                }
            })
            .catch(() => showAlert('Error sending OTP', 'danger'));
        });

        addMoneyBtn.addEventListener('click', function() {
            const amount = parseFloat(amountInput.value);
            const otp = otpInput.value.trim();
            if (!validateAmount(amount)) {
                showAlert('Please enter a valid amount', 'danger');
                return;
            }
            if (!otp) {
                showAlert('Please enter the OTP sent to your phone', 'danger');
                return;
            }
            addMoney(amount, otp);
        });
    }

    // Store user phone number for OTP (set from template)
    window.userPhoneNumber = window.userPhoneNumber || null;
});

// Export functions for global access
window.showAlert = showAlert;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.validatePhoneNumber = validatePhoneNumber;
window.validateAmount = validateAmount;
window.handleFileUpload = handleFileUpload;
window.addMoney = addMoney;
window.createPaymentRequest = createPaymentRequest;
window.simulatePalmScan = simulatePalmScan;
window.showUserInputForm = showUserInputForm;
window.processPayment = processPayment;
