// Analytics & Tools functionality (for irregular income earners and students)

function showAnalytics() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;
    
    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-analytics');
    }
    
    mainContent.innerHTML = `
        <div class="analytics-page">
            <div class="analytics-header">
                <h1>📊 Analytics & Tools</h1>
                <p>Powerful calculators and insights for irregular income earners and students</p>
            </div>
            
            <div class="analytics-grid">
                <!-- Spender Personality Test -->
                <div class="card analytics-card">
                    <h2>🎭 Spender Personality Test</h2>
                    <p>Discover your spending personality: Saver, Balanced, or Spender</p>
                    <button class="btn-primary" onclick="runPersonalityTest()">Run Test</button>
                    <div id="personality-result" style="margin-top: 20px; display: none;"></div>
                </div>
                
                <!-- Survival Days Calculator -->
                <div class="card analytics-card">
                    <h2>⏳ Survival Days Calculator</h2>
                    <p>Calculate how many days your current balance can last</p>
                    <button class="btn-primary" onclick="calculateSurvivalDays()">Calculate</button>
                    <div id="survival-result" style="margin-top: 20px; display: none;"></div>
                </div>
                
                <!-- Daily Target Calculator -->
                <div class="card analytics-card calculator-card">
                    <h2>🎯 Daily Target Calculator</h2>
                    <p>For irregular income earners: Calculate your daily earning target</p>
                    <form id="daily-target-form" class="calculator-form">
                        <div class="form-group">
                            <label>Monthly Expenses (₹)</label>
                            <input type="number" id="monthly-expenses" step="0.01" min="0" placeholder="10000" required>
                        </div>
                        <div class="form-group">
                            <label>Monthly Savings Goal (₹)</label>
                            <input type="number" id="savings-goal" step="0.01" min="0" placeholder="5000" value="0">
                        </div>
                        <div class="form-group">
                            <label>Working Days per Month</label>
                            <input type="number" id="working-days" min="1" max="31" value="20" required>
                        </div>
                        <button type="submit" class="btn-primary">Calculate Target</button>
                    </form>
                    <div id="daily-target-result" style="margin-top: 20px; display: none;"></div>
                </div>
                
                <!-- Smart Recommendations -->
                <div class="card analytics-card">
                    <h2>💡 Smart Recommendations</h2>
                    <p>Get personalized saving suggestions and expense control tips</p>
                    <button class="btn-primary" onclick="getRecommendations()">Get Recommendations</button>
                    <div id="recommendations-result" style="margin-top: 20px; display: none;"></div>
                </div>
            </div>
        </div>
    `;
    
    // Handle daily target form
    const form = document.getElementById('daily-target-form');
    form.onsubmit = function(e) {
        e.preventDefault();
        calculateDailyTarget();
    };
}

