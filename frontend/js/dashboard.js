// Dashboard functionality

function showDashboard() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;
    
    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-dashboard');
    }
    
    // Fetch user info first
    fetch('/api/user')
        .then(res => res.json())
        .then(userData => {
            const userName = userData.name || userData.email || 'User';
            renderDashboard(userName);
        })
        .catch(() => {
            renderDashboard('User');
        });
}

function renderDashboard(userName) {
    mainContent.innerHTML = `
        <div class="dashboard-header">
            <div class="welcome-section">
                <h1 class="welcome-title">Welcome, ${userName}! <span class="overview-badge">Overview</span></h1>
            </div>
            <div class="dashboard-tabs">
                <button class="tab-btn active" data-tab="overview">Overview</button>
                <button class="tab-btn" data-tab="insights">Insights</button>
            </div>
        </div>
        
        <div class="dashboard-stats">
            <div class="stat-card income-card">
                <div class="stat-header">
                    <h3>Income</h3>
                    <span class="stat-icon">➕</span>
                </div>
                <p class="stat-amount" id="stat-income">₹0.00</p>
                <p class="stat-upcoming">Upcoming: <span id="stat-income-upcoming">₹0.00</span></p>
            </div>
            <div class="stat-card expense-card">
                <div class="stat-header">
                    <h3>Spendings</h3>
                    <span class="stat-icon">➖</span>
                </div>
                <p class="stat-amount" id="stat-expense">₹0.00</p>
                <p class="stat-upcoming">Upcoming: <span id="stat-expense-upcoming">₹0.00</span></p>
            </div>
            <div class="stat-card balance-card">
                <div class="stat-header">
                    <h3>Balance</h3>
                    <span class="stat-icon">⚖️</span>
                </div>
                <p class="stat-amount" id="stat-balance">₹0.00</p>
                <p class="stat-upcoming">Estimated: <span id="stat-estimated">₹0.00</span></p>
            </div>
        </div>
        
        <div class="dashboard-main-grid">
            <div class="dashboard-left">
                <div class="card subscriptions-card">
                    <div class="card-header">
                        <h3>Your active financial goals</h3>
                        <button class="card-add-btn">➕</button>
                    </div>
                    <div id="subscriptions-list">
                        <p style="color: #888; text-align: center; padding: 20px;">No active goals yet. Create one in the Goals section.</p>
                    </div>
                </div>
                
                <div class="card chart-card pie-chart-card">
                    <div class="chart-header">
                        <h3>Categorized Spendings</h3>
                        <div class="chart-toggles">
                            <button class="toggle-btn active" data-period="month">May.</button>
                            <button class="toggle-btn" data-period="all">All</button>
                        </div>
                    </div>
                    <div class="pie-chart-container">
                        <canvas id="expenseChart" width="400" height="400"></canvas>
                        <div class="pie-chart-center" id="pie-chart-total">
                            <div class="center-label">Total</div>
                            <div class="center-amount">₹0.00</div>
                        </div>
                    </div>
                    <div style="padding: 20px; text-align: center; border-top: 1px solid #333;">
                        <button id="generate-report-btn" class="generate-report-btn" style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 8px;
                            font-size: 14px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: transform 0.2s, box-shadow 0.2s;
                            display: inline-flex;
                            align-items: center;
                            gap: 8px;
                        ">
                            📧 Generate & Email Report
                        </button>
                        <p id="report-status" style="margin-top: 10px; font-size: 12px; color: #888; display: none;"></p>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-right">
                <div class="card recent-transactions-card">
                    <div class="card-header">
                        <h3>What purchases did you make recently?</h3>
                        <button class="card-add-btn">➕</button>
                    </div>
                    <div id="recent-transactions"></div>
                </div>
            </div>
        </div>
    `;
    
    // Fetch and update stats
    fetch('/api/summary')
        .then(res => res.json())
        .then(data => {
            const incomeEl = document.getElementById('stat-income');
            const expenseEl = document.getElementById('stat-expense');
            const balanceEl = document.getElementById('stat-balance');
            const incomeUpcomingEl = document.getElementById('stat-income-upcoming');
            const expenseUpcomingEl = document.getElementById('stat-expense-upcoming');
            const estimatedEl = document.getElementById('stat-estimated');
            
            if (incomeEl) incomeEl.textContent = formatCurrency(data.income);
            if (expenseEl) expenseEl.textContent = formatCurrency(data.expense);
            const balance = data.savings;
            if (balanceEl) {
                balanceEl.textContent = formatCurrency(balance);
                balanceEl.parentElement.parentElement.classList.toggle('negative', balance < 0);
            }
            
            // Calculate upcoming amounts (for demo, using 10% of current)
            if (incomeUpcomingEl) incomeUpcomingEl.textContent = formatCurrency(data.income * 0.1);
            if (expenseUpcomingEl) expenseUpcomingEl.textContent = formatCurrency(data.expense * 0.1);

            // Use backend predictive model for estimated next-month balance/expenses
            fetch('/api/prediction')
                .then(res => res.json())
                .then(pred => {
                    if (estimatedEl && typeof pred.next_month_total === 'number') {
                        estimatedEl.textContent = formatCurrency(pred.next_month_total);
                        if (pred.next_month_label) {
                            estimatedEl.title = `Predicted expenses for ${pred.next_month_label}`;
                        }
                    }
                })
                .catch(() => {
                    // Fallback to simple heuristic if prediction fails
                    if (estimatedEl) {
                        estimatedEl.textContent = formatCurrency(balance * 1.02);
                    }
                });
        });
    
    // Fetch goals and surface them on the dashboard
    fetch('/api/goals')
        .then(res => res.json())
        .then(goals => {
            const subscriptionsList = document.getElementById('subscriptions-list');
            if (goals.length === 0) {
                subscriptionsList.innerHTML = '<p style="color: #888; text-align: center; padding: 20px;">No active goals yet. Create one in the Goals section.</p>';
            } else {
                const upcoming = goals.slice(0, 3).map(g => {
                    const deadlineDate = new Date(g.deadline);
                    const month = deadlineDate.toLocaleString('default', { month: '2-digit' });
                    const day = deadlineDate.toLocaleString('default', { day: '2-digit' });
                    const remaining = Math.max(g.target_amount - g.current_amount, 0);
                    return `
                        <div class="subscription-item">
                            <div class="subscription-info">
                                <strong>${g.name}</strong>
                                <span class="subscription-date">Target by ${day}.${month}</span>
                                <span class="subscription-tag">Goal</span>
                            </div>
                            <span class="subscription-amount">${formatCurrency(remaining)} left</span>
                        </div>
                    `;
                }).join('');
                subscriptionsList.innerHTML = upcoming;
            }
        });
    
    setTimeout(() => {
        renderExpenseChart();
    }, 200);
    fetchRecentTransactions();
    
    // Tab switching (Overview / Budget / Insights)
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab || 'overview';
            tabButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            updateDashboardTab(tab);
        });
    });
    // Initial state
    updateDashboardTab('overview');
    
    // Chart period toggle
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            renderExpenseChart();
        });
    });
    
    // Generate Report button
    const reportBtn = document.getElementById('generate-report-btn');
    const reportStatus = document.getElementById('report-status');
    if (reportBtn) {
        reportBtn.addEventListener('click', function() {
            reportBtn.disabled = true;
            reportBtn.style.opacity = '0.6';
            reportBtn.style.cursor = 'not-allowed';
            reportStatus.style.display = 'block';
            reportStatus.textContent = 'Generating report...';
            reportStatus.style.color = '#0984e3';
            
            // Get email from localStorage as fallback
            const userEmail = localStorage.getItem('user_email');
            
            fetch('/api/generate-report', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    email: userEmail || undefined
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    reportStatus.textContent = `Error: ${data.error}`;
                    reportStatus.style.color = '#e17055';
                } else {
                    reportStatus.textContent = `✅ Report sent successfully to ${data.email || 'your email'}!`;
                    reportStatus.style.color = '#00b894';
                }
                reportBtn.disabled = false;
                reportBtn.style.opacity = '1';
                reportBtn.style.cursor = 'pointer';
                
                // Hide status after 5 seconds
                setTimeout(() => {
                    reportStatus.style.display = 'none';
                }, 5000);
            })
            .catch(err => {
                reportStatus.textContent = `Error: ${err.message}`;
                reportStatus.style.color = '#e17055';
                reportBtn.disabled = false;
                reportBtn.style.opacity = '1';
                reportBtn.style.cursor = 'pointer';
            });
        });
        
        // Add hover effect
        reportBtn.addEventListener('mouseenter', function() {
            if (!reportBtn.disabled) {
                reportBtn.style.transform = 'translateY(-2px)';
                reportBtn.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
            }
        });
        reportBtn.addEventListener('mouseleave', function() {
            reportBtn.style.transform = 'translateY(0)';
            reportBtn.style.boxShadow = 'none';
        });
    }
}

