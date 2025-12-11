// Merchant QR Payment Request functionality

function showMerchant() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;
    
    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-merchant');
    }
    
    mainContent.innerHTML = `
        <div class="merchant-page">
            <h1>💳 Merchant QR Payments</h1>
            <p style="color: #999; margin-bottom: 30px;">Generate dynamic UPI QR codes for payments</p>
            
            <div class="merchant-tabs">
                <button class="merchant-tab-btn active" data-tab="create">➕ Create Payment</button>
                <button class="merchant-tab-btn" data-tab="requests">📋 Payment Requests</button>
            </div>
            
            <div id="create-section" class="merchant-section active">
                <div class="card">
                    <h2>Create Payment Request</h2>
                    <form id="create-payment-form" class="payment-form">
                        <div class="form-group">
                            <label>Your UPI ID</label>
                            <input name="upi_id" type="text" placeholder="yourname@paytm" required>
                            <small>Enter your UPI ID (e.g., merchant@paytm, merchant@ybl)</small>
                        </div>
                        <div class="form-group">
                            <label>Amount (₹)</label>
                            <input name="amount" type="number" step="0.01" min="0.01" placeholder="100.00" required>
                        </div>
                    <div class="form-group">
                        <label>Description</label>
                        <input name="description" type="text" placeholder="Payment for services" required>
                    </div>
                    <div class="form-group">
                        <label>Payer Email (Optional - for testing)</label>
                        <input name="payer_email" type="email" placeholder="payer@example.com">
                        <small>Enter email to send dummy transaction notification (for testing)</small>
                    </div>
                    <button type="submit" class="btn-primary">Generate QR Code</button>
                    </form>
                </div>
                
                <div id="qr-display" class="card" style="display: none;">
                    <h2>Payment QR Code</h2>
                    <div id="qr-code-container" style="text-align: center; padding: 20px;">
                        <img id="qr-image" src="" alt="QR Code" style="max-width: 300px; border: 2px solid #00b894; border-radius: 10px;">
                    </div>
                    <div style="margin-top: 20px; text-align: center;">
                        <p><strong>Amount:</strong> ₹<span id="qr-amount"></span></p>
                        <p><strong>Description:</strong> <span id="qr-description"></span></p>
                        <p><strong>Status:</strong> <span id="qr-status" class="status-badge pending">PENDING</span></p>
                        <button id="copy-deeplink" class="btn-secondary" style="margin-top: 10px;">Copy Payment Link</button>
                        <button id="check-status" class="btn-secondary" style="margin-top: 10px;">Check Status</button>
                        <button id="simulate-payment" class="btn-primary" style="margin-top: 10px; background: linear-gradient(120deg, #00b894, #00cec9);">
                            📱 Simulate Payment (After Scanning)
                        </button>
                        <p id="simulate-status" style="margin-top: 10px; font-size: 0.9em; color: #999; display: none;"></p>
                    </div>
                </div>
            </div>
            
            <div id="requests-section" class="merchant-section">
                <div class="card">
                    <h2>Payment Requests</h2>
                    <div id="payment-requests-list"></div>
                </div>
            </div>
        </div>
    `;
    
    // Tab switching
    const tabButtons = document.querySelectorAll('.merchant-tab-btn');
    const sections = document.querySelectorAll('.merchant-section');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            
            tabButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            sections.forEach(s => s.classList.remove('active'));
            document.getElementById(`${tab}-section`).classList.add('active');
            
            if (tab === 'requests') {
                loadPaymentRequests();
            }
        });
    });
    
    // Create payment form
    document.getElementById('create-payment-form').onsubmit = async function(e) {
        e.preventDefault();
        const form = e.target;
        const formData = {
            upi_id: form.upi_id.value.trim(),
            amount: parseFloat(form.amount.value),
            description: form.description.value.trim(),
            payer_email: form.payer_email?.value.trim() || ''
        };
        
        try {
            const response = await fetch('/api/payment-requests', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create payment request');
            }
            
            const data = await response.json();
            
            // Display QR code
            document.getElementById('qr-image').src = data.qr_code;
            document.getElementById('qr-amount').textContent = data.amount.toFixed(2);
            document.getElementById('qr-description').textContent = data.description;
            document.getElementById('qr-status').textContent = data.status;
            document.getElementById('qr-display').style.display = 'block';
            
            // Store current payment request ID
            document.getElementById('qr-display').dataset.requestId = data.id;
            document.getElementById('qr-display').dataset.deeplink = data.deeplink;
            
            // Scroll to QR code
            document.getElementById('qr-display').scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            alert('Error: ' + error.message);
        }
    };
    
    // Copy deeplink
    document.getElementById('copy-deeplink')?.addEventListener('click', function() {
        const deeplink = document.getElementById('qr-display').dataset.deeplink;
        if (deeplink) {
            navigator.clipboard.writeText(deeplink).then(() => {
                alert('Payment link copied to clipboard!');
            });
        }
    });
    
    // Check status
    document.getElementById('check-status')?.addEventListener('click', async function() {
        const requestId = document.getElementById('qr-display').dataset.requestId;
        if (!requestId) return;
        
        try {
            const response = await fetch(`/api/payment-requests/${requestId}`);
            const data = await response.json();
            
            document.getElementById('qr-status').textContent = data.status;
            document.getElementById('qr-status').className = `status-badge ${data.status.toLowerCase()}`;
            
            if (data.status === 'PAID') {
                alert(`Payment received! Amount: ₹${data.amount.toFixed(2)}`);
            }
        } catch (error) {
            alert('Error checking status: ' + error.message);
        }
    });
    
    // Simulate payment button
    document.getElementById('simulate-payment')?.addEventListener('click', async function() {
        const requestId = document.getElementById('qr-display').dataset.requestId;
        if (!requestId) return;
        
        const btn = this;
        const statusMsg = document.getElementById('simulate-status');
        const originalText = btn.textContent;
        
        btn.disabled = true;
        btn.textContent = '⏳ Processing...';
        statusMsg.style.display = 'block';
        statusMsg.textContent = 'Sending transaction email...';
        statusMsg.style.color = '#00b894';
        
        try {
            const response = await fetch(`/api/payment-requests/${requestId}/simulate-payment`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (response.ok) {
                statusMsg.textContent = data.message;
                statusMsg.style.color = '#00b894';
                
                // Poll for status update
                let attempts = 0;
                const maxAttempts = 15; // Check for 15 seconds
                const checkInterval = setInterval(async () => {
                    attempts++;
                    try {
                        const statusResponse = await fetch(`/api/payment-requests/${requestId}`);
                        const statusData = await statusResponse.json();
                        
                        if (statusData.status === 'PAID') {
                            clearInterval(checkInterval);
                            document.getElementById('qr-status').textContent = 'PAID';
                            document.getElementById('qr-status').className = 'status-badge paid';
                            statusMsg.textContent = `✅ Payment detected and logged! Amount: ₹${statusData.amount.toFixed(2)}`;
                            statusMsg.style.color = '#00b894';
                            btn.disabled = false;
                            btn.textContent = originalText;
                            
                            // Refresh payment requests list if visible
                            if (typeof loadPaymentRequests === 'function') {
                                loadPaymentRequests();
                            }
                        } else if (attempts >= maxAttempts) {
                            clearInterval(checkInterval);
                            statusMsg.textContent = '⏳ Still processing... Check status manually or wait a bit longer.';
                            statusMsg.style.color = '#ffc107';
                            btn.disabled = false;
                            btn.textContent = originalText;
                        }
                    } catch (e) {
                        console.error('Error checking status:', e);
                    }
                }, 1000);
            } else {
                statusMsg.textContent = data.error || 'Error simulating payment';
                statusMsg.style.color = '#e17055';
                btn.disabled = false;
                btn.textContent = originalText;
            }
        } catch (error) {
            statusMsg.textContent = 'Error: ' + error.message;
            statusMsg.style.color = '#e17055';
            btn.disabled = false;
            btn.textContent = originalText;
        }
    });
}

