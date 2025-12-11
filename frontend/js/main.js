// Main entry point - Initialize app
// This file loads after all other modules

// Wait for DOM to be fully loaded before initializing
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    // DOM is already loaded
    initApp();
}

async function initApp() {
    // Initialize navigation first
    if (typeof initNavigation === 'function') {
        initNavigation();
    }
    
    // Initialize chatbot
    if (typeof initChatbot === 'function') {
        initChatbot();
    }
    
    // Check authentication before showing dashboard
    try {
        const response = await fetch('/api/user');
        const data = await response.json();
        
        if (data.email && data.authenticated !== false) {
            // User is authenticated, show dashboard
            if (typeof showDashboard === 'function') {
                showDashboard();
            }
        } else {
            // User not authenticated, show login
            if (typeof showLogin === 'function') {
                showLogin();
            }
        }
    } catch (err) {
        console.error('Error checking auth:', err);
        // On error, show login as fallback
        if (typeof showLogin === 'function') {
            showLogin();
        }
    }
}
