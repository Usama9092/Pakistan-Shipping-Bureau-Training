from __future__ import annotations
from typing import Any
import streamlit as st
from .design_system import apply_global_css

def psb_page_header(title: str, subtitle: str = "", *, role: str = "") -> None:
    apply_global_css()
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    if role:
        st.caption(f"Role: {role}")

def psb_metric_card(label: str, value: Any, help_text: str = "") -> None:
    st.metric(label, value, help=help_text or None)

def psb_status_badge(status: str) -> None:
    st.markdown(f"**Status:** `{status}`")

def psb_empty_state(message: str, action_label: str | None = None) -> bool:
    st.info(message)
    return bool(action_label and st.button(action_label))

def psb_error_state(message: str, reference_id: str = "") -> None:
    suffix = f" Reference: `{reference_id}`" if reference_id else ""
    st.error(message + suffix)
