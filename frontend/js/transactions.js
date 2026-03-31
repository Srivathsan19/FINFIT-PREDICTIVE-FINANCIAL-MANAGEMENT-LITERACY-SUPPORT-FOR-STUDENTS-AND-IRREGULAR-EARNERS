// Transactions functionality

function showTransactions() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;
    
    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-transactions');
    }
    mainContent.innerHTML = `
        <div class="transactions-page">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                    <h1 style="margin: 0;">💳 Transactions</h1>
                    <p style="color: #999; margin-top: 5px;">Track your income and expenses</p>
                </div>
                <button id="sync-transactions-btn" class="btn-primary" style="
                    background: linear-gradient(120deg, #00b894, #00cec9);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    cursor: pointer;
                    box-shadow: 0 2px 8px rgba(0, 184, 148, 0.3);
                ">
                    <span id="sync-icon">🔄</span>
                    <span id="sync-text">Sync from Email</span>
                </button>
            </div>
            <div id="sync-status" style="display: none; margin-bottom: 15px; padding: 12px; border-radius: 8px; font-size: 0.9em;"></div>
            
            <div class="transactions-tabs">
                <button class="transaction-tab-btn active" data-tab="add-income">➕ Add Income</button>
                <button class="transaction-tab-btn" data-tab="add-expense">➖ Add Expense</button>
                <button class="transaction-tab-btn" data-tab="history">📜 View History</button>
            </div>
            
            <div id="add-income-section" class="transaction-section active">
                <div class="card">
                    <h2>Add Income</h2>
                    <form id="add-income-form" class="transaction-form">
                        <input name="category" placeholder="Income Source (e.g., Freelance, Part-time, Gig)" required>
                        <input name="amount" type="number" step="0.01" placeholder="Amount (₹)" required>
                        <input name="date" type="date" required>
                        <input name="note" placeholder="Note (optional)">
                        <button type="submit" class="btn-primary">Add Income</button>
                    </form>
                </div>
            </div>
            
            <div id="add-expense-section" class="transaction-section">
                <div class="card">
                    <h2>Add Expense</h2>
                    <form id="add-expense-form" class="transaction-form">
                        <input name="category" placeholder="Category (e.g., Food, Transport, Rent)" required>
                        <input name="amount" type="number" step="0.01" placeholder="Amount (₹)" required>
                        <input name="date" type="date" required>
                        <input name="note" placeholder="Note (optional)">
                        <button type="submit" class="btn-primary">Add Expense</button>
                    </form>
                </div>
            </div>
            
            <div id="history-section" class="transaction-section">
                <div class="card">
                    <h2 style="margin: 0 0 20px 0;">Transaction History</h2>
                    <div id="transactions-list"></div>
                </div>
            </div>
        </div>
    `;
    
    // Wire up sync button
    const syncBtn = document.getElementById('sync-transactions-btn');
    const syncStatus = document.getElementById('sync-status');
    const syncIcon = document.getElementById('sync-icon');
    const syncText = document.getElementById('sync-text');
    
    if (syncBtn) {
        syncBtn.addEventListener('click', async function() {
            if (syncBtn.disabled) return;
            
            // Disable button and show loading
            syncBtn.disabled = true;
            syncIcon.textContent = '⏳';
            syncText.textContent = 'Syncing...';
            syncStatus.style.display = 'block';
            syncStatus.style.background = 'rgba(0, 184, 148, 0.1)';
            syncStatus.style.color = '#00b894';
            syncStatus.style.border = '1px solid #00b894';
            syncStatus.textContent = '🔄 Syncing transactions from your email...';
            
            try {
                const response = await fetch('/api/gmail/sync', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    syncStatus.style.background = 'rgba(0, 184, 148, 0.1)';
                    syncStatus.style.color = '#00b894';
                    syncStatus.style.border = '1px solid #00b894';
                    syncStatus.innerHTML = `✅ ${data.message || 'Sync started successfully!'}<br><small>${data.note || 'Please wait a few seconds and refresh the list.'}</small>`;
                    
                    // Wait a bit then refresh transactions
                    setTimeout(() => {
                        fetchTransactions();
                        // Refresh dashboard if visible
                        if (mainContent && mainContent.querySelector('.dashboard-stats') && typeof showDashboard === 'function') {
                            showDashboard();
                        }
                    }, 3000);
                    
                    // Re-enable button after a delay
                    setTimeout(() => {
                        syncBtn.disabled = false;
                        syncIcon.textContent = '🔄';
                        syncText.textContent = 'Sync from Email';
                        setTimeout(() => {
                            syncStatus.style.display = 'none';
                        }, 5000);
                    }, 3000);
                } else {
                    syncStatus.style.background = 'rgba(225, 112, 85, 0.1)';
                    syncStatus.style.color = '#e17055';
                    syncStatus.style.border = '1px solid #e17055';
                    syncStatus.textContent = `❌ ${data.error || 'Sync failed. Please try again.'}`;
                    
                    syncBtn.disabled = false;
                    syncIcon.textContent = '🔄';
                    syncText.textContent = 'Sync from Email';
                }
            } catch (error) {
                console.error('Sync error:', error);
                syncStatus.style.background = 'rgba(225, 112, 85, 0.1)';
                syncStatus.style.color = '#e17055';
                syncStatus.style.border = '1px solid #e17055';
                syncStatus.textContent = '❌ Error syncing transactions. Please check your Gmail connection.';
                
                syncBtn.disabled = false;
                syncIcon.textContent = '🔄';
                syncText.textContent = 'Sync from Email';
            }
        });
    }
    
    // Tab switching
    const tabButtons = document.querySelectorAll('.transaction-tab-btn');
    const sections = document.querySelectorAll('.transaction-section');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            
            // Update buttons
            tabButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update sections
            sections.forEach(s => s.classList.remove('active'));
            document.getElementById(`${tab}-section`).classList.add('active');
            
            // Load history if needed
            if (tab === 'history') {
                fetchTransactions();
            }
        });
    });
    
    // Income form
    document.getElementById('add-income-form').onsubmit = function(e) {
        e.preventDefault();
        const form = e.target;
        fetch('/api/transactions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                type: 'income',
                category: form.category.value,
                amount: parseFloat(form.amount.value),
                date: form.date.value,
                note: form.note.value
            })
        }).then(() => {
            form.reset();
            if (typeof showDashboard === 'function') showDashboard();
            alert('Income added successfully!');
        });
    };
    
    // Expense form
    document.getElementById('add-expense-form').onsubmit = function(e) {
        e.preventDefault();
        const form = e.target;
        fetch('/api/transactions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                type: 'expense',
                category: form.category.value,
                amount: parseFloat(form.amount.value),
                date: form.date.value,
                note: form.note.value
            })
        }).then(() => {
            form.reset();
            if (typeof showDashboard === 'function') showDashboard();
            alert('Expense added successfully!');
        });
    };
    fetchTransactions();
    document.getElementById('add-transaction-form').onsubmit = function(e) {
        e.preventDefault();
        const form = e.target;
        fetch('/api/transactions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                type: form.type.value,
                category: form.category.value,
                amount: parseFloat(form.amount.value),
                date: form.date.value,
                note: form.note.value
            })
        }).then(() => {
            fetchTransactions();
            form.reset();
            // Refresh dashboard if it's visible
            if (mainContent.querySelector('.dashboard-stats')) {
                showDashboard();
            }
        });
    };
}

