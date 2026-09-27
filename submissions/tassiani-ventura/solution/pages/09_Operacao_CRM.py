import streamlit as st

from src.crm_ui import render_crm_workspace
from src.ui import setup_page

setup_page(st, "CRM e operação comercial")
render_crm_workspace()
