"""Central database gateway for PSB.
All SQL connections and raw execution live here; business pages use the repository facade.
"""
from __future__ import annotations
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL','')
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE','5'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW','10'))
DB_STATEMENT_TIMEOUT_MS = int(os.getenv('DB_STATEMENT_TIMEOUT_MS','15000'))

@st.cache_resource
def get_engine():
    url = DATABASE_URL
    if url.startswith('postgres://'):
        url = url.replace('postgres://','postgresql+psycopg2://',1)
    elif url.startswith('postgresql://'):
        url = url.replace('postgresql://','postgresql+psycopg2://',1)
    if url.startswith('sqlite'):
        return create_engine(url, pool_pre_ping=True, connect_args={'check_same_thread':False})
    return create_engine(url, pool_pre_ping=True, pool_size=DB_POOL_SIZE, max_overflow=DB_MAX_OVERFLOW, pool_recycle=1800, pool_timeout=15, connect_args={'options': f'-c statement_timeout={DB_STATEMENT_TIMEOUT_MS}'})

def exec_sql(sql: str, params: dict | None = None) -> None:
    with get_engine().begin() as conn:
        conn.execute(text(sql), params or {})

def query_sql(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().begin() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})
