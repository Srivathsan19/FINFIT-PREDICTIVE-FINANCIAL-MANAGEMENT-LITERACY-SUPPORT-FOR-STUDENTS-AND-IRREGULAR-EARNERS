"""
Machine Learning models for financial analytics
"""
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import math


class PersonalityClassifier:
    """ML-based classifier for spending personality"""
    
    def __init__(self):
        self.saver_threshold = 0.20  # 20% savings rate
        self.spender_threshold = 0.05  # 5% savings rate (or negative)
        
    def classify(self, transactions: List[Dict], total_income: float, total_expense: float) -> Dict:
        """
        Classify spending personality using ML features
        
        Features:
        - Savings rate
        - Expense consistency (variance)
        - Category diversity
        - Impulse spending patterns
        - Income stability
        """
        if total_income == 0:
            return {
                'personality': 'Unknown',
                'confidence': 0,
                'savings_rate': 0,
                'traits': ['Insufficient data'],
                'recommendations': ['Start tracking your income and expenses']
            }
        
        # Calculate savings rate (can be negative if spending exceeds income)
        savings_rate = (total_income - total_expense) / total_income if total_income > 0 else -1
        
        # Calculate features
        features = self._extract_features(transactions, total_income, total_expense, savings_rate)
        
        # ML-based classification
        personality, confidence = self._classify_personality(features, savings_rate)
        
        # Generate traits and recommendations
        traits = self._generate_traits(personality, features)
        recommendations = self._generate_recommendations(personality, features)
        
        return {
            'personality': personality,
            'confidence': f"{confidence:.1f}%",
            'savings_rate': f"{savings_rate * 100:.1f}",
            'total_income': total_income,
            'total_expense': total_expense,
            'traits': traits,
            'recommendations': recommendations
        }
    
    def _extract_features(self, transactions: List[Dict], income: float, expense: float, savings_rate: float) -> Dict:
        """Extract ML features from transactions"""
        if not transactions:
            return {
                'expense_variance': 0,
                'category_diversity': 0,
                'impulse_score': 0,
                'income_stability': 0,
                'large_purchase_ratio': 0,
                'immediate_spending_score': 0
            }
        
        expenses = [t for t in transactions if t.get('type') == 'expense']
        
        # Feature 1: Expense variance (consistency)
        daily_expenses = defaultdict(float)
        for t in expenses:
            try:
                date_str = t['date']
                if isinstance(date_str, str):
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    date = date_str if hasattr(date_str, 'date') else datetime.now().date()
                daily_expenses[date] += t['amount']
            except (ValueError, KeyError, TypeError):
                # Skip invalid dates
                continue
        
        if daily_expenses:
            expense_values = list(daily_expenses.values())
            expense_variance = np.var(expense_values) if len(expense_values) > 1 else 0
            expense_mean = np.mean(expense_values)
            expense_variance = expense_variance / (expense_mean ** 2) if expense_mean > 0 else 0
        else:
            expense_variance = 0
        
        # Feature 2: Category diversity (normalized)
        category_counts = defaultdict(int)
        for t in expenses:
            category_counts[t.get('category', 'Other')] += 1
        
        total_categories = len(category_counts)
        # Normalize: more categories relative to transactions = more diverse
        if len(expenses) > 0:
            category_diversity = min(1.0, total_categories / max(len(expenses) / 3, 1))
        else:
            category_diversity = 0
        
        # Feature 3: Impulse spending score (small frequent purchases)
        # Calculate average transaction amount
        if len(expenses) > 0:
            avg_transaction = expense / len(expenses)
            # Small purchases are those less than 30% of average
            small_purchases = [t for t in expenses if t['amount'] < avg_transaction * 0.3]
            impulse_score = len(small_purchases) / len(expenses)
        else:
            impulse_score = 0
        
        # Feature 4: Large purchase ratio
        if expense > 0:
            large_threshold = expense * 0.2  # 20% of total expense
            large_purchases = [t for t in expenses if t['amount'] >= large_threshold]
            large_purchase_ratio = sum(t['amount'] for t in large_purchases) / expense
        else:
            large_purchase_ratio = 0
        
        # Feature 5: Income stability (if we have income data)
        incomes = [t for t in transactions if t.get('type') == 'income']
        if len(incomes) > 1:
            income_values = [t['amount'] for t in incomes]
            income_mean = np.mean(income_values)
            income_stability = 1 - (np.std(income_values) / income_mean) if income_mean > 0 else 0
        else:
            income_stability = 0.5  # Neutral if insufficient data
        
        # Feature 6: Immediate spending score (spending on/after income receipt day)
        # This is a key indicator of spender behavior
        immediate_spending_score = self._calculate_immediate_spending(transactions, expenses)
        
        return {
            'expense_variance': expense_variance,
            'category_diversity': category_diversity,
            'impulse_score': impulse_score,
            'income_stability': income_stability,
            'large_purchase_ratio': large_purchase_ratio,
            'immediate_spending_score': immediate_spending_score,
            'savings_rate': savings_rate
        }
    
    def _calculate_immediate_spending(self, transactions: List[Dict], expenses: List[Dict]) -> float:
        """Calculate how much spending happens on the same day or within 3 days of receiving income"""
        if not expenses or not transactions:
            return 0.0
        
        # Get all income dates
        income_dates = []
        for t in transactions:
            if t.get('type') == 'income':
                try:
                    date_str = t['date']
                    if isinstance(date_str, str):
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        date = date_str if hasattr(date_str, 'date') else None
                    if date:
                        income_dates.append(date)
                except (ValueError, KeyError, TypeError):
                    continue
        
        if not income_dates:
            return 0.0
        
        # Calculate spending within 3 days of each income receipt
        immediate_spending_total = 0.0
        total_expense_amount = sum(t['amount'] for t in expenses)
        
        if total_expense_amount == 0:
            return 0.0
        
        for expense in expenses:
            try:
                date_str = expense['date']
                if isinstance(date_str, str):
                    expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    expense_date = date_str if hasattr(date_str, 'date') else None
                
                if not expense_date:
                    continue
                
                # Check if this expense is within 3 days of any income receipt
                for income_date in income_dates:
                    days_diff = (expense_date - income_date).days
                    # Same day (0) or within 3 days after income (1-3 days)
                    if 0 <= days_diff <= 3:
                        immediate_spending_total += expense['amount']
                        break  # Count each expense only once
            except (ValueError, KeyError, TypeError):
                continue
        
        # Return ratio of immediate spending to total expenses
        return immediate_spending_total / total_expense_amount if total_expense_amount > 0 else 0.0
    
    def _classify_personality(self, features: Dict, savings_rate: float) -> Tuple[str, float]:
        """ML classification using weighted features"""
        # Weighted scoring system (0-100 scale)
        saver_score = 0
        spender_score = 0
        
        # Feature 1: Savings rate (weight: 35%)
        # Negative savings rate = strong spender indicator
        if savings_rate < 0:
            spender_score += 35
        elif savings_rate >= self.saver_threshold:
            saver_score += 35
        elif savings_rate <= self.spender_threshold:
            spender_score += 35
        else:
            # Balanced range (5% to 20%)
            if savings_rate > 0.12:  # Closer to saver
                saver_score += 20
                spender_score += 15
            else:  # Closer to spender
                saver_score += 15
                spender_score += 20
        
        # Feature 2: Expense variance (weight: 20%)
        # High variance = inconsistent spending = spender behavior
        variance = features['expense_variance']
        if variance < 0.3:
            saver_score += 20  # Very consistent
        elif variance > 2.0:
            spender_score += 20  # Very inconsistent
        elif variance > 1.0:
            spender_score += 12
            saver_score += 8
        else:
            # Balanced variance
            saver_score += 10
            spender_score += 10
        
        # Feature 3: Impulse spending (weight: 20%)
        # High impulse score = spender behavior
        impulse = features['impulse_score']
        if impulse < 0.2:
            saver_score += 20  # Very low impulse
        elif impulse > 0.8:
            spender_score += 20  # Very high impulse
        elif impulse > 0.5:
            spender_score += 12
            saver_score += 8
        else:
            # Balanced impulse
            saver_score += 10
            spender_score += 10
        
        # Feature 4: Large purchase ratio (weight: 15%)
        # Very high ratio = planned purchases (saver), moderate = balanced
        large_ratio = features['large_purchase_ratio']
        if large_ratio > 0.7:
            saver_score += 15  # Mostly large planned purchases
        elif large_ratio < 0.2:
            spender_score += 15  # Many small purchases
        else:
            # Balanced
            saver_score += 7
            spender_score += 8
        
        # Feature 5: Income stability (weight: 10%)
        # High stability = saver-like behavior
        stability = features['income_stability']
        if stability > 0.8:
            saver_score += 10
        elif stability < 0.2:
            spender_score += 10
        else:
            # Balanced
            saver_score += 5
            spender_score += 5
        
        # Feature 6: Immediate spending (weight: 15%) - NEW KEY FEATURE
        # Spending on/within 3 days of receiving income = strong spender indicator
        immediate_spending = features.get('immediate_spending_score', 0)
        if immediate_spending > 0.6:
            spender_score += 15  # Strong spender behavior
        elif immediate_spending > 0.4:
            spender_score += 10
            saver_score += 5
        elif immediate_spending > 0.2:
            # Moderate immediate spending
            spender_score += 7
            saver_score += 8
        else:
            # Low immediate spending = saver behavior
            saver_score += 15
        
        # Determine personality with more balanced thresholds
        score_diff = saver_score - spender_score
        
        if score_diff > 15:
            personality = 'Saver'
            confidence = min(95, 50 + abs(score_diff))
        elif score_diff < -15:
            personality = 'Spender'
            confidence = min(95, 50 + abs(score_diff))
        else:
            personality = 'Balanced'
            confidence = max(60, 100 - abs(score_diff))
        
        return personality, confidence
    
    def _generate_traits(self, personality: str, features: Dict) -> List[str]:
        """Generate personality traits based on classification"""
        traits = []
        immediate_spending = features.get('immediate_spending_score', 0)
        
        if personality == 'Saver':
            traits.extend([
                'High savings rate',
                'Consistent spending patterns',
                'Planned purchases',
                'Financial discipline'
            ])
        elif personality == 'Spender':
            traits.extend([
                'Low savings rate',
                'Frequent small purchases',
                'Impulse buying tendencies',
                'Variable spending patterns'
            ])
        else:
            traits.extend([
                'Moderate savings rate',
                'Balanced spending approach',
                'Mix of planned and spontaneous purchases'
            ])
        
        # Immediate spending trait (key indicator)
        if immediate_spending > 0.6:
            traits.append(f'Strong immediate spending pattern ({immediate_spending*100:.0f}% of expenses within 3 days of income)')
        elif immediate_spending > 0.4:
            traits.append(f'Moderate immediate spending ({immediate_spending*100:.0f}% of expenses soon after income)')
        elif immediate_spending > 0.2:
            traits.append('Some tendency to spend after receiving income')
        else:
            traits.append('Good restraint - doesn\'t rush to spend after receiving income')
        
        # Add specific traits based on features
        if features['category_diversity'] > 0.5:
            traits.append('Diverse spending categories')
        
        if features['income_stability'] < 0.5:
            traits.append('Irregular income pattern')
        
        if features['impulse_score'] > 0.6:
            traits.append('High frequency of small/impulse purchases')
        
        if features['expense_variance'] > 1.5:
            traits.append('Highly inconsistent daily spending')
        elif features['expense_variance'] < 0.3:
            traits.append('Very consistent daily spending')
        
        return traits
    
    def _generate_recommendations(self, personality: str, features: Dict) -> List[str]:
        """Generate personalized, actionable recommendations"""
        recommendations = []
        immediate_spending = features.get('immediate_spending_score', 0)
        
        # Immediate spending recommendations (highest priority)
        if immediate_spending > 0.6:
            recommendations.extend([
                '🚨 CRITICAL: You\'re spending ' + f'{immediate_spending*100:.0f}%' + ' of your expenses within 3 days of receiving income. This is a strong spender pattern.',
                '✅ ACTION: Implement a "48-hour rule" - wait 48 hours before spending any money after receiving income',
                '✅ ACTION: Set up automatic savings transfer (20-30% of income) on the day you receive money, before you can spend it',
                '✅ ACTION: Create a "spending buffer" - only allow yourself to spend from previous month\'s savings, not current income'
            ])
        elif immediate_spending > 0.4:
            recommendations.extend([
                '⚠️ You tend to spend ' + f'{immediate_spending*100:.0f}%' + ' of expenses soon after receiving income',
                '✅ ACTION: Delay non-essential purchases by at least 1 week after receiving income',
                '✅ ACTION: Automatically transfer 15-20% to savings immediately when income arrives',
                '✅ ACTION: Create a monthly budget and stick to it, regardless of when income arrives'
            ])
        elif immediate_spending > 0.2:
            recommendations.append('💡 Consider waiting a few days after receiving income before making purchases to build better spending discipline')
        else:
            recommendations.append('✅ Great! You don\'t rush to spend immediately after receiving income - this is a saver trait')
        
        # Personality-based recommendations
        if personality == 'Saver':
            recommendations.extend([
                '✅ Continue maintaining your excellent savings habits',
                '💡 Consider investing your surplus funds for long-term growth',
                '💡 Review your budget periodically to optimize further',
                '💡 Set up an emergency fund if you haven\'t already (3-6 months of expenses)'
            ])
        elif personality == 'Spender':
            recommendations.extend([
                '🚨 Set up automatic savings transfers (start with 10%, increase gradually)',
                '🚨 Create a strict budget for discretionary spending and track it daily',
                '🚨 Implement the "24-hour rule" - wait 24 hours before any non-essential purchase',
                '🚨 Track every expense to increase awareness of where your money goes',
                '🚨 Use the envelope method: allocate cash for different categories and don\'t exceed limits',
                '🚨 Unsubscribe from shopping emails and remove shopping apps to reduce temptation'
            ])
        else:
            recommendations.extend([
                '💡 Aim to increase your savings rate gradually (target: 20% of income)',
                '💡 Set specific financial goals with deadlines',
                '💡 Review your largest expense categories monthly and look for savings opportunities',
                '💡 Build an emergency fund covering 3 months of expenses'
            ])
        
        # Feature-based specific recommendations
        if features['impulse_score'] > 0.6:
            recommendations.extend([
                '🚨 High impulse spending detected (' + f'{features["impulse_score"]*100:.0f}%' + ' of purchases are small/impulsive)',
                '✅ ACTION: Create a shopping list before going shopping and stick to it',
                '✅ ACTION: Use cash for discretionary spending to feel the money leaving your hands',
                '✅ ACTION: Delete saved payment methods from online stores to add friction'
            ])
        elif features['impulse_score'] > 0.4:
            recommendations.append('💡 Reduce impulse purchases by implementing a "wish list" - add items and review after 1 week')
        
        if features['expense_variance'] > 1.0:
            recommendations.extend([
                '⚠️ Your spending is highly inconsistent (variance: ' + f'{features["expense_variance"]:.2f}' + ')',
                '✅ ACTION: Create a daily spending limit and track it',
                '✅ ACTION: Use a budgeting app to monitor spending in real-time',
                '✅ ACTION: Plan your expenses for the week ahead every Sunday'
            ])
        
        if features['large_purchase_ratio'] > 0.5:
            recommendations.extend([
                '💡 You make many large purchases (' + f'{features["large_purchase_ratio"]*100:.0f}%' + ' of expenses)',
                '✅ ACTION: Plan large purchases in advance and save specifically for them',
                '✅ ACTION: Research and compare prices before making large purchases',
                '✅ ACTION: Wait 2 weeks before making any purchase over ₹5000'
            ])
        
        # Savings rate specific recommendations
        savings_rate = features.get('savings_rate', 0)
        if savings_rate < 0:
            recommendations.extend([
                '🚨 CRITICAL: You\'re spending more than you earn! Immediate action required.',
                '✅ ACTION: Cut non-essential expenses by 30% immediately',
                '✅ ACTION: Find ways to increase income or reduce expenses to break even',
                '✅ ACTION: Create a strict survival budget with only essential expenses'
            ])
        elif savings_rate < 0.05:
            recommendations.extend([
                '⚠️ Your savings rate is very low (' + f'{savings_rate*100:.1f}%' + '). Aim for at least 10%.',
                '✅ ACTION: Identify your top 3 expense categories and reduce each by 20%',
                '✅ ACTION: Set up automatic savings of ₹500-1000 per month to start building the habit'
            ])
        elif savings_rate < 0.10:
            recommendations.append('💡 Increase your savings rate from ' + f'{savings_rate*100:.1f}%' + ' to 15-20% by reducing discretionary spending')
        
        return recommendations


