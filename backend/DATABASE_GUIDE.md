# FinFit Database Guide

## Database Location & Type

- **Type:** SQLite 3
- **File:** `backend/database.db` (created when you first run the app)
- **Full path:** `FinFit_Project - Copy - Copy/backend/database.db`

---

## Schema Overview

FinFit uses **5 tables** with the following relationships:

```
User (1) ─────┬───── (*) Transaction
              ├───── (*) Goal
              ├───── (1) GmailConnection
              └───── (*) PaymentRequest
Transaction (1) ───── (*) PaymentRequest (optional link)
```

---

## Table Schemas

### 1. **user**
| Column         | Type         | Constraints                    | Description                    |
|----------------|--------------|--------------------------------|--------------------------------|
| id             | INTEGER      | PRIMARY KEY                    | Auto-increment user ID         |
| email          | VARCHAR(100) | UNIQUE, NOT NULL               | Login email                    |
| name           | VARCHAR(100) |                                | Display name                   |
| password_hash  | VARCHAR(255) | NOT NULL                       | Hashed password (Werkzeug)     |
| created_at     | VARCHAR(20)  |                                | e.g. '2026-02-06'              |

**Relations:** One user has many transactions, goals, payment_requests; one user has at most one gmail_connection.

---

### 2. **transaction**
| Column   | Type        | Constraints     | Description                    |
|----------|-------------|-----------------|--------------------------------|
| id       | INTEGER     | PRIMARY KEY     | Auto-increment transaction ID  |
| user_id  | INTEGER     | NOT NULL, FK→user.id | Owner of this transaction  |
| type     | VARCHAR(10) |                 | 'income' or 'expense'          |
| category | VARCHAR(50) |                 | e.g. 'Food', 'Payment Received - Name' |
| amount   | FLOAT       |                 | Amount (e.g. 10000.00)         |
| date     | VARCHAR(20) |                 | Date string 'YYYY-MM-DD'      |
| note     | VARCHAR(200)|                 | Optional note                  |

**Relations:** Many transactions belong to one user.

---

### 3. **goal**
| Column         | Type        | Constraints     | Description                    |
|----------------|-------------|-----------------|--------------------------------|
| id             | INTEGER     | PRIMARY KEY     | Auto-increment goal ID         |
| user_id        | INTEGER     | NOT NULL, FK→user.id | Owner of this goal        |
| name           | VARCHAR(50) |                 | Goal name                      |
| target_amount  | FLOAT       |                 | Target amount (₹)              |
| current_amount | FLOAT       |                 | Current saved amount           |
| deadline       | VARCHAR(20) |                 | e.g. '2026-12-31'              |

**Relations:** Many goals belong to one user.

---

### 4. **gmail_connection**
| Column        | Type        | Constraints        | Description                    |
|---------------|-------------|--------------------|--------------------------------|
| id            | INTEGER     | PRIMARY KEY        | Auto-increment ID              |
| user_id       | INTEGER     | UNIQUE, NOT NULL, FK→user.id | One Gmail per user   |
| access_token  | TEXT        |                    | OAuth access token             |
| refresh_token | TEXT        |                    | OAuth refresh token            |
| token_expiry  | VARCHAR(20) |                    | Token expiry timestamp         |
| connected_at  | VARCHAR(20) |                    | When Gmail was connected       |
| last_sync_at  | VARCHAR(20) |                    | Last email sync time           |
| is_active     | BOOLEAN     | default True       | Whether connection is active   |

**Relations:** One row per user for Gmail OAuth.

---

