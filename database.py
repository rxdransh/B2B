"""Small SQLite data layer for the CRM."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3

import pandas as pd

from seed_data import generate_sample_leads


DB_PATH = Path(__file__).with_name("crm.db")


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(seed: bool = True) -> None:
    """Create the database and insert demo rows only when it is empty."""
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                company TEXT NOT NULL,
                industry TEXT NOT NULL,
                job_title TEXT NOT NULL,
                company_size INTEGER NOT NULL CHECK(company_size >= 0),
                lead_source TEXT NOT NULL,
                budget REAL NOT NULL CHECK(budget >= 0),
                lead_score INTEGER NOT NULL CHECK(lead_score BETWEEN 0 AND 100),
                temperature TEXT NOT NULL CHECK(temperature IN ('Hot', 'Warm', 'Cold')),
                gtm_stage TEXT NOT NULL,
                sales_stage TEXT NOT NULL,
                deal_value REAL NOT NULL CHECK(deal_value >= 0),
                last_contacted TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        if seed and count == 0:
            rows = generate_sample_leads(50)
            conn.executemany(
                """
                INSERT INTO leads (
                    name, email, phone, company, industry, job_title, company_size,
                    lead_source, budget, lead_score, temperature, gtm_stage,
                    sales_stage, deal_value, last_contacted, created_at
                ) VALUES (
                    :name, :email, :phone, :company, :industry, :job_title, :company_size,
                    :lead_source, :budget, :lead_score, :temperature, :gtm_stage,
                    :sales_stage, :deal_value, :last_contacted, :created_at
                )
                """,
                rows,
            )


def get_leads() -> pd.DataFrame:
    with connection() as conn:
        return pd.read_sql_query("SELECT * FROM leads ORDER BY id DESC", conn)


def get_lead(lead_id: int):
    with connection() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None


def add_lead(lead: dict) -> int:
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO leads (
                name, email, phone, company, industry, job_title, company_size,
                lead_source, budget, lead_score, temperature, gtm_stage,
                sales_stage, deal_value, last_contacted, created_at
            ) VALUES (
                :name, :email, :phone, :company, :industry, :job_title, :company_size,
                :lead_source, :budget, :lead_score, :temperature, :gtm_stage,
                :sales_stage, :deal_value, :last_contacted, :created_at
            )
            """,
            lead,
        )
        return int(cursor.lastrowid)


def update_lead_stages(lead_id: int, gtm_stage: str, sales_stage: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE leads SET gtm_stage = ?, sales_stage = ? WHERE id = ?",
            (gtm_stage, sales_stage, lead_id),
        )


def mark_contacted(lead_id: int, contacted_date: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE leads SET last_contacted = ? WHERE id = ?",
            (contacted_date, lead_id),
        )