class SurvivalDaysPredictor:
    """ML model to predict survival days based on spending patterns"""
    
    def predict(self, transactions: List[Dict], current_balance: float) -> Dict:
        """Predict how many days the balance can last"""
        if current_balance <= 0:
            return {
                'survival_days': None,
                'status': 'critical',
                'message': 'Your balance is negative or zero. Immediate action needed!',
                'current_balance': current_balance,
                'average_daily_expense': 0
            }
        
        # Get expenses from last 30 days
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_expenses = []
        for t in transactions:
            if t.get('type') == 'expense':
                try:
                    date_str = t['date']
                    if isinstance(date_str, str):
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        date = date_str if hasattr(date_str, 'date') else datetime.now().date()
                    if date >= thirty_days_ago:
                        recent_expenses.append(t)
                except (ValueError, KeyError, TypeError):
                    continue
        
        if not recent_expenses:
            return {
                'survival_days': None,
                'status': 'unknown',
                'message': 'Insufficient expense data. Start tracking your expenses!',
                'current_balance': current_balance,
                'average_daily_expense': 0
            }
        
        # Calculate average daily expense with ML smoothing
        total_expense = sum(t['amount'] for t in recent_expenses)
        days_with_expenses = len(set(
            datetime.strptime(t['date'], '%Y-%m-%d').date() 
            for t in recent_expenses
        ))
        
        # Use weighted average (recent days weighted more)
        if days_with_expenses > 0:
            # Simple average
            avg_daily = total_expense / max(days_with_expenses, 1)
            
            # Apply exponential smoothing for better prediction
            recent_7_days = []
            seven_days_ago = datetime.now().date() - timedelta(days=7)
            for t in recent_expenses:
                try:
                    date_str = t['date']
                    if isinstance(date_str, str):
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        date = date_str if hasattr(date_str, 'date') else datetime.now().date()
                    if date >= seven_days_ago:
                        recent_7_days.append(t)
                except (ValueError, KeyError, TypeError):
                    continue
            if recent_7_days:
                recent_avg = sum(t['amount'] for t in recent_7_days) / 7
                # Weighted: 70% recent, 30% overall
                avg_daily = 0.7 * recent_avg + 0.3 * avg_daily
        else:
            avg_daily = total_expense / 30
        
        if avg_daily <= 0:
            return {
                'survival_days': None,
                'status': 'safe',
                'message': 'No expenses detected. Your balance is safe!',
                'current_balance': current_balance,
                'average_daily_expense': 0
            }
        
        # Predict survival days
        survival_days = math.floor(current_balance / avg_daily)
        
        # Determine status
        if survival_days < 7:
            status = 'critical'
            message = f'⚠️ Critical: Your balance will last only {survival_days} days!'
        elif survival_days < 14:
            status = 'warning'
            message = f'⚠️ Warning: Your balance will last {survival_days} days'
        elif survival_days < 30:
            status = 'moderate'
            message = f'✓ Moderate: Your balance will last {survival_days} days'
        else:
            status = 'safe'
            message = f'✓ Safe: Your balance will last {survival_days} days'
        
        return {
            'survival_days': survival_days,
            'status': status,
            'message': message,
            'current_balance': current_balance,
            'average_daily_expense': avg_daily
        }