// Simple tab behavior for Dashboard
function updateDashboardTab(tab) {
    const welcomeTitle = document.querySelector('.welcome-title');
    const subsCard = document.querySelector('.subscriptions-card');
    const pieCard = document.querySelector('.pie-chart-card');
    const recentCard = document.querySelector('.recent-transactions-card');
    const chartHeader = pieCard ? pieCard.querySelector('.chart-header h3') : null;
    const subsHeader = subsCard ? subsCard.querySelector('.card-header h3') : null;

    if (welcomeTitle) {
        if (tab === 'overview') {
            // Update with actual username if available
            fetch('/api/user')
                .then(res => res.json())
                .then(userData => {
                    const userName = userData.name || userData.email || 'User';
                    welcomeTitle.innerHTML = `Welcome, ${userName}! <span class="overview-badge">Overview</span>`;
                })
                .catch(() => {
                    welcomeTitle.innerHTML = 'Welcome, User! <span class="overview-badge">Overview</span>';
                });
        } else if (tab === 'insights') {
            welcomeTitle.innerHTML = 'Spending Insights <span class="overview-badge">Insights</span>';
        }
    }

    // Show / hide sections in a simple, intuitive way
    if (subsCard) {
        subsCard.style.display = (tab === 'overview') ? 'block' : 'none';
        if (subsHeader) {
            subsHeader.textContent = 'Your active financial goals';
        }
    }

    if (pieCard) {
        pieCard.style.display = (tab === 'overview' || tab === 'insights') ? 'block' : 'none';
        if (chartHeader) {
            chartHeader.textContent = tab === 'insights'
                ? 'Spending Breakdown & Patterns'
                : 'Categorized Spendings';
        }
    }

    if (recentCard) {
        // Keep recent transactions visible on Overview & Insights
        recentCard.style.display = (tab === 'overview' || tab === 'insights') ? 'block' : 'none';
    }
}

function fetchRecentTransactions() {
    fetch('/api/transactions')
        .then(res => res.json())
        .then(data => {
            const recent = data.sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 5);
            const container = document.getElementById('recent-transactions');
            if (!container) return;
            
            if (recent.length === 0) {
                container.innerHTML = '<p style="color: #888; text-align: center; padding: 20px;">No transactions yet.</p>';
                return;
            }
            const list = recent.map(t => {
                const dateParts = t.date.split('-');
                const displayDate = dateParts.length === 3 ? `${dateParts[2]}.${dateParts[1]}` : t.date;
                return `
                    <div class="transaction-item-new ${t.type}">
                        <span class="transaction-icon">📄</span>
                        <div class="transaction-info">
                            <strong>${t.category}</strong>
                            <div class="transaction-meta">
                                <span class="transaction-date">${displayDate}</span>
                                <span class="transaction-category-tag">${t.category}</span>
                            </div>
                        </div>
                        <span class="transaction-amount-new ${t.type}">${t.type === 'income' ? '+' : '-'}${formatCurrency(Math.abs(t.amount))}</span>
                    </div>
                `;
            }).join('');
            container.innerHTML = list;
        });
}