function runPersonalityTest() {
    const resultDiv = document.getElementById('personality-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Analyzing your spending patterns...</p>';
    
    fetch('/api/personality-test')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultDiv.innerHTML = `<p style="color: #e17055;">${data.error}</p>`;
                return;
            }
            
            const personalityColors = {
                'Saver': '#00b894',
                'Balanced': '#0984e3',
                'Spender': '#e17055'
            };
            
            const color = personalityColors[data.personality] || '#999';
            
            resultDiv.innerHTML = `
                <div class="personality-result" style="border-left: 4px solid ${color}; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 8px;">
                    <h3 style="color: ${color}; margin-top: 0;">Your Personality: ${data.personality}</h3>
                    <p><strong>Confidence:</strong> ${data.confidence}</p>
                    <p><strong>Savings Rate:</strong> ${data.savings_rate}%</p>
                    <p><strong>Total Income:</strong> ₹${data.total_income.toFixed(2)}</p>
                    <p><strong>Total Expense:</strong> ₹${data.total_expense.toFixed(2)}</p>
                    <div style="margin-top: 15px;">
                        <strong>Traits:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            ${data.traits.map(t => `<li>${t}</li>`).join('')}
                        </ul>
                    </div>
                    <div style="margin-top: 15px;">
                        <strong>Recommendations:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            ${data.recommendations.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        })
        .catch(err => {
            resultDiv.innerHTML = `<p style="color: #e17055;">Error: ${err.message}</p>`;
        });
}

function calculateSurvivalDays() {
    const resultDiv = document.getElementById('survival-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Calculating survival days...</p>';
    
    fetch('/api/survival-days')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultDiv.innerHTML = `<p style="color: #e17055;">${data.error}</p>`;
                return;
            }
            
            if (data.survival_days === null) {
                resultDiv.innerHTML = `
                    <div style="padding: 15px; background: rgba(0,0,0,0.2); border-radius: 8px;">
                        <p>${data.message}</p>
                        <p><strong>Current Balance:</strong> ₹${data.current_balance.toFixed(2)}</p>
                    </div>
                `;
                return;
            }
            
            const statusColors = {
                'critical': '#e17055',
                'warning': '#f39c12',
                'moderate': '#fdcb6e',
                'safe': '#00b894',
                'unknown': '#999'
            };
            
            const color = statusColors[data.status] || '#999';
            
            resultDiv.innerHTML = `
                <div class="survival-result" style="border-left: 4px solid ${color}; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 8px;">
                    <h3 style="color: ${color}; margin-top: 0;">${data.message}</h3>
                    <div style="font-size: 2em; font-weight: bold; color: ${color}; margin: 15px 0;">
                        ${data.survival_days} days
                    </div>
                    <p><strong>Current Balance:</strong> ₹${data.current_balance.toFixed(2)}</p>
                    <p><strong>Average Daily Expense:</strong> ₹${data.average_daily_expense.toFixed(2)}</p>
                    <p style="margin-top: 15px; font-size: 0.9em; color: #999;">
                        Based on your spending patterns from the last 30 days
                    </p>
                </div>
            `;
        })
        .catch(err => {
            resultDiv.innerHTML = `<p style="color: #e17055;">Error: ${err.message}</p>`;
        });
}

function calculateDailyTarget() {
    const monthlyExpenses = parseFloat(document.getElementById('monthly-expenses').value);
    const savingsGoal = parseFloat(document.getElementById('savings-goal').value) || 0;
    const workingDays = parseInt(document.getElementById('working-days').value);
    
    const resultDiv = document.getElementById('daily-target-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Calculating daily target...</p>';
    
    fetch('/api/daily-target', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            monthly_expenses: monthlyExpenses,
            savings_goal: savingsGoal,
            working_days: workingDays
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            resultDiv.innerHTML = `<p style="color: #e17055;">${data.error}</p>`;
            return;
        }
        
        resultDiv.innerHTML = `
            <div class="target-result" style="padding: 15px; background: rgba(0,0,0,0.2); border-radius: 8px; border-left: 4px solid #00b894;">
                <h3 style="color: #00b894; margin-top: 0;">Your Earning Targets</h3>
                <div style="font-size: 1.8em; font-weight: bold; color: #00b894; margin: 15px 0;">
                    ₹${data.daily_target.toFixed(2)} / day
                </div>
                <div style="margin: 15px 0;">
                    <p><strong>Weekly Target:</strong> ₹${data.weekly_target.toFixed(2)}</p>
                    <p><strong>Monthly Target:</strong> ₹${data.monthly_target.toFixed(2)}</p>
                    <p><strong>Total Needed:</strong> ₹${data.total_needed.toFixed(2)}</p>
                </div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #333;">
                    <p><strong>Breakdown per day:</strong></p>
                    <p>Expenses: ₹${data.breakdown.expenses_portion.toFixed(2)}</p>
                    <p>Savings: ₹${data.breakdown.savings_portion.toFixed(2)}</p>
                </div>
            </div>
        `;
    })
    .catch(err => {
        resultDiv.innerHTML = `<p style="color: #e17055;">Error: ${err.message}</p>`;
    });
}

function getRecommendations() {
    const resultDiv = document.getElementById('recommendations-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Generating recommendations...</p>';
    
    fetch('/api/recommendations')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultDiv.innerHTML = `<p style="color: #e17055;">${data.error}</p>`;
                return;
            }
            
            if (data.recommendations.length === 0) {
                resultDiv.innerHTML = '<p>No recommendations at this time. Keep tracking your expenses!</p>';
                return;
            }
            
            const typeColors = {
                'critical': '#e17055',
                'warning': '#f39c12',
                'info': '#0984e3',
                'tip': '#00b894'
            };
            
            const recommendationsList = data.recommendations.map(rec => {
                const color = typeColors[rec.type] || '#999';
                return `
                    <div class="recommendation-item" style="border-left: 4px solid ${color}; padding: 15px; margin: 10px 0; background: rgba(0,0,0,0.2); border-radius: 8px;">
                        <h4 style="color: ${color}; margin-top: 0;">${rec.title}</h4>
                        <p>${rec.message}</p>
                        <p style="margin-top: 10px; font-size: 0.9em; color: #999;"><strong>Action:</strong> ${rec.action}</p>
                    </div>
                `;
            }).join('');
            
            resultDiv.innerHTML = recommendationsList;
        })
        .catch(err => {
            resultDiv.innerHTML = `<p style="color: #e17055;">Error: ${err.message}</p>`;
        });
}