class SmartRecommendationsEngine:
    """ML-powered recommendation system"""
    
    def generate(self, transactions: List[Dict], total_income: float, total_expense: float, goals: List[Dict]) -> List[Dict]:
        """Generate smart recommendations using ML analysis"""
        recommendations = []
        
        if not transactions:
            return [{
                'type': 'info',
                'title': 'Get Started',
                'message': 'Start tracking your income and expenses to get personalized recommendations.',
                'action': 'Add your first transaction'
            }]
        
        # Analyze spending patterns
        expenses = [t for t in transactions if t.get('type') == 'expense']
        categories = defaultdict(float)
        for t in expenses:
            categories[t.get('category', 'Other')] += t['amount']
        
        # Recommendation 1: Savings rate analysis
        if total_income > 0:
            savings_rate = (total_income - total_expense) / total_income
            if savings_rate < 0.1:
                recommendations.append({
                    'type': 'critical',
                    'title': 'Low Savings Rate',
                    'message': f'Your savings rate is only {savings_rate*100:.1f}%. Aim for at least 20% to build financial security.',
                    'action': 'Review your expenses and identify areas to cut back'
                })
            elif savings_rate < 0.2:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Improve Savings Rate',
                    'message': f'Your savings rate is {savings_rate*100:.1f}%. Try to increase it to 20% or more.',
                    'action': 'Set up automatic savings transfers'
                })
            elif savings_rate >= 0.2:
                recommendations.append({
                    'type': 'tip',
                    'title': 'Excellent Savings!',
                    'message': f'Great job! Your savings rate is {savings_rate*100:.1f}%. Keep it up!',
                    'action': 'Consider investing your surplus funds'
                })
        
        # Recommendation 2: Top spending category
        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            top_percentage = (top_category[1] / total_expense * 100) if total_expense > 0 else 0
            
            if top_percentage > 40:
                recommendations.append({
                    'type': 'warning',
                    'title': 'High Category Concentration',
                    'message': f'You\'re spending {top_percentage:.1f}% of your expenses on {top_category[0]}. Consider diversifying.',
                    'action': f'Review {top_category[0]} expenses and look for savings opportunities'
                })
        
        # Recommendation 3: Expense consistency
        if len(expenses) > 7:
            daily_expenses = defaultdict(float)
            for t in expenses:
                try:
                    date_str = t['date']
                    if isinstance(date_str, str):
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        date = date_str if hasattr(date_str, 'date') else datetime.now().date()
                    daily_expenses[date] += t['amount']
                except (ValueError, KeyError, TypeError):
                    continue
            
            if daily_expenses:
                expense_values = list(daily_expenses.values())
                variance = np.var(expense_values) / (np.mean(expense_values) ** 2) if np.mean(expense_values) > 0 else 0
                
                if variance > 1.5:
                    recommendations.append({
                        'type': 'info',
                        'title': 'Inconsistent Spending',
                        'message': 'Your daily spending varies significantly. Try to maintain more consistent spending patterns.',
                        'action': 'Create a daily spending budget and track it'
                    })
        
        # Recommendation 4: Goals progress
        if goals:
            active_goals = [g for g in goals if g.get('current_amount', 0) < g.get('target_amount', 0)]
            if active_goals:
                progress_avg = np.mean([
                    (g.get('current_amount', 0) / g.get('target_amount', 1) * 100)
                    for g in active_goals
                ])
                
                if progress_avg < 30:
                    recommendations.append({
                        'type': 'warning',
                        'title': 'Low Goal Progress',
                        'message': f'Your financial goals are only {progress_avg:.1f}% complete on average.',
                        'action': 'Increase your savings allocation towards goals'
                    })
        else:
            recommendations.append({
                'type': 'info',
                'title': 'Set Financial Goals',
                'message': 'Setting financial goals helps you stay motivated and track progress.',
                'action': 'Create a financial goal in the Goals section'
            })
        
        # Recommendation 5: Large purchases
        if total_expense > 0:
            large_threshold = total_expense * 0.15
            large_purchases = [t for t in expenses if t['amount'] >= large_threshold]
            if large_purchases:
                recommendations.append({
                    'type': 'tip',
                    'title': 'Large Purchases Detected',
                    'message': f'You have {len(large_purchases)} large purchase(s). Plan these in advance.',
                    'action': 'Create a savings goal for large purchases'
                })
        
        return recommendations if recommendations else [{
            'type': 'info',
            'title': 'Keep Tracking',
            'message': 'Continue tracking your expenses to get more personalized recommendations.',
            'action': 'Add more transactions'
        }]

