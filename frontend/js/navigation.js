// Navigation and theme management

// Global reference to main content area (will be initialized when DOM is ready)
var mainContent = null;

function setActiveNav(activeId) {
    document.querySelectorAll('.nav-link').forEach(btn => {
        btn.classList.toggle('active', btn.id === activeId);
    });
}

// Initialize navigation when DOM is ready
function initNavigation() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    
    // Theme toggle
    const themeToggle = document.getElementById('toggle-theme');
    if (themeToggle) {
        themeToggle.onclick = function() {
            document.body.classList.toggle('light');
            if(document.body.classList.contains('light')) {
                document.body.style.background = '#f1f1f1';
                document.body.style.color = '#181a1b';
            } else {
                document.body.style.background = '#181a1b';
                document.body.style.color = '#f1f1f1';
            }
        };
    }

    // Navigation handlers
    const navHandlers = {
        'nav-dashboard': showDashboard,
        'nav-transactions': showTransactions,
        'nav-goals': showGoals,
        'nav-analytics': showAnalytics,
        'nav-learning': showLearning,
        'nav-profile': showProfile,
        'nav-login': showLogin
    };

    Object.entries(navHandlers).forEach(([id, handler]) => {
        const el = document.getElementById(id);
        if (el && typeof handler === 'function') {
            el.addEventListener('click', handler);
        }
    });
    
    // Logout handler
    const logoutBtn = document.getElementById('nav-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Check authentication status on load
    updateAuthUI();
}

async function updateAuthUI() {
    try {
        const response = await fetch('/api/user');
        const data = await response.json();
        
        const userInfo = document.getElementById('user-info');
        const userNameDisplay = document.getElementById('user-name-display');
        const logoutBtn = document.getElementById('nav-logout');
        const loginBtn = document.getElementById('nav-login');
        
        const profileBtn = document.getElementById('nav-profile');
        const analyticsBtn = document.getElementById('nav-analytics');
        if (data.email && data.authenticated !== false) {
            // User is logged in
            if (userInfo) userInfo.style.display = 'block';
            if (userNameDisplay) userNameDisplay.textContent = `👤 ${data.name || data.email}`;
            if (logoutBtn) logoutBtn.style.display = 'block';
            if (profileBtn) profileBtn.style.display = 'block';
            if (analyticsBtn) analyticsBtn.style.display = 'block';
            if (loginBtn) loginBtn.style.display = 'none';
        } else {
            // User is not logged in
            if (userInfo) userInfo.style.display = 'none';
            if (logoutBtn) logoutBtn.style.display = 'none';
            if (profileBtn) profileBtn.style.display = 'none';
            if (analyticsBtn) analyticsBtn.style.display = 'none';
            if (loginBtn) loginBtn.style.display = 'block';
        }
    } catch (err) {
        console.error('Error checking auth status:', err);
    }
}

async function handleLogout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        if (response.ok) {
            // Update UI
            updateAuthUI();
            // Redirect to login
            if (typeof showLogin === 'function') {
                showLogin();
            }
        }
    } catch (err) {
        console.error('Logout error:', err);
        // Still update UI and redirect
        updateAuthUI();
        if (typeof showLogin === 'function') {
            showLogin();
        }
    }
}

