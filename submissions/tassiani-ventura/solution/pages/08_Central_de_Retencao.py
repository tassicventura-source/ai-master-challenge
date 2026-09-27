import streamlit as st

from src.ui import setup_page
from src.retention_ui import render_retention_central

setup_page(st, "Central de Retenção")
render_retention_central()
