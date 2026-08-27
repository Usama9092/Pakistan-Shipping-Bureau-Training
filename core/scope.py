"""Compatibility facade for the single PSB access-policy engine.

All scope logic lives in core.access_policy. This module exists only so legacy
imports continue to work without creating a second scope implementation.
"""
from __future__ import annotations
from .access_policy import allowed_user_ids, filter_frame

def restrict_user_frame(frame, actor, db_all, user_col='user_id'):
    users=db_all('users')
    uds=db_all('user_departments')
    return filter_frame(frame, actor, users, uds)
