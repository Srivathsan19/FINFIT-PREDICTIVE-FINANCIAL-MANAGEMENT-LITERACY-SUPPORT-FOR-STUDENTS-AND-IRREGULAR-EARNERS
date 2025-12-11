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
            <h1>💳 Transactions</h1>
            <p style="color: #999; margin-bottom: 30px;">Track your income and expenses</p>
            
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
                    <h2>Transaction History</h2>
                    <div id="transactions-list"></div>
                </div>
            </div>
        </div>
    `;
    
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
            
            if (data.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">No transactions yet. Start adding income and expenses!</p>';
                return;
            }
            
            // Sort by date (newest first)
            const sorted = data.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            const list = sorted.map(t => {
                const isIncome = t.type === 'income';
                const color = isIncome ? '#00b894' : '#e17055';
                const icon = isIncome ? '➕' : '➖';
                const isAutoLogged = t.note && (t.note.includes('Auto-logged') || t.note.includes('from email'));
                
                return `
                    <div class="transaction-history-item" style="border-left: 4px solid ${color};">
                        <div class="transaction-history-content">
                            <div>
                                <strong>${icon} ${t.category}</strong>
                                ${isAutoLogged ? '<span style="font-size: 0.75em; background: rgba(0, 184, 148, 0.2); color: #00b894; padding: 2px 6px; border-radius: 4px; margin-left: 8px;">🤖 Auto</span>' : ''}
                                <div style="font-size: 0.9em; color: #999; margin-top: 5px;">
                                    ${t.date} ${t.note ? '• ' + t.note : ''}
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

