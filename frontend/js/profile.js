// Profile management functionality

function showProfile() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;
    
    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-profile');
    }
    
    // Fetch current user data
    fetch('/api/user')
        .then(res => res.json())
        .then(userData => {
            if (!userData.authenticated) {
                if (typeof showLogin === 'function') {
                    showLogin();
                }
                return;
            }
            renderProfilePage(userData);
        })
        .catch(err => {
            console.error('Error fetching user data:', err);
            mainContent.innerHTML = '<div class="card"><p>Error loading profile. Please try again.</p></div>';
        });
}

function renderProfilePage(userData) {
    // Fetch additional stats
    fetch('/api/summary')
        .then(res => res.json())
        .then(stats => {
            renderProfileContent(userData, stats);
        })
        .catch(err => {
            renderProfileContent(userData, null);
        });
}

function renderProfileContent(userData, stats) {
    const memberSince = userData.created_at || 'N/A';
    const initials = (userData.name || userData.email || 'U').substring(0, 2).toUpperCase();
    
    mainContent.innerHTML = `
        <div class="profile-page">
            <!-- Profile Header with Avatar -->
            <div class="profile-header-section">
                <div class="profile-avatar-container">
                    <div class="profile-avatar">
                        <span class="avatar-initials">${initials}</span>
                    </div>
                    <div class="avatar-badge">
                        <span class="badge-icon">✓</span>
                    </div>
                </div>
                <div class="profile-header-info">
                    <h1 class="profile-name">${userData.name || 'User'}</h1>
                    <p class="profile-email">${userData.email || ''}</p>
                    <div class="profile-meta">
                        <span class="meta-item">
                            <span class="meta-icon">📅</span>
                            Member since ${memberSince}
                        </span>
                    </div>
                </div>
            </div>

            <!-- Quick Stats -->
            ${stats ? `
            <div class="profile-quick-stats">
                <div class="quick-stat-card income-stat">
                    <div class="stat-icon">💰</div>
                    <div class="stat-content">
                        <div class="stat-label">Total Income</div>
                        <div class="stat-value">₹${parseFloat(stats.income || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                    </div>
                </div>
                <div class="quick-stat-card expense-stat">
                    <div class="stat-icon">💸</div>
                    <div class="stat-content">
                        <div class="stat-label">Total Expenses</div>
                        <div class="stat-value">₹${parseFloat(stats.expense || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                    </div>
                </div>
                <div class="quick-stat-card balance-stat">
                    <div class="stat-icon">⚖️</div>
                    <div class="stat-content">
                        <div class="stat-label">Balance</div>
                        <div class="stat-value">₹${parseFloat(stats.savings || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                    </div>
                </div>
            </div>
            ` : ''}

            <!-- Main Content Grid -->
            <div class="profile-content-grid">
                <!-- Personal Information Card -->
                <div class="profile-section-card">
                    <div class="section-header">
                        <div class="section-icon">👤</div>
                        <div>
                            <h2>Personal Information</h2>
                            <p class="section-subtitle">Update your account details</p>
                        </div>
                    </div>
                    <form id="profile-form" class="profile-form">
                        <div class="form-group">
                            <label for="profile-name">
                                <span class="label-icon">👤</span>
                                Full Name
                            </label>
                            <input type="text" id="profile-name" value="${userData.name || ''}" placeholder="Enter your full name" required>
                        </div>
                        <div class="form-group">
                            <label for="profile-email">
                                <span class="label-icon">📧</span>
                                Email Address
                            </label>
                            <input type="email" id="profile-email" value="${userData.email || ''}" placeholder="Enter your email" required>
                        </div>
                        <div class="form-group">
                            <label>
                                <span class="label-icon">🆔</span>
                                User ID
                            </label>
                            <input type="text" value="#${userData.id || 'N/A'}" disabled class="disabled-input">
                        </div>
                        <button type="submit" class="btn-primary btn-save">
                            <span class="btn-icon">💾</span>
                            Save Changes
                        </button>
                        <div id="profile-feedback" class="feedback-message" style="display:none;"></div>
                    </form>
                </div>

                <!-- Security Card -->
                <div class="profile-section-card">
                    <div class="section-header">
                        <div class="section-icon">🔒</div>
                        <div>
                            <h2>Security & Password</h2>
                            <p class="section-subtitle">Change your password to keep your account secure</p>
                        </div>
                    </div>
                    <form id="password-form" class="profile-form">
                        <div class="form-group">
                            <label for="current-password">
                                <span class="label-icon">🔑</span>
                                Current Password
                            </label>
                            <div class="input-wrapper">
                                <input type="password" id="current-password" placeholder="Enter current password" required>
                                <button type="button" class="password-toggle" data-target="current-password">👁️</button>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="new-password">
                                <span class="label-icon">🔐</span>
                                New Password
                            </label>
                            <div class="input-wrapper">
                                <input type="password" id="new-password" placeholder="Enter new password (min 6 characters)" required minlength="6">
                                <button type="button" class="password-toggle" data-target="new-password">👁️</button>
                            </div>
                            <div id="password-strength" class="password-strength" style="display:none;">
                                <div class="strength-bar">
                                    <div class="strength-fill" id="strength-fill"></div>
                                </div>
                                <span class="strength-text" id="strength-text"></span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="confirm-password">
                                <span class="label-icon">✓</span>
                                Confirm New Password
                            </label>
                            <div class="input-wrapper">
                                <input type="password" id="confirm-password" placeholder="Confirm new password" required minlength="6">
                                <button type="button" class="password-toggle" data-target="confirm-password">👁️</button>
                            </div>
                        </div>
                        <button type="submit" class="btn-primary btn-save">
                            <span class="btn-icon">🔒</span>
                            Update Password
                        </button>
                        <div id="password-feedback" class="feedback-message" style="display:none;"></div>
                    </form>
                </div>

                <!-- Gmail Integration Card -->
                <div class="profile-section-card">
                    <div class="section-header">
                        <div class="section-icon">📧</div>
                        <div>
                            <h2>Gmail Integration</h2>
                            <p class="section-subtitle">Auto-log transactions from your email</p>
                        </div>
                    </div>
                    <div id="gmail-status" class="gmail-integration-section">
                        <div id="gmail-status-content"></div>
                        <button id="gmail-connect-btn" class="btn-primary" style="display: none;">
                            <span class="btn-icon">🔗</span>
                            Connect Gmail
                        </button>
                        <button id="gmail-disconnect-btn" class="btn-secondary" style="display: none;">
                            <span class="btn-icon">🔌</span>
                            Disconnect
                        </button>
                        <button id="gmail-sync-btn" class="btn-secondary" style="display: none; margin-left: 10px;">
                            <span class="btn-icon">🔄</span>
                            Sync Now
                        </button>
                        <div id="gmail-feedback" class="feedback-message" style="display:none;"></div>
                    </div>
                </div>

                <!-- Account Settings Card -->
                <div class="profile-section-card">
                    <div class="section-header">
                        <div class="section-icon">⚙️</div>
                        <div>
                            <h2>Account Settings</h2>
                            <p class="section-subtitle">Manage your account preferences</p>
                        </div>
                    </div>
                    <div class="settings-list">
                        <div class="setting-item">
                            <div class="setting-info">
                                <div class="setting-icon">🎨</div>
                                <div>
                                    <div class="setting-title">Theme</div>
                                    <div class="setting-desc">Choose your preferred color theme</div>
                                </div>
                            </div>
                            <div class="setting-control">
                                <button class="theme-toggle-btn" id="theme-toggle">
                                    <span class="theme-icon">🌙</span>
                                    <span class="theme-text">Dark Mode</span>
                                </button>
                            </div>
                        </div>
                        <div class="setting-item">
                            <div class="setting-info">
                                <div class="setting-icon">📊</div>
                                <div>
                                    <div class="setting-title">Account Statistics</div>
                                    <div class="setting-desc">View detailed account information</div>
                                </div>
                            </div>
                            <div class="setting-control">
                                <button class="btn-secondary" onclick="showAccountStats()">
                                    View Stats
                                </button>
                            </div>
                        </div>
                        <div class="setting-item">
                            <div class="setting-info">
                                <div class="setting-icon">📧</div>
                                <div>
                                    <div class="setting-title">Email Reports</div>
                                    <div class="setting-desc">Receive monthly financial reports</div>
                                </div>
                            </div>
                            <div class="setting-control">
                                <label class="toggle-switch">
                                    <input type="checkbox" id="email-reports-toggle" checked>
                                    <span class="toggle-slider"></span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Account Information Card -->
                <div class="profile-section-card">
                    <div class="section-header">
                        <div class="section-icon">ℹ️</div>
                        <div>
                            <h2>Account Information</h2>
                            <p class="section-subtitle">Your account details and statistics</p>
                        </div>
                    </div>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-icon">📅</div>
                            <div class="info-content">
                                <div class="info-label">Member Since</div>
                                <div class="info-value">${memberSince}</div>
                            </div>
                        </div>
                        <div class="info-item">
                            <div class="info-icon">📧</div>
                            <div class="info-content">
                                <div class="info-label">Email Address</div>
                                <div class="info-value email-value" title="${userData.email || 'N/A'}">${userData.email || 'N/A'}</div>
                            </div>
                        </div>
                        <div class="info-item">
                            <div class="info-icon">🆔</div>
                            <div class="info-content">
                                <div class="info-label">User ID</div>
                                <div class="info-value">#${userData.id || 'N/A'}</div>
                            </div>
                        </div>
                        <div class="info-item">
                            <div class="info-icon">✅</div>
                            <div class="info-content">
                                <div class="info-label">Account Status</div>
                                <div class="info-value status-active">Active</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Delete Account Section -->
                    <div class="delete-account-section">
                        <div class="delete-account-header">
                            <div class="delete-icon">🗑️</div>
                            <div>
                                <h3>Danger Zone</h3>
                                <p class="delete-warning">Permanently delete your account and all associated data</p>
                            </div>
                        </div>
                        <button class="btn-delete" onclick="showDeleteAccountModal()">
                            <span class="btn-icon">🗑️</span>
                            Delete Account
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Account Confirmation Modal -->
        <div id="delete-account-modal" class="modal-overlay" style="display: none;">
            <div class="modal-container">
                <div class="modal-header">
                    <div class="modal-icon danger-icon">⚠️</div>
                    <h2>Delete Account</h2>
                </div>
                <div class="modal-content">
                    <p class="modal-warning-text">
                        This action cannot be undone. This will permanently delete your account, 
                        remove all your data, transactions, goals, and settings from our servers.
                    </p>
                    <div class="verification-step" id="verification-step-1">
                        <p class="verification-label">To confirm, please type your email address:</p>
                        <input type="email" id="delete-email-verification" class="verification-input" 
                               placeholder="${userData.email || 'Enter your email'}" autocomplete="off">
                    </div>
                    <div class="verification-step" id="verification-step-2" style="display: none;">
                        <p class="verification-label">Type <strong>"DELETE"</strong> to confirm:</p>
                        <input type="text" id="delete-confirm-text" class="verification-input" 
                               placeholder="Type DELETE" autocomplete="off">
                    </div>
                    <div id="delete-error-message" class="delete-error" style="display: none;"></div>
                </div>
                <div class="modal-actions">
                    <button class="btn-modal-cancel" onclick="closeDeleteAccountModal()">Cancel</button>
                    <button class="btn-modal-delete" id="btn-delete-confirm" onclick="handleDeleteAccount('${userData.email || ''}')" disabled>
                        Delete Account
                    </button>
                </div>
            </div>
        </div>
    `;

    // Initialize password toggle buttons
    document.querySelectorAll('.password-toggle').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (input.type === 'password') {
                input.type = 'text';
                this.textContent = '🙈';
            } else {
                input.type = 'password';
                this.textContent = '👁️';
            }
        });
    });

    // Password strength indicator
    const newPasswordInput = document.getElementById('new-password');
    if (newPasswordInput) {
        newPasswordInput.addEventListener('input', function() {
            checkPasswordStrength(this.value);
        });
    }

    // Load Gmail status
    loadGmailStatus();
    
    // Gmail connect button
    const gmailConnectBtn = document.getElementById('gmail-connect-btn');
    if (gmailConnectBtn) {
        gmailConnectBtn.addEventListener('click', async function() {
            try {
                const response = await fetch('/api/gmail/connect');
                const data = await response.json();
                if (data.auth_url) {
                    // Open OAuth popup
                    const popup = window.open(data.auth_url, 'gmail_auth', 'width=500,height=600');
                    
                    // Listen for OAuth callback
                    window.addEventListener('message', function(event) {
                        if (event.data.type === 'gmail_connected' && event.data.success) {
                            popup.close();
                            loadGmailStatus();
                            showFeedback('gmail-feedback', 'Gmail connected successfully!', 'success');
                        }
                    });
                }
            } catch (error) {
                showFeedback('gmail-feedback', 'Error connecting Gmail: ' + error.message, 'error');
            }
        });
    }
    
    // Gmail disconnect button
    const gmailDisconnectBtn = document.getElementById('gmail-disconnect-btn');
    if (gmailDisconnectBtn) {
        gmailDisconnectBtn.addEventListener('click', async function() {
            if (!confirm('Are you sure you want to disconnect Gmail? Auto-logging will stop.')) return;
            
            try {
                const response = await fetch('/api/gmail/disconnect', { method: 'POST' });
                const data = await response.json();
                if (response.ok) {
                    loadGmailStatus();
                    showFeedback('gmail-feedback', 'Gmail disconnected successfully.', 'success');
                } else {
                    showFeedback('gmail-feedback', data.error || 'Error disconnecting Gmail', 'error');
                }
            } catch (error) {
                showFeedback('gmail-feedback', 'Error disconnecting Gmail: ' + error.message, 'error');
            }
        });
    }
    
    // Gmail sync button
    const gmailSyncBtn = document.getElementById('gmail-sync-btn');
    if (gmailSyncBtn) {
        gmailSyncBtn.addEventListener('click', async function() {
            gmailSyncBtn.disabled = true;
            gmailSyncBtn.textContent = '🔄 Syncing...';
            
            try {
                const response = await fetch('/api/gmail/sync', { method: 'POST' });
                const data = await response.json();
                if (response.ok) {
                    showFeedback('gmail-feedback', data.message || 'Sync started. Check transactions shortly.', 'success');
                    setTimeout(() => {
                        if (typeof showTransactions === 'function') showTransactions();
                    }, 2000);
                } else {
                    showFeedback('gmail-feedback', data.error || 'Error syncing', 'error');
                }
            } catch (error) {
                showFeedback('gmail-feedback', 'Error syncing: ' + error.message, 'error');
            } finally {
                gmailSyncBtn.disabled = false;
                gmailSyncBtn.innerHTML = '<span class="btn-icon">🔄</span> Sync Now';
            }
        });
    }
    
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const body = document.body;
            const isLight = body.classList.contains('light');
            if (isLight) {
                body.classList.remove('light');
                this.innerHTML = '<span class="theme-icon">🌙</span><span class="theme-text">Dark Mode</span>';
            } else {
                body.classList.add('light');
                this.innerHTML = '<span class="theme-icon">☀️</span><span class="theme-text">Light Mode</span>';
            }
        });
    }

    // Check current theme
    if (document.body.classList.contains('light') && themeToggle) {
        themeToggle.innerHTML = '<span class="theme-icon">☀️</span><span class="theme-text">Light Mode</span>';
    }
    
    // Handle profile update form
    const profileForm = document.getElementById('profile-form');
    const profileFeedback = document.getElementById('profile-feedback');
    
    if (profileForm) {
        profileForm.onsubmit = function(e) {
            e.preventDefault();
            const name = document.getElementById('profile-name').value.trim();
            const email = document.getElementById('profile-email').value.trim();
            
            profileFeedback.style.display = 'block';
            profileFeedback.className = 'feedback-message feedback-loading';
            profileFeedback.innerHTML = '<span class="feedback-icon">⏳</span> Updating profile...';
            
            fetch('/api/user', {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name, email })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    profileFeedback.className = 'feedback-message feedback-error';
                    profileFeedback.innerHTML = `<span class="feedback-icon">❌</span> ${data.error}`;
                } else {
                    profileFeedback.className = 'feedback-message feedback-success';
                    profileFeedback.innerHTML = '<span class="feedback-icon">✅</span> Profile updated successfully!';
                    // Update navigation UI
                    if (typeof updateAuthUI === 'function') {
                        updateAuthUI();
                    }
                    // Update header name
                    const profileNameEl = document.querySelector('.profile-name');
                    if (profileNameEl) profileNameEl.textContent = name;
                }
            })
            .catch(err => {
                profileFeedback.className = 'feedback-message feedback-error';
                profileFeedback.innerHTML = '<span class="feedback-icon">❌</span> Error updating profile. Please try again.';
            });
        };
    }
    
    // Handle password change form
    const passwordForm = document.getElementById('password-form');
    const passwordFeedback = document.getElementById('password-feedback');
    
    if (passwordForm) {
        passwordForm.onsubmit = function(e) {
            e.preventDefault();
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            if (newPassword !== confirmPassword) {
                passwordFeedback.style.display = 'block';
                passwordFeedback.className = 'feedback-message feedback-error';
                passwordFeedback.innerHTML = '<span class="feedback-icon">❌</span> New passwords do not match';
                return;
            }
            
            if (newPassword.length < 6) {
                passwordFeedback.style.display = 'block';
                passwordFeedback.className = 'feedback-message feedback-error';
                passwordFeedback.innerHTML = '<span class="feedback-icon">❌</span> Password must be at least 6 characters';
                return;
            }
            
            passwordFeedback.style.display = 'block';
            passwordFeedback.className = 'feedback-message feedback-loading';
            passwordFeedback.innerHTML = '<span class="feedback-icon">⏳</span> Changing password...';
            
            fetch('/api/user/password', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    passwordFeedback.className = 'feedback-message feedback-error';
                    passwordFeedback.innerHTML = `<span class="feedback-icon">❌</span> ${data.error}`;
                } else {
                    passwordFeedback.className = 'feedback-message feedback-success';
                    passwordFeedback.innerHTML = '<span class="feedback-icon">✅</span> Password changed successfully!';
                    passwordForm.reset();
                    const strengthDiv = document.getElementById('password-strength');
                    if (strengthDiv) strengthDiv.style.display = 'none';
                }
            })
            .catch(err => {
                passwordFeedback.className = 'feedback-message feedback-error';
                passwordFeedback.innerHTML = '<span class="feedback-icon">❌</span> Error changing password. Please try again.';
            });
        };
    }
}

