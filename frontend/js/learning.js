// Learning page functionality (dynamic, personalized modules)

function escapeHtml(str) {
    return String(str ?? '').replace(/[&<>"']/g, function (m) {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return map[m] || m;
    });
}

async function loadLearningRecommendations() {
    const container = document.getElementById('learning-modules');
    if (!container) return;

    container.innerHTML = `<div class="card" style="padding:18px; color:#999;">Loading your learning modules...</div>`;

    try {
        const res = await fetch('/api/learning/recommendations');
        const data = await res.json();
        if (data.error) {
            container.innerHTML = `<div class="card" style="padding:18px; color:#e17055;">${escapeHtml(data.error)}</div>`;
            return;
        }

        const modules = data.recommendations || [];
        if (!modules.length) {
            container.innerHTML = `<div class="card" style="padding:18px; color:#999;">No modules available right now.</div>`;
            return;
        }

        container.innerHTML = modules.map(m => {
            const content = m.generated_content ? m.generated_content : (m.summary || '');
            const contentSafe = escapeHtml(content);
            const title = escapeHtml(m.title);
            const moduleKey = escapeHtml(m.module_key);

            return `
                <div class="card learning-card" data-module-key="${moduleKey}" style="margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
                        <div>
                            <h3 style="margin-top:0;">${title}</h3>
                            <p style="color:#999; margin:6px 0 12px;">Module ${escapeHtml(m.rank ?? '')}</p>
                        </div>
                        <div style="display:flex; gap:8px; flex-wrap:wrap;">
                            <button class="btn-secondary" onclick="completeLearningModule('${moduleKey}')">Mark completed</button>
                            <button class="btn-primary" onclick="regenerateLearningModule('${moduleKey}')">Regenerate</button>
                        </div>
                    </div>
                    <div style="margin-top:10px; white-space:pre-wrap; line-height:1.6;">
                        ${contentSafe}
                    </div>
                    ${m.content_source ? `<div style="margin-top:10px; color:#999; font-size:0.9em;">Source: ${escapeHtml(m.content_source)}</div>` : ''}
                </div>
            `;
        }).join('');
    } catch (err) {
        container.innerHTML = `<div class="card" style="padding:18px; color:#e17055;">Error loading modules: ${escapeHtml(err.message)}</div>`;
    }
}

async function completeLearningModule(moduleKey) {
    try {
        await fetch('/api/learning/complete-module', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ module_key: moduleKey })
        });
    } catch (err) {
        // ignore; UI will reload
    }
    await loadLearningRecommendations();
}

async function regenerateLearningModule(moduleKey) {
    const card = document.querySelector(`[data-module-key="${moduleKey}"]`);
    if (card) {
        card.style.opacity = '0.7';
    }
    try {
        const res = await fetch('/api/learning/regenerate-module', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ module_key: moduleKey })
        });
        const data = await res.json();
        if (data.generated_content) {
            // Replace content block (simple approach: last div with white-space pre-wrap)
            const contentDiv = card.querySelector('div[style*="white-space:pre-wrap"]');
            if (contentDiv) contentDiv.textContent = data.generated_content;
        }
    } catch (err) {
        // ignore
    } finally {
        if (card) card.style.opacity = '1';
    }
}

function showLearning() {
    if (!mainContent) {
        mainContent = document.getElementById('main-content');
    }
    if (!mainContent) return;

    if (typeof setActiveNav === 'function') {
        setActiveNav('nav-learning');
    }

    mainContent.innerHTML = `
        <div class="learning-header">
            <h1>Financial Literacy Center</h1>
            <p class="learning-intro">Personalized modules that adapt after every transaction.</p>
        </div>

        <div class="learning-section">
            <h2 class="section-title">Recommended For You</h2>
            <div id="learning-modules" class="learning-grid"></div>
        </div>
    `;

    loadLearningRecommendations();
}

