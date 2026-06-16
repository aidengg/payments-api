from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import sqlite3

def get_db():
    conn = sqlite3.connect('payments.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
                 create table if not exists accounts (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     owner_name TEXT NOT NULL,
                     currency TEXT NOT NULL,
                     balance REAL NOT NULL DEFAULT 0,
                     created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
""")
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS transactions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 from_account INTEGER NOT NULL,
                 to_account INTEGER NOT NULL,
                 amount REAL NOT NULL, 
                 status TEXT NOT NULL DEFAULT 'completed',
                 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
                 """)
    conn.commit()
    conn.close()

init_db()
class TransactionCreate(BaseModel):
    from_account: int
    to_account: int
    amount: float 
class AccountCreate(BaseModel):
    owner_name: str
    currency: str

app = FastAPI()

@app.get("/health")

def health():
    return {"status": "ok"}

@app.post("/accounts")

def create_account(account: AccountCreate):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO accounts (owner_name, currency) VALUES (?,?) ",
        (account.owner_name, account.currency),
    )
    conn.commit()
    new_id= cursor.lastrowid
    conn.close()
    return {
            "id": new_id,
            "owner_name": account.owner_name,
            "currency": account.currency,
        }

@app.get("/accounts")
def list_accounts():
    conn =get_db()
    rows = conn.execute("SELECT * FROM accounts").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/accounts/{account_id}")
def get_account(account_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM accounts WHERE id = ?",
            (account_id,),
        ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail= "Account not found")
    return dict(row)

@app.post("/transactions")

def create_transaction(txn: TransactionCreate):
    conn = get_db()

    if txn.amount <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")
    sender = conn.execute(
        "SELECT * FROM accounts WHERE id = ?", (txn.from_account,)
    ).fetchone()
    receiver = conn.execute(
        "SELECT * FROM accounts WHERE id = ?" , (txn.to_account,)
    ).fetchone()
    
    if sender is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Sender account not found")
    if receiver is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Receiver account not found")
    if sender["Balance"]< txn.amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient funds in sender account")
    
    conn.execute(
        "UPDATE accounts SET balance = balance - ? WHERE id= ?", (txn.amount, txn.from_account)
    )
    conn.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id= ?", (txn.amount, txn.to_account)
    )

    cursor =conn.execute(
        "INSERT INTO transactions (from_account, to_account, amount) VALUES (?,?,?)", (txn.from_account, txn.to_account, txn.amount)
    )

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {
        "id": new_id,
        "from_account":txn.from_account,
        "to_account": txn.to_account,
        "amount": txn.amount,
        "status": "completed",
    }