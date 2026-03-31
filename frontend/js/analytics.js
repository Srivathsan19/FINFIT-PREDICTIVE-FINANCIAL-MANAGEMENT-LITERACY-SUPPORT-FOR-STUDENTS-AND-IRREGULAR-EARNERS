// Analytics & Insights UI

function escapeHtml(str) {
    return String(str ?? '').replace(/[&<>"']/g, function (m) {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return map[m] || m;
    });
}

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
                <h1>Analytics & Insights</h1>
                <p>Real-time metrics, spending profile, need vs want, and expense forecasting.</p>
            </div>

            <div class="insights-inner">
                <div class="card insight-card">
                    <div class="insight-label">Expense Ratio</div>
                    <div class="stat-amount" id="insight-expense-ratio">-</div>
                    <div class="insight-meta" id="insight-expense-ratio-meta"></div>
                </div>

                <div class="card insight-card">
                    <div class="insight-label">Income Stability</div>
                    <div class="stat-amount" id="insight-income-stability">-</div>
                    <div class="insight-meta" id="insight-income-stability-meta"></div>
                </div>

                <div class="card insight-card">
                    <div class="insight-label">Dominant Category Share</div>
                    <div class="stat-amount" id="insight-dominant-category">-</div>
                    <div class="insight-meta" id="insight-dominant-category-meta"></div>
                </div>

                <div class="card insight-card">
                    <div class="insight-label">Daily Earning Target</div>
                    <div class="stat-amount" id="insight-daily-target">-</div>
                    <div class="insight-meta" id="insight-daily-target-meta"></div>
                </div>

                <div class="card insight-card">
                    <div class="insight-label">Spending Profile (K-Means)</div>
                    <div class="stat-amount" id="insight-spending-profile">-</div>
                    <div class="insight-meta" id="insight-spending-profile-meta"></div>
                </div>

                <div class="card insight-card">
                    <div class="insight-label">Needs vs Wants</div>
                    <div class="stat-amount" id="insight-need-want">-</div>
                    <div class="insight-meta" id="insight-need-want-meta"></div>
                </div>

                <div class="card insight-card">
                    <div class="insight-label">2-Month Expense Forecast</div>
                    <div class="stat-amount" id="insight-expense-forecast">-</div>
                    <div class="insight-meta" id="insight-expense-forecast-meta"></div>
                </div>
            </div>

            <div class="analytics-grid" style="margin-top:24px;">
                <div class="card analytics-card">
                    <h2>📌 Spender Personality Test</h2>
                    <p>Runs your personality classifier based on your spending + income.</p>
                    <button class="btn-primary" onclick="runPersonalityTest()">Run Test</button>
                    <div id="personality-result" style="margin-top:16px; display:none;"></div>
                </div>

                <div class="card analytics-card">
                    <h2>⏳ Survival Days Calculator</h2>
                    <p>Forecasts runway using your expense forecast.</p>
                    <button class="btn-primary" onclick="calculateSurvivalDays()">Calculate</button>
                    <div id="survival-result" style="margin-top:16px; display:none;"></div>
                </div>

                <div class="card analytics-card calculator-card">
                    <h2>🎯 Daily Target Calculator</h2>
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
                    <div id="daily-target-result" style="margin-top:16px; display:none;"></div>
                </div>

                <div class="card analytics-card">
                    <h2>💡 Smart Recommendations</h2>
                    <p>Personalized suggestions based on your recorded transactions.</p>
                    <button class="btn-primary" onclick="getRecommendations()">Get Recommendations</button>
                    <div id="recommendations-result" style="margin-top:16px; display:none;"></div>
                </div>
            </div>
        </div>
    `;

    // form handler
    const form = document.getElementById('daily-target-form');
    form.onsubmit = function (e) {
        e.preventDefault();
        calculateDailyTarget();
    };

    // insights loader
    loadInsights();
}

async function loadInsights() {
    try {
        const res1 = await fetch('/api/metrics/summary');
        const metrics = await res1.json();
        if (!metrics.error) {
            const er = metrics.expense_ratio;
            document.getElementById('insight-expense-ratio').textContent =
                (er == null ? '-' : `${(er * 100).toFixed(1)}%`);
            document.getElementById('insight-expense-ratio-meta').textContent =
                metrics.savings_rate_percent == null ? '' : `Savings rate: ${metrics.savings_rate_percent.toFixed(1)}%`;

            const stability = metrics.income_stability_score;
            document.getElementById('insight-income-stability').textContent =
                stability == null ? '-' : `${(stability * 100).toFixed(0)}%`;
            document.getElementById('insight-income-stability-meta').textContent =
                metrics.income_variability_index == null ? '' : `Variability index: ${metrics.income_variability_index.toFixed(2)}`;

            const domShare = metrics.dominant_category_share;
            const domCat = metrics.dominant_category;
            document.getElementById('insight-dominant-category').textContent =
                domShare == null ? '-' : `${(domShare * 100).toFixed(1)}%`;
            document.getElementById('insight-dominant-category-meta').textContent =
                domCat ? `Top category: ${domCat}` : '';

            const dailyTarget =
                metrics.daily_earning_target_with_savings != null
                    ? metrics.daily_earning_target_with_savings
                    : metrics.daily_earning_target_expense_only;
            document.getElementById('insight-daily-target').textContent =
                dailyTarget == null ? '-' : `₹${Number(dailyTarget).toFixed(2)}/day`;
            document.getElementById('insight-daily-target-meta').textContent =
                metrics.daily_earning_target_with_savings != null ? 'Including savings goal' : 'Based on expenses only';
        }
    } catch (e) {
        // ignore, UI still usable
    }

    try {
        const res2 = await fetch('/api/classification/spending-behavior-kmeans');
        const kmeans = await res2.json();
        if (!kmeans.error) {
            document.getElementById('insight-spending-profile').textContent = escapeHtml(kmeans.behavior || '-');
            document.getElementById('insight-spending-profile-meta').textContent =
                kmeans.confidence != null ? `Confidence: ${Number(kmeans.confidence).toFixed(2)}` : '';
        }
    } catch (e) {}

    try {
        const res3 = await fetch('/api/classification/need-want');
        const nw = await res3.json();
        if (!nw.error) {
            const need = nw.need_ratio == null ? null : nw.need_ratio;
            const want = nw.want_ratio == null ? null : nw.want_ratio;
            document.getElementById('insight-need-want').textContent =
                need == null ? '-' : `${(need * 100).toFixed(0)}% needs / ${(want * 100).toFixed(0)}% wants`;
            document.getElementById('insight-need-want-meta').textContent =
                `Unclassified: ${nw.unclassified_count ?? 0}`;
        }
    } catch (e) {}

    try {
        const res4 = await fetch('/api/forecast/expense-2mo');
        const fc = await res4.json();
        if (!fc.error) {
            const amt = fc.forecasted_amount;
            document.getElementById('insight-expense-forecast').textContent =
                amt == null ? '-' : `₹${Number(amt).toFixed(2)}`;
            const conf = fc.confidence_level ? ` (${escapeHtml(fc.confidence_level)} confidence)` : '';
            document.getElementById('insight-expense-forecast-meta').textContent =
                `${conf} • Months used: ${fc.data_months_used ?? 0}`;
        }
    } catch (e) {}
}

function runPersonalityTest() {
    const resultDiv = document.getElementById('personality-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Analyzing your spending patterns...</p>';

    fetch('/api/personality-test')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultDiv.innerHTML = `<p style="color:#e17055;">${escapeHtml(data.error)}</p>`;
                return;
            }
            resultDiv.innerHTML = `
                <div style="padding:16px; border-left:4px solid #d4af37; background:rgba(0,0,0,0.2); border-radius:8px;">
                    <h3 style="margin-top:0; color:#d4af37;">Your Personality: ${escapeHtml(data.personality)}</h3>
                    <p><strong>Confidence:</strong> ${escapeHtml(data.confidence)}</p>
                    <p><strong>Savings Rate:</strong> ${escapeHtml(data.savings_rate)}%</p>
                    <p><strong>Total Income:</strong> ₹${Number(data.total_income || 0).toFixed(2)}</p>
                    <p><strong>Total Expense:</strong> ₹${Number(data.total_expense || 0).toFixed(2)}</p>
                </div>
            `;
        })
        .catch(err => {
            resultDiv.innerHTML = `<p style="color:#e17055;">Error: ${escapeHtml(err.message)}</p>`;
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
                resultDiv.innerHTML = `<p style="color:#e17055;">${escapeHtml(data.error)}</p>`;
                return;
            }
            if (data.survival_days === null || data.survival_days === undefined) {
                resultDiv.innerHTML = `<div style="padding:15px; background:rgba(0,0,0,0.2); border-radius:8px;"><p>${escapeHtml(data.message || 'No data')}</p></div>`;
                return;
            }

            resultDiv.innerHTML = `
                <div style="padding:16px; border-left:4px solid #d4af37; background:rgba(0,0,0,0.2); border-radius:8px;">
                    <h3 style="margin-top:0; color:#d4af37;">${escapeHtml(data.message || 'Survival estimate')}</h3>
                    <div style="font-size:2em; font-weight:bold; color:#d4af37; margin:12px 0;">
                        ${escapeHtml(data.survival_days)} days
                    </div>
                    <p><strong>Current Balance:</strong> ₹${Number(data.current_balance || 0).toFixed(2)}</p>
                </div>
            `;
        })
        .catch(err => {
            resultDiv.innerHTML = `<p style="color:#e17055;">Error: ${escapeHtml(err.message)}</p>`;
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            monthly_expenses: monthlyExpenses,
            savings_goal: savingsGoal,
            working_days: workingDays
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultDiv.innerHTML = `<p style="color:#e17055;">${escapeHtml(data.error)}</p>`;
                return;
            }
            resultDiv.innerHTML = `
                <div style="padding:15px; background:rgba(0,0,0,0.2); border-radius:8px; border-left:4px solid #d4af37;">
                    <h3 style="margin-top:0; color:#d4af37;">Your Earning Targets</h3>
                    <div style="font-size:1.8em; font-weight:bold; color:#d4af37; margin:12px 0;">
                        ₹${Number(data.daily_target || 0).toFixed(2)} / day
                    </div>
                    <p><strong>Weekly Target:</strong> ₹${Number(data.weekly_target || 0).toFixed(2)}</p>
                    <p><strong>Monthly Target:</strong> ₹${Number(data.monthly_target || 0).toFixed(2)}</p>
                    <p><strong>Total Needed:</strong> ₹${Number(data.total_needed || 0).toFixed(2)}</p>
                </div>
            `;
        })
        .catch(err => {
            resultDiv.innerHTML = `<p style="color:#e17055;">Error: ${escapeHtml(err.message)}</p>`;
        });
}

function getRecommendations() {
    const resultDiv = document.getElementById('recommendations-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p>Loading smart recommendations...</p>';

    fetch('/api/recommendations')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultDiv.innerHTML = `<p style="color:#e17055;">${escapeHtml(data.error)}</p>`;
                return;
            }

            const recs = data.recommendations || [];
            if (!recs.length) {
                resultDiv.innerHTML = `<p style="color:#999;">No recommendations right now.</p>`;
                return;
            }

            resultDiv.innerHTML = `
                <div style="padding:16px; background:rgba(0,0,0,0.2); border-radius:8px; border-left:4px solid #d4af37;">
                    <h3 style="margin-top:0; color:#d4af37;">Recommendations</h3>
                    <ul style="padding-left:18px; margin:8px 0;">
                        ${recs.map(r => `<li><strong>${escapeHtml(r.title || r.type || '')}:</strong> ${escapeHtml(r.message || r.action || '')}</li>`).join('')}
                    </ul>
                </div>
            `;
        })
        .catch(err => {
            resultDiv.innerHTML = `<p style="color:#e17055;">Error: ${escapeHtml(err.message)}</p>`;
        });
}