### 5. **payment_request**
| Column         | Type        | Constraints           | Description                    |
|----------------|-------------|------------------------|--------------------------------|
| id             | INTEGER     | PRIMARY KEY           | Auto-increment ID              |
| merchant_id    | INTEGER     | NOT NULL, FK→user.id  | User who created the request   |
| amount         | FLOAT       | NOT NULL              | Requested amount               |
| description    | VARCHAR(200)|                        | Description                    |
| upi_id         | VARCHAR(100)|                        | Merchant UPI ID                 |
| status         | VARCHAR(20) | default 'PENDING'     | PENDING, PAID, EXPIRED, CANCELLED |
| token          | VARCHAR(100)| UNIQUE, NOT NULL       | Tracking token                 |
| created_at     | VARCHAR(20) |                        | Creation time                  |
| paid_at        | VARCHAR(20) |                        | When paid (if paid)            |
| payer_email    | VARCHAR(100)|                        | Payer email                    |
| transaction_id | INTEGER     | FK→transaction.id, nullable | Linked FinFit transaction |

**Relations:** Many payment_requests per user (merchant); optional link to one transaction.

---

## How to View the Database

### Option 1: Command line (sqlite3)

If you have SQLite installed:

```bash
# Navigate to project folder, then:
cd backend
sqlite3 database.db
```

Inside the SQLite shell:

```sql
-- List tables
.tables

-- View schema of a table
.schema user
.schema transaction

-- Query examples
SELECT * FROM user;
SELECT id, type, category, amount, date FROM transaction ORDER BY date DESC LIMIT 10;
SELECT * FROM goal;

-- Exit
.quit
```

**Windows:** Install SQLite from https://www.sqlite.org/download.html or use `winget install SQLite.SQLite`  
**Mac:** `brew install sqlite3`  
**Linux:** `sudo apt install sqlite3` (Ubuntu/Debian)

---

### Option 2: GUI tools

- **DB Browser for SQLite** (free): https://sqlitebrowser.org/  
  - Open → select `backend/database.db`  
  - Browse tables, run SQL, export data  

- **DBeaver** (free): https://dbeaver.io/  
  - New connection → SQLite → choose `database.db`  

- **VS Code / Cursor:** Install extension “SQLite Viewer” or “SQLite” and open `database.db`.

---

### Option 3: Python script (from project)

Run this from the **backend** folder (so it finds `database.db` and your app):

```bash
cd backend
python view_database.py
```

(You’ll create `view_database.py` next.)

---

## How to Access Programmatically

### From Python (same app – Flask/SQLAlchemy)

```python
from app import app
from models import db, User, Transaction, Goal, GmailConnection, PaymentRequest

with app.app_context():
    # All users
    users = User.query.all()
    
    # One user by email
    user = User.query.filter_by(email='someone@example.com').first()
    
    # User's transactions
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
    
    # User's goals
    goals = Goal.query.filter_by(user_id=user.id).all()
```

### From Python (standalone script, no Flask app)

```python
import sqlite3

conn = sqlite3.connect('database.db')  # run from backend/ folder
conn.row_factory = sqlite3.Row  # access columns by name
cur = conn.cursor()

cur.execute("SELECT * FROM user")
users = cur.fetchall()

cur.execute("SELECT * FROM transaction ORDER BY date DESC")
transactions = cur.fetchall()

conn.close()
```

---

## Quick Reference: Useful SQL

```sql
-- Count users
SELECT COUNT(*) FROM user;

-- All transactions for a user (replace 1 with user id)
SELECT * FROM transaction WHERE user_id = 1 ORDER BY date DESC;

-- Total income and expense per user
SELECT user_id,
       SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS total_income,
       SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS total_expense
FROM transaction
GROUP BY user_id;

-- Recent transactions with user email
SELECT t.id, u.email, t.type, t.category, t.amount, t.date
FROM transaction t
JOIN user u ON t.user_id = u.id
ORDER BY t.date DESC
LIMIT 20;
```

---

## Summary

| Item        | Value                                      |
|------------|---------------------------------------------|
| Database   | SQLite 3                                   |
| File       | `backend/database.db`                       |
| ORM        | Flask-SQLAlchemy                           |
| Models     | `backend/models.py`                        |
| Tables     | user, transaction, goal, gmail_connection, payment_request |
| Create DB  | Run app once; `db.create_all()` in `app.py` creates tables |