function checkPasswordStrength(password) {
    const strengthDiv = document.getElementById('password-strength');
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');
    
    if (!password) {
        strengthDiv.style.display = 'none';
        return;
    }
    
    strengthDiv.style.display = 'block';
    
    let strength = 0;
    let strengthLabel = '';
    let strengthColor = '';
    
    if (password.length >= 6) strength += 1;
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 1;
    if (/\d/.test(password)) strength += 1;
    if (/[^a-zA-Z\d]/.test(password)) strength += 1;
    
    if (strength <= 2) {
        strengthLabel = 'Weak';
        strengthColor = '#e17055';
    } else if (strength <= 4) {
        strengthLabel = 'Medium';
        strengthColor = '#fdcb6e';
    } else {
        strengthLabel = 'Strong';
        strengthColor = '#00b894';
    }
    
    const percentage = (strength / 6) * 100;
    strengthFill.style.width = percentage + '%';
    strengthFill.style.backgroundColor = strengthColor;
    strengthText.textContent = strengthLabel;
    strengthText.style.color = strengthColor;
}

function showAccountStats() {
    // This can be expanded to show detailed statistics
    alert('Account statistics feature coming soon!');
}

function showDeleteAccountModal() {
    const modal = document.getElementById('delete-account-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        // Reset modal state
        const step1 = document.getElementById('verification-step-1');
        const step2 = document.getElementById('verification-step-2');
        const emailInput = document.getElementById('delete-email-verification');
        const confirmInput = document.getElementById('delete-confirm-text');
        const errorDiv = document.getElementById('delete-error-message');
        const deleteBtn = document.getElementById('btn-delete-confirm');
        
        step1.style.display = 'block';
        step2.style.display = 'none';
        emailInput.value = '';
        confirmInput.value = '';
        errorDiv.style.display = 'none';
        deleteBtn.disabled = true;
        deleteBtn.style.opacity = '0.5';
        deleteBtn.innerHTML = 'Delete Account';
        emailInput.style.borderColor = '';
        confirmInput.style.borderColor = '';
        emailInput.focus();
    }
}

