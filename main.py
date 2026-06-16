from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

def get_db():
    conn = sqlite3.connect('accounts.db')
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
    conn.commit()
    conn.close()

init_db()

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