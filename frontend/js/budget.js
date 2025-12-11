// Budget Planner functionality

function showBudget() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;
    
    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-budget');
    }
    
    mainContent.innerHTML = `
        <div class="budget-page">
            <div class="budget-header">
                <h1>💰 Budget Planner</h1>
                <p>Set monthly budgets for categories and track your spending</p>
            </div>
            
            <div class="budget-content">
                <div class="card budget-form-card">
                    <h2>Create New Budget</h2>
                    <form id="budget-form" class="budget-form">
                        <div class="form-group">
                            <label for="budget-category">Category</label>
                            <input type="text" id="budget-category" placeholder="e.g., Food, Transport, Entertainment" required>
                        </div>
                        <div class="form-group">
                            <label for="budget-amount">Monthly Budget Amount (₹)</label>
                            <input type="number" id="budget-amount" step="0.01" min="0" placeholder="5000" required>
                        </div>
                        <div class="form-group">
                            <label for="budget-period">Period</label>
                            <select id="budget-period">
                                <option value="monthly">Monthly</option>
                                <option value="weekly">Weekly</option>
                                <option value="daily">Daily</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="alert-threshold">Alert Threshold (%)</label>
                            <input type="number" id="alert-threshold" step="1" min="0" max="100" value="80" required>
                            <small>Get alerted when you reach this percentage of your budget</small>
                        </div>
                        <button type="submit" class="btn-primary">➕ Create Budget</button>
                        <p id="budget-feedback" class="feedback-message" style="display:none;"></p>
                    </form>
                </div>
                
                <div class="card budget-list-card">
                    <h2>Your Budgets</h2>
                    <div id="budgets-list">
                        <p style="text-align: center; color: #888; padding: 20px;">Loading budgets...</p>
                    </div>
                </div>
                
                <div class="card budget-alerts-card">
                    <h2>⚠️ Budget Alerts</h2>
                    <div id="budget-alerts">
                        <p style="text-align: center; color: #888; padding: 20px;">Loading alerts...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Handle form submission
    const form = document.getElementById('budget-form');
    const feedback = document.getElementById('budget-feedback');
    
    form.onsubmit = function(e) {
        e.preventDefault();
        const category = document.getElementById('budget-category').value.trim();
        const amount = parseFloat(document.getElementById('budget-amount').value);
        const period = document.getElementById('budget-period').value;
        const threshold = parseFloat(document.getElementById('alert-threshold').value) / 100;
        
        feedback.style.display = 'block';
        feedback.textContent = 'Creating budget...';
        feedback.style.color = '#999';
        
        fetch('/api/budgets', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                category: category,
                budget_amount: amount,
                period: period,
                alert_threshold: threshold
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                feedback.textContent = data.error;
                feedback.style.color = '#e17055';
            } else {
                feedback.textContent = 'Budget created successfully!';
                feedback.style.color = '#00b894';
                form.reset();
                fetchBudgets();
                fetchAlerts();
            }
        })
        .catch(err => {
            feedback.textContent = 'Error creating budget. Please try again.';
            feedback.style.color = '#e17055';
        });
    };
    
    fetchBudgets();
    fetchAlerts();
}

function fetchBudgets() {
    fetch('/api/budgets')
        .then(res => res.json())
        .then(budgets => {
            const container = document.getElementById('budgets-list');
            if (!container) return;
            
            if (budgets.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">No budgets created yet. Create one above!</p>';
                return;
            }
            
            const list = budgets.map(budget => {
                const percentage = budget.percentage || 0;
                const progressColor = percentage >= 100 ? '#e17055' : 
                                     percentage >= 80 ? '#f39c12' : '#00b894';
                
                return `
                    <div class="budget-item ${budget.alert ? 'alert' : ''}">
                        <div class="budget-item-header">
                            <div>
                                <h3>${budget.category}</h3>
                                <small>${budget.period} budget</small>
                            </div>
                            <button class="delete-budget-btn" onclick="deleteBudget(${budget.id})" title="Delete budget">🗑️</button>
                        </div>
                        <div class="budget-progress">
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(100, percentage)}%; background: ${progressColor};"></div>
                            </div>
                            <div class="budget-stats">
                                <span>₹${budget.spent.toFixed(2)} / ₹${budget.budget_amount.toFixed(2)}</span>
                                <span style="color: ${progressColor}; font-weight: 600;">${percentage.toFixed(1)}%</span>
                            </div>
                        </div>
                        <div class="budget-remaining">
                            <span>Remaining: ₹${budget.remaining.toFixed(2)}</span>
                            ${budget.alert ? '<span style="color: #e17055;">⚠️ Budget Alert!</span>' : ''}
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = list;
        })
        .catch(err => {
            const container = document.getElementById('budgets-list');
            if (container) {
                container.innerHTML = '<p style="text-align: center; color: #e17055; padding: 20px;">Error loading budgets. Please try again.</p>';
            }
        });
}

function fetchAlerts() {
    fetch('/api/budgets/alerts')
        .then(res => res.json())
        .then(alerts => {
            const container = document.getElementById('budget-alerts');
            if (!container) return;
            
            if (alerts.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #00b894; padding: 20px;">✅ No budget alerts. You\'re doing great!</p>';
                return;
            }
            
            const alertsList = alerts.map(alert => `
                <div class="alert-item">
                    <div class="alert-icon">⚠️</div>
                    <div class="alert-content">
                        <strong>${alert.category}</strong>
                        <p>${alert.message}</p>
                        <small>Spent: ₹${alert.spent.toFixed(2)} / Budget: ₹${alert.budget_amount.toFixed(2)} (${alert.percentage.toFixed(1)}%)</small>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = alertsList;
        })
        .catch(err => {
            const container = document.getElementById('budget-alerts');
            if (container) {
                container.innerHTML = '<p style="text-align: center; color: #e17055; padding: 20px;">Error loading alerts.</p>';
            }
        });
}

window.deleteBudget = function(id) {
    if (confirm('Are you sure you want to delete this budget?')) {
        fetch(`/api/budgets/${id}`, {method: 'DELETE'})
            .then(res => res.json())
            .then(() => {
                fetchBudgets();
                fetchAlerts();
            })
            .catch(err => {
                alert('Error deleting budget. Please try again.');
            });
    }
};






