// Learning page functionality

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
            <h1>📚 Financial Literacy Center</h1>
            <p class="learning-intro">Master your finances with comprehensive guides, tips, and strategies to build wealth and achieve financial freedom.</p>
        </div>
        
        <div class="learning-section">
            <h2 class="section-title">🎯 Core Concepts</h2>
            <div class="learning-grid">
                <div class="card learning-card">
                    <h3>💡 Budgeting Basics</h3>
                    <p><strong>The 50/30/20 Rule:</strong> Allocate 50% of income to needs (housing, food, utilities), 30% to wants (entertainment, dining out), and 20% to savings and debt repayment. This simple framework helps maintain financial balance and ensures you're saving consistently.</p>
                    <p><strong>Zero-Based Budgeting:</strong> Assign every rupee a purpose before the month begins. This method ensures complete control over your finances and eliminates wasteful spending.</p>
                </div>
                <div class="card learning-card">
                    <h3>💰 Emergency Fund</h3>
                    <p><strong>What is an emergency fund?</strong> An emergency fund is money set aside to cover unexpected expenses, like medical bills, car repairs, or job loss. It's your financial safety net.</p>
                    <p><strong>How much to save:</strong> Aim for 3-6 months of living expenses. Start with ₹10,000-₹50,000 as a beginner goal, then build up to cover 6 months of essential expenses.</p>
                    <p><strong>Where to keep it:</strong> Store in a high-yield savings account that's easily accessible but separate from your checking account.</p>
                </div>
                <div class="card learning-card">
                    <h3>📊 Tracking Expenses</h3>
                    <p><strong>Why track expenses?</strong> Understanding where your money goes is the first step to financial control. You can't manage what you don't measure.</p>
                    <p><strong>Best practices:</strong> Record every transaction, categorize spending, review weekly, and identify patterns. Use FinFit's transaction tracker to automate this process.</p>
                    <p><strong>Common categories:</strong> Housing, Transportation, Food, Utilities, Healthcare, Entertainment, Debt Payments, Savings.</p>
                </div>
                <div class="card learning-card">
                    <h3>🎯 Setting Financial Goals</h3>
                    <p><strong>SMART Goals Framework:</strong></p>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li><strong>Specific:</strong> "Save ₹50,000 for vacation" not "Save money"</li>
                        <li><strong>Measurable:</strong> Track progress with numbers</li>
                        <li><strong>Achievable:</strong> Realistic based on your income</li>
                        <li><strong>Relevant:</strong> Aligned with your values</li>
                        <li><strong>Time-bound:</strong> Set a deadline</li>
                    </ul>
                    <p>Break large goals into smaller milestones for better success and motivation.</p>
                </div>
            </div>
        </div>
        
        <div class="learning-section">
            <h2 class="section-title">💳 Debt Management</h2>
            <div class="learning-grid">
                <div class="card learning-card">
                    <h3>🔥 High-Interest Debt Strategy</h3>
                    <p><strong>Avalanche Method:</strong> Pay off debts with highest interest rates first. This saves the most money over time.</p>
                    <p><strong>Snowball Method:</strong> Pay off smallest debts first for quick wins and motivation.</p>
                    <p><strong>Key principle:</strong> Always pay more than minimum payments. Even an extra ₹500/month can save thousands in interest.</p>
                </div>
                <div class="card learning-card">
                    <h3>📉 Credit Score Basics</h3>
                    <p><strong>What affects your score:</strong> Payment history (35%), credit utilization (30%), credit history length (15%), credit mix (10%), new credit (10%).</p>
                    <p><strong>How to improve:</strong> Pay bills on time, keep credit utilization below 30%, don't close old accounts, limit hard inquiries.</p>
                    <p><strong>Why it matters:</strong> Good credit scores (750+) get you better interest rates, saving thousands on loans.</p>
                </div>
            </div>
        </div>
        
        <div class="learning-section">
            <h2 class="section-title">📈 Saving & Investing</h2>
            <div class="learning-grid">
                <div class="card learning-card">
                    <h3>💵 Saving Strategies</h3>
                    <p><strong>Pay yourself first:</strong> Set aside savings before spending on non-essentials. Automate transfers to savings accounts to make it effortless.</p>
                    <p><strong>Rule of 72:</strong> Divide 72 by your interest rate to see how long it takes money to double. At 8% return, money doubles in 9 years.</p>
                    <p><strong>Compound interest:</strong> Your money earns money, and those earnings earn money too. Start early to maximize this powerful effect.</p>
                </div>
                <div class="card learning-card">
                    <h3>📊 Investment Basics</h3>
                    <p><strong>Start with basics:</strong> Build emergency fund first, then pay high-interest debt, then invest.</p>
                    <p><strong>Diversification:</strong> Don't put all eggs in one basket. Spread investments across stocks, bonds, and other assets.</p>
                    <p><strong>Long-term thinking:</strong> Invest for 5+ years. Short-term market fluctuations are normal; focus on long-term growth.</p>
                    <p><strong>Index funds:</strong> Low-cost way to invest in entire market. Perfect for beginners.</p>
                </div>
                <div class="card learning-card">
                    <h3>🏦 Retirement Planning</h3>
                    <p><strong>Start early:</strong> The earlier you start, the less you need to save monthly due to compound interest.</p>
                    <p><strong>Rule of thumb:</strong> Save 15% of income for retirement. If you start at 25, you'll likely retire comfortably.</p>
                    <p><strong>Take advantage:</strong> Use employer-matched retirement accounts - it's free money!</p>
                </div>
            </div>
        </div>
        
        <div class="learning-section">
            <h2 class="section-title">🛒 Smart Spending</h2>
            <div class="learning-grid">
                <div class="card learning-card">
                    <h3>💸 Needs vs. Wants</h3>
                    <p><strong>Needs:</strong> Essential for survival and basic well-being (food, shelter, healthcare, transportation to work).</p>
                    <p><strong>Wants:</strong> Enhance quality of life but aren't essential (dining out, entertainment, luxury items).</p>
                    <p><strong>Strategy:</strong> Always cover needs first. For wants, use the 24-hour rule: wait a day before purchasing to avoid impulse buys.</p>
                </div>
                <div class="card learning-card">
                    <h3>🛍️ Smart Shopping Tips</h3>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Create shopping lists and stick to them</li>
                        <li>Compare prices online before buying</li>
                        <li>Use cash-back apps and credit card rewards</li>
                        <li>Buy generic brands for non-essential items</li>
                        <li>Wait for sales on big-ticket items</li>
                        <li>Unsubscribe from marketing emails to reduce temptation</li>
                    </ul>
                </div>
                <div class="card learning-card">
                    <h3>📱 Subscription Management</h3>
                    <p><strong>Audit regularly:</strong> Review subscriptions monthly. Cancel unused services - they add up quickly.</p>
                    <p><strong>Common culprits:</strong> Streaming services, gym memberships, software subscriptions, magazine subscriptions.</p>
                    <p><strong>Tip:</strong> Use FinFit to track all subscriptions and set reminders to review them quarterly.</p>
                </div>
            </div>
        </div>
        
        <div class="learning-section">
            <h2 class="section-title">📅 Financial Habits</h2>
            <div class="learning-grid">
                <div class="card learning-card">
                    <h3>✅ Monthly Financial Review</h3>
                    <p><strong>What to review:</strong> Income vs. expenses, progress toward goals, spending patterns, upcoming bills.</p>
                    <p><strong>Questions to ask:</strong> Did I stay within budget? Where did I overspend? What can I improve next month?</p>
                    <p><strong>Celebrate wins:</strong> Acknowledge progress, even small steps. Positive reinforcement builds lasting habits.</p>
                </div>
                <div class="card learning-card">
                    <h3>🎯 Goal Tracking</h3>
                    <p><strong>Set milestones:</strong> Break annual goals into monthly targets. This makes progress visible and motivating.</p>
                    <p><strong>Adjust as needed:</strong> Life changes, so should your goals. Review and update quarterly.</p>
                    <p><strong>Use FinFit:</strong> Track goals in the app, get progress updates, and celebrate achievements.</p>
                </div>
            </div>
        </div>
        
        <div class="card tips-card">
            <h3>💡 Quick Financial Tips</h3>
            <ul class="tips-list">
                <li><strong>Automate savings:</strong> Set up automatic transfers to savings account on payday</li>
                <li><strong>Track everything:</strong> Record every expense, even small ones - they add up quickly</li>
                <li><strong>Use the envelope method:</strong> Allocate cash to different spending categories</li>
                <li><strong>Build emergency fund first:</strong> Before investing, ensure you have 3-6 months of expenses saved</li>
                <li><strong>Review subscriptions:</strong> Cancel unused services monthly - save hundreds per year</li>
                <li><strong>Pay bills automatically:</strong> Set up auto-pay to avoid late fees and maintain good credit</li>
                <li><strong>Negotiate bills:</strong> Call service providers annually to negotiate better rates</li>
                <li><strong>Meal planning:</strong> Plan meals weekly to reduce food waste and save money</li>
                <li><strong>Buy quality:</strong> Sometimes spending more upfront saves money long-term (buy it for life)</li>
                <li><strong>Learn continuously:</strong> Read financial books, follow finance blogs, stay educated</li>
            </ul>
        </div>
        
        <div class="card learning-card" style="margin-top: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <h3 style="color: white; margin-top: 0;">🚀 Ready to Start?</h3>
            <p>Use FinFit's tools to put these concepts into practice:</p>
            <ul style="margin: 15px 0; padding-left: 20px;">
                <li>Track your expenses in the Transactions section</li>
                <li>Set and monitor goals in the Goals section</li>
                <li>Review your dashboard for insights and predictions</li>
                <li>Chat with our AI assistant for personalized advice</li>
                <li>Generate monthly reports to track your progress</li>
            </ul>
        </div>
    `;
}