function fetchTransactions() {
    fetch('/api/transactions')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('transactions-list');
            if (!container) return;
            
            // Debug: Log all transactions
            console.log('All transactions:', data);
            const incomeCount = data.filter(t => t.type === 'income').length;
            const expenseCount = data.filter(t => t.type === 'expense').length;
            console.log(`Income: ${incomeCount}, Expenses: ${expenseCount}`);
            
            if (data.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">No transactions yet. Start adding income and expenses!</p>';
                return;
            }
            
            // Sort by date (newest first), then by ID (higher ID = newer) to ensure most recent at top
            const sorted = data.sort((a, b) => {
                const dateA = new Date(a.date);
                const dateB = new Date(b.date);
                // First sort by date (newest first)
                if (dateB - dateA !== 0) {
                    return dateB - dateA;
                }
                // If dates are same, sort by ID (higher ID = newer transaction)
                return (b.id || 0) - (a.id || 0);
            });
            
            // Filter out any null/undefined transactions and ensure we show ALL transactions
            const validTransactions = sorted.filter(t => t && t.type && t.amount);
            
            if (validTransactions.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">No valid transactions found.</p>';
                return;
            }
            
            const list = validTransactions.map(t => {
                const isIncome = t.type === 'income';
                const color = isIncome ? '#00b894' : '#e17055';
                const icon = isIncome ? '➕' : '➖';
                const isAutoLogged = t.note && (t.note.includes('Auto-logged') || t.note.includes('from email') || t.note.includes('Synced from email'));
                
                // Debug log for income transactions
                if (isIncome) {
                    console.log('Rendering income transaction:', t);
                }
                
                return `
                    <div class="transaction-history-item" style="border-left: 4px solid ${color};">
                        <div class="transaction-history-content">
                            <div>
                                <strong>${icon} ${t.category || 'Unknown'}</strong>
                                ${isAutoLogged ? '<span style="font-size: 0.75em; background: rgba(0, 184, 148, 0.2); color: #00b894; padding: 2px 6px; border-radius: 4px; margin-left: 8px;">🤖 Auto</span>' : ''}
                                <div style="font-size: 0.9em; color: #999; margin-top: 5px;">
                                    ${t.date} ${t.note ? '• ' + t.note.substring(0, 50) : ''}
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.2em; font-weight: bold; color: ${color};">
                                    ${isIncome ? '+' : '-'}${formatCurrency(t.amount)}
                                </div>
                                <button onclick="deleteTransaction(${t.id})" style="
                                    margin-top: 5px;
                                    background: transparent;
                                    border: 1px solid #e17055;
                                    color: #e17055;
                                    padding: 4px 8px;
                                    border-radius: 4px;
                                    cursor: pointer;
                                    font-size: 0.8em;
                                ">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = list;
            
            // Debug: Log what was rendered
            console.log(`Rendered ${validTransactions.length} transactions (${incomeCount} income, ${expenseCount} expenses)`);
        })
        .catch(err => {
            const container = document.getElementById('transactions-list');
            if (container) {
                container.innerHTML = '<p style="text-align: center; color: #e17055; padding: 20px;">Error loading transactions.</p>';
            }
        });
}

window.deleteTransaction = function(id) {
    if (confirm('Are you sure you want to delete this transaction?')) {
        fetch('/api/transactions/' + id, {method: 'DELETE'})
            .then(() => {
                fetchTransactions();
                // Refresh dashboard if it's visible
                if (mainContent.querySelector('.dashboard-stats')) {
                    showDashboard();
                }
            });
    }
};

