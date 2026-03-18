from __future__ import annotations

from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CATALOGOS_DIR = DATA_DIR / "catalogos"
OUTPUT_DIR = DATA_DIR / "output"
TEMPLATES_DIR = DATA_DIR / "templates"

COLABORADORES_FILE = CATALOGOS_DIR / "colaboradores.json"
DESTINATARIOS_FILE = CATALOGOS_DIR / "destinatarios.json"
TIPOS_FILE = CATALOGOS_DIR / "tipos_pedido.json"
PEDIDOS_XLSX = OUTPUT_DIR / "pedidos_registrados.xlsx"

load_dotenv(BASE_DIR / ".env")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() == "true"
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER)
MAIL_CC = os.getenv("MAIL_CC", "")
MAIL_BCC = os.getenv("MAIL_BCC", "")