function closeDeleteAccountModal() {
    const modal = document.getElementById('delete-account-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

function handleDeleteAccount(userEmail) {
    const emailInput = document.getElementById('delete-email-verification');
    let confirmInput = document.getElementById('delete-confirm-text');
    const errorDiv = document.getElementById('delete-error-message');
    const deleteBtn = document.getElementById('btn-delete-confirm');
    const step1 = document.getElementById('verification-step-1');
    const step2 = document.getElementById('verification-step-2');
    
    // Step 1: Verify email
    if (step2.style.display === 'none' || step2.style.display === '') {
        const enteredEmail = emailInput.value.trim().toLowerCase();
        const correctEmail = userEmail.toLowerCase();
        
        if (enteredEmail !== correctEmail) {
            errorDiv.textContent = 'Email does not match. Please try again.';
            errorDiv.style.display = 'block';
            emailInput.style.borderColor = '#f44336';
            return;
        }
        
        // Email verified, show step 2
        step1.style.display = 'none';
        step2.style.display = 'block';
        errorDiv.style.display = 'none';
        emailInput.style.borderColor = '';
        
        // Get fresh reference to confirm input
        confirmInput = document.getElementById('delete-confirm-text');
        confirmInput.focus();
        
        // Enable delete button when user types DELETE
        confirmInput.addEventListener('input', function() {
            if (this.value.trim().toUpperCase() === 'DELETE') {
                deleteBtn.disabled = false;
                deleteBtn.style.opacity = '1';
            } else {
                deleteBtn.disabled = true;
                deleteBtn.style.opacity = '0.5';
            }
        });
        return;
    }
    
    // Step 2: Verify DELETE text and proceed with deletion
    // Get fresh reference
    confirmInput = document.getElementById('delete-confirm-text');
    if (confirmInput.value.trim().toUpperCase() !== 'DELETE') {
        errorDiv.textContent = 'Please type "DELETE" exactly to confirm.';
        errorDiv.style.display = 'block';
        confirmInput.style.borderColor = '#f44336';
        return;
    }
    
    // All verifications passed, proceed with deletion
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<span class="btn-icon">⏳</span> Deleting...';
    errorDiv.style.display = 'none';
    
    fetch('/api/user/delete', {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'}
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            errorDiv.textContent = data.error;
            errorDiv.style.display = 'block';
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = 'Delete Account';
        } else {
            // Account deleted successfully
            alert('Your account has been permanently deleted. You will be logged out now.');
            // Redirect to login or home page
            if (typeof handleLogout === 'function') {
                handleLogout();
            } else {
                window.location.href = '/';
            }
        }
    })
    .catch(err => {
        errorDiv.textContent = 'Error deleting account. Please try again.';
        errorDiv.style.display = 'block';
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = 'Delete Account';
    });
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('delete-account-modal');
    if (modal && event.target === modal) {
        closeDeleteAccountModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('delete-account-modal');
        if (modal && modal.style.display === 'flex') {
            closeDeleteAccountModal();
        }
    }
});

