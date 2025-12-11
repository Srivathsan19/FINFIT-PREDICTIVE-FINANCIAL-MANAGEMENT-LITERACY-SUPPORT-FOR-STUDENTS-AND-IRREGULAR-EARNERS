# Analytics Module - ML-Powered Features

## Overview
The analytics section has been refactored into a modular structure with machine learning-powered features.

## Structure

```
backend/
├── routes/
│   └── analytics.py          # API endpoints for analytics
├── ml/
│   └── analytics_ml.py       # ML models and algorithms
├── utils/
│   └── helpers.py            # Helper functions
└── app.py                    # Main application (registers blueprints)
```

## Features

### 1. Spender Personality Test (`/api/personality-test`)
- **ML Model**: PersonalityClassifier
- **Features Analyzed**:
  - Savings rate
  - Expense consistency (variance)
  - Category diversity
  - Impulse spending patterns
  - Income stability
- **Output**: Personality type (Saver/Balanced/Spender) with confidence score, traits, and recommendations

### 2. Survival Days Calculator (`/api/survival-days`)
- **ML Model**: SurvivalDaysPredictor
- **Algorithm**: Exponential smoothing for expense prediction
- **Features**:
  - Analyzes last 30 days of expenses
  - Weighted average (70% recent 7 days, 30% overall)
  - Status classification (critical/warning/moderate/safe)
- **Output**: Number of days balance will last, status, and average daily expense

### 3. Daily Target Calculator (`/api/daily-target`)
- **Purpose**: For irregular income earners
- **Input**: Monthly expenses, savings goal, working days
- **Output**: Daily, weekly, and monthly earning targets with breakdown

### 4. Smart Recommendations (`/api/recommendations`)
- **ML Model**: SmartRecommendationsEngine
- **Analysis**:
  - Savings rate analysis
  - Top spending category detection
  - Expense consistency
  - Goal progress tracking
  - Large purchase patterns
- **Output**: Personalized recommendations with priority levels (critical/warning/info/tip)

## ML Algorithms Used

1. **Weighted Feature Scoring**: For personality classification
2. **Exponential Smoothing**: For expense prediction
3. **Statistical Analysis**: Variance, entropy, and pattern detection
4. **Rule-Based Recommendations**: Context-aware suggestions

## Installation

Install required packages:
```bash
pip install -r requirements.txt
```

Required packages:
- Flask
- Flask-SQLAlchemy
- numpy (for ML calculations)
- Other dependencies as listed in requirements.txt

## Usage

All endpoints require authentication. The analytics blueprint is automatically registered in `app.py`.

## Testing

Test each endpoint:
- GET `/api/personality-test`
- GET `/api/survival-days`
- POST `/api/daily-target` (with JSON body)
- GET `/api/recommendations`

