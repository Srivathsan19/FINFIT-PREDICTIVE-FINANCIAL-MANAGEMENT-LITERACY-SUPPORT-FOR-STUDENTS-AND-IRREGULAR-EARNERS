// Login page functionality

let isRegisterMode = false;

function showLogin() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;
    
    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-login');
    }
    
    renderLoginPage();
}

function renderLoginPage() {
    mainContent.innerHTML = `
        <section class="login-page">
            <div class="card login-card">
                <h1 id="login-title">${isRegisterMode ? 'Create Account ✨' : 'Welcome back 👋'}</h1>
                <p class="login-subtext">${isRegisterMode ? 'Join FinFit to start your financial journey with AI-powered insights and smart budgeting tools.' : 'Access your personalized dashboard, stay on top of your spending, and sync goals across every device.'}</p>
                <form id="auth-form" class="login-form">
                    ${isRegisterMode ? `
                        <label for="auth-name">Full Name</label>
                        <input id="auth-name" type="text" placeholder="John Doe" required>
                    ` : ''}
                    <label for="auth-email">Email address</label>
                    <input id="auth-email" type="email" placeholder="you@example.com" required>
                    <label for="auth-password">Password</label>
                    <input id="auth-password" type="password" placeholder="••••••••" required minlength="6">
                    ${isRegisterMode ? `
                        <small style="color: #999; display: block; margin-top: -10px; margin-bottom: 15px;">Password must be at least 6 characters</small>
                    ` : ''}
                    ${!isRegisterMode ? `
                        <div class="remember-row">
                            <label><input type="checkbox" id="remember-me"> Keep me signed in</label>
                            <a class="forgot-link" href="#" onclick="alert('Password reset feature coming soon!'); return false;">Forgot password?</a>
                        </div>
                    ` : ''}
                    <button type="submit">${isRegisterMode ? 'Create Account' : 'Sign in securely'}</button>
                </form>
                <div class="login-divider"></div>
                <p class="login-subtext" style="text-align: center; margin-top: 20px;">
                    ${isRegisterMode ? 'Already have an account? ' : 'New here? '}
                    <a href="#" id="toggle-auth-mode" style="color: #00b894; text-decoration: underline; cursor: pointer;">
                        ${isRegisterMode ? 'Sign in' : 'Create an account'}
                    </a>
                </p>
                <p id="auth-feedback" class="login-subtext" style="display:none; margin-top: 15px;"></p>
            </div>
            <div class="card login-benefits">
                <span class="benefit-tag">Why FinFit?</span>
                <ul class="benefit-list">
                    <li>📊 Visual dashboards that make trends effortless to understand.</li>
                    <li>🎯 Goal tracking that nudges you when you're off pace.</li>
                    <li>🤖 AI-powered chatbot for personalized financial advice.</li>
                    <li>📈 Predictive analytics to forecast your expenses.</li>
                    <li>📧 Automated email reports with detailed insights.</li>
                    <li>🔒 Secure data storage with encrypted passwords.</li>
                </ul>
                <div class="login-divider"></div>
                <p class="login-subtext">${isRegisterMode ? 'Start tracking your finances today and take control of your financial future!' : 'Create an account to unlock AI-powered insights, guided budgeting, and collaborative goal planning.'}</p>
            </div>
        </section>
    `;
    
    // Setup form submission
    const form = document.getElementById('auth-form');
    const feedback = document.getElementById('auth-feedback');
    
    form.onsubmit = function(e) {
        e.preventDefault();
        handleAuth();
    };
    
    // Setup toggle mode
    document.getElementById('toggle-auth-mode').onclick = function(e) {
        e.preventDefault();
        isRegisterMode = !isRegisterMode;
        renderLoginPage();
    };
}

function handleAuth() {
    const form = document.getElementById('auth-form');
    const feedback = document.getElementById('auth-feedback');
    const email = document.getElementById('auth-email').value.trim();
    const password = document.getElementById('auth-password').value;
    const name = isRegisterMode ? document.getElementById('auth-name').value.trim() : null;
    
    // Validation
    if (isRegisterMode && !name) {
        feedback.style.display = 'block';
        feedback.textContent = 'Please enter your name';
        feedback.style.color = '#e17055';
        return;
    }
    
    if (!email || !password) {
        feedback.style.display = 'block';
        feedback.textContent = 'Please fill in all fields';
        feedback.style.color = '#e17055';
        return;
    }
    
    if (password.length < 6) {
        feedback.style.display = 'block';
        feedback.textContent = 'Password must be at least 6 characters';
        feedback.style.color = '#e17055';
        return;
    }
    
    feedback.style.display = 'block';
    feedback.textContent = isRegisterMode ? 'Creating account...' : 'Authenticating...';
    feedback.style.color = '#999';
    
    const endpoint = isRegisterMode ? '/api/register' : '/api/login';
    const payload = isRegisterMode 
        ? { email, password, name }
        : { email, password };
    
    fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            feedback.textContent = data.error;
            feedback.style.color = '#e17055';
        } else {
            feedback.textContent = isRegisterMode 
                ? 'Account created! Redirecting...' 
                : 'Login successful! Redirecting...';
            feedback.style.color = '#00b894';
            setTimeout(() => {
                // Update navigation UI
                if (typeof updateAuthUI === 'function') {
                    updateAuthUI();
                }
                if (typeof showDashboard === 'function') {
                    showDashboard();
                } else {
                    window.location.reload();
                }
            }, 1000);
        }
    })
    .catch(err => {
        feedback.textContent = 'An error occurred. Please try again.';
        feedback.style.color = '#e17055';
        console.error('Auth error:', err);
    });
}

