// Goals functionality

function showGoals() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;
    
    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-goals');
    }
    mainContent.innerHTML = `
        <h1>Financial Goals</h1>
        <div class="card">
            <h3>Create New Goal</h3>
            <form id="add-goal-form" class="goal-form">
                <input name="name" placeholder="Goal Name (e.g., Vacation, Emergency Fund)" required>
                <input name="target_amount" type="number" step="0.01" placeholder="Target Amount (₹)" required>
                <input name="deadline" type="date" required>
                <button type="submit">Add Goal</button>
            </form>
        </div>
        <div id="goals-list"></div>
    `;
    fetchGoals();
    document.getElementById('add-goal-form').onsubmit = function(e) {
        e.preventDefault();
        const form = e.target;
        fetch('/api/goals', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: form.name.value,
                target_amount: parseFloat(form.target_amount.value),
                deadline: form.deadline.value
            })
        }).then(() => {
            fetchGoals();
            form.reset();
        });
    };
}

function fetchGoals() {
    fetch('/api/goals')
        .then(res => res.json())
        .then(data => {
            if (data.length === 0) {
                document.getElementById('goals-list').innerHTML = `
                    <div class="card">
                        <p style="text-align: center; color: #888;">No goals yet. Create your first financial goal above!</p>
                    </div>
                `;
                return;
            }
            const list = data.map(g => {
                const progress = (g.current_amount / g.target_amount) * 100;
                const progressPercent = Math.min(progress, 100).toFixed(1);
                const daysLeft = Math.ceil((new Date(g.deadline) - new Date()) / (1000 * 60 * 60 * 24));
                const isOverdue = daysLeft < 0;
                const remaining = g.target_amount - g.current_amount;
                
                return `
                    <div class="card goal-card">
                        <div class="goal-header">
                            <h3>${g.name}</h3>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span class="goal-deadline ${isOverdue ? 'overdue' : ''}">
                                    ${isOverdue ? '⚠️ Overdue' : `📅 ${daysLeft} days left`}
                                </span>
                                <button onclick="deleteGoal(${g.id})" class="delete-goal-btn" title="Delete goal">🗑️</button>
                            </div>
                        </div>
                        <div class="goal-progress">
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${progressPercent}%"></div>
                            </div>
                            <div class="progress-text">
                                <span>${formatCurrency(g.current_amount)} / ${formatCurrency(g.target_amount)}</span>
                                <span class="progress-percent">${progressPercent}%</span>
                            </div>
                        </div>
                        <div class="goal-details">
                            <p><strong>Remaining:</strong> ${formatCurrency(remaining)}</p>
                            <p><strong>Deadline:</strong> ${g.deadline}</p>
                        </div>
                        <div class="goal-actions">
                            <input type="number" step="0.01" id="update-${g.id}" placeholder="Add amount" class="update-input">
                            <button onclick="updateGoal(${g.id})" class="update-btn">Update Progress</button>
                        </div>
                    </div>
                `;
            }).join('');
            document.getElementById('goals-list').innerHTML = list;
        });
}

window.updateGoal = function(id) {
    const input = document.getElementById(`update-${id}`);
    const amount = parseFloat(input.value);
    if (!amount || amount <= 0) {
        alert('Please enter a valid amount');
        return;
    }
    fetch(`/api/goals/${id}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({amount: amount})
    }).then(() => {
        fetchGoals();
        input.value = '';
        // Refresh dashboard if it's visible
        if (mainContent.querySelector('.dashboard-stats')) {
            showDashboard();
        }
    });
};

window.deleteGoal = function(id) {
    if (confirm('Are you sure you want to delete this goal? This action cannot be undone.')) {
        fetch(`/api/goals/${id}`, {
            method: 'DELETE'
        }).then(() => {
            fetchGoals();
            // Refresh dashboard if it's visible
            if (mainContent.querySelector('.dashboard-stats')) {
                showDashboard();
            }
        });
    }
};