async function loadPaymentRequests() {
    const listContainer = document.getElementById('payment-requests-list');
    if (!listContainer) return;
    
    try {
        const response = await fetch('/api/payment-requests');
        const requests = await response.json();
        
        if (requests.length === 0) {
            listContainer.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">No payment requests yet.</p>';
            return;
        }
        
        listContainer.innerHTML = requests.map(req => `
            <div class="payment-request-item">
                <div class="request-header">
                    <div>
                        <strong>₹${req.amount.toFixed(2)}</strong>
                        <span class="status-badge ${req.status.toLowerCase()}">${req.status}</span>
                    </div>
                    <small>${req.created_at}</small>
                </div>
                <div class="request-details">
                    <p><strong>Description:</strong> ${req.description || 'N/A'}</p>
                    <p><strong>UPI ID:</strong> ${req.upi_id}</p>
                    ${req.paid_at ? `<p><strong>Paid at:</strong> ${req.paid_at}</p>` : ''}
                    ${req.payer_email ? `<p><strong>Payer:</strong> ${req.payer_email}</p>` : ''}
                </div>
                ${req.status === 'PENDING' ? `
                    <div style="display: flex; gap: 10px; margin-top: 10px;">
                        <button class="btn-secondary check-status-btn" data-id="${req.id}">Check Status</button>
                        <button class="btn-primary simulate-payment-btn" data-id="${req.id}" style="background: linear-gradient(120deg, #00b894, #00cec9);">
                            📱 Simulate Payment
                        </button>
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        // Add event listeners for check status buttons
        listContainer.querySelectorAll('.check-status-btn').forEach(btn => {
            btn.addEventListener('click', async function() {
                const requestId = this.dataset.id;
                try {
                    const response = await fetch(`/api/payment-requests/${requestId}`);
                    const data = await response.json();
                    
                    if (data.status === 'PAID') {
                        alert(`Payment received! Amount: ₹${data.amount.toFixed(2)}`);
                        loadPaymentRequests(); // Refresh list
                    } else {
                        alert(`Status: ${data.status}`);
                    }
                } catch (error) {
                    alert('Error checking status: ' + error.message);
                }
            });
        });
        
        // Add event listeners for simulate payment buttons
        listContainer.querySelectorAll('.simulate-payment-btn').forEach(btn => {
            btn.addEventListener('click', async function() {
                const requestId = this.dataset.id;
                const originalText = this.textContent;
                
                this.disabled = true;
                this.textContent = '⏳ Processing...';
                
                try {
                    const response = await fetch(`/api/payment-requests/${requestId}/simulate-payment`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({})
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        alert(data.message);
                        
                        // Poll for status update
                        let attempts = 0;
                        const maxAttempts = 15;
                        const checkInterval = setInterval(async () => {
                            attempts++;
                            try {
                                const statusResponse = await fetch(`/api/payment-requests/${requestId}`);
                                const statusData = await statusResponse.json();
                                
                                if (statusData.status === 'PAID') {
                                    clearInterval(checkInterval);
                                    alert(`✅ Payment detected and logged! Amount: ₹${statusData.amount.toFixed(2)}`);
                                    loadPaymentRequests();
                                } else if (attempts >= maxAttempts) {
                                    clearInterval(checkInterval);
                                    alert('Still processing... Check status manually.');
                                }
                            } catch (e) {
                                console.error('Error checking status:', e);
                            }
                        }, 1000);
                    } else {
                        alert(data.error || 'Error simulating payment');
                        this.disabled = false;
                        this.textContent = originalText;
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                    this.disabled = false;
                    this.textContent = originalText;
                }
            });
        });
        
    } catch (error) {
        listContainer.innerHTML = '<p style="color: #ff6b6b;">Error loading payment requests.</p>';
    }
}