async function loadGmailStatus() {
    const statusContent = document.getElementById('gmail-status-content');
    const connectBtn = document.getElementById('gmail-connect-btn');
    const disconnectBtn = document.getElementById('gmail-disconnect-btn');
    const syncBtn = document.getElementById('gmail-sync-btn');
    
    if (!statusContent) return;
    
    try {
        const response = await fetch('/api/gmail/status');
        const data = await response.json();
        
        if (data.connected) {
            statusContent.innerHTML = `
                <div style="padding: 15px; background: rgba(0, 184, 148, 0.1); border-radius: 8px; margin-bottom: 15px;">
                    <p style="margin: 0; color: #00b894;"><strong>✓ Gmail Connected</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #999;">
                        Connected: ${data.connected_at || 'N/A'}<br>
                        Last sync: ${data.last_sync_at || 'Never'}
                    </p>
                </div>
                <p style="color: #999; font-size: 0.9em; margin-bottom: 15px;">
                    FinFit will automatically scan your Gmail for UPI/bank transaction emails and log them as transactions.
                </p>
            `;
            if (connectBtn) connectBtn.style.display = 'none';
            if (disconnectBtn) disconnectBtn.style.display = 'inline-block';
            if (syncBtn) syncBtn.style.display = 'inline-block';
        } else {
            statusContent.innerHTML = `
                <p style="color: #999; margin-bottom: 15px;">
                    Connect your Gmail account to automatically log transactions from payment emails.
                </p>
            `;
            if (connectBtn) connectBtn.style.display = 'inline-block';
            if (disconnectBtn) disconnectBtn.style.display = 'none';
            if (syncBtn) syncBtn.style.display = 'none';
        }
    } catch (error) {
        statusContent.innerHTML = '<p style="color: #ff6b6b;">Error loading Gmail status.</p>';
    }
}

function showFeedback(elementId, message, type) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.style.display = 'block';
    element.className = `feedback-message feedback-${type}`;
    element.innerHTML = `<span class="feedback-icon">${type === 'success' ? '✅' : '❌'}</span> ${message}`;
    
    if (type === 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}






