from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
import mimetypes
import smtplib
from typing import Iterable

from .config import (
    MAIL_BCC,
    MAIL_CC,
    MAIL_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)


def _split_addresses(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_addresses(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return _split_addresses(value)
    return [str(item).strip() for item in value if str(item).strip()]


def can_send_email() -> bool:
    return all([
        SMTP_HOST,
        SMTP_PORT,
        SMTP_USER,
        SMTP_PASSWORD,
        MAIL_FROM,
    ])


def build_final_email_payload(
    *,
    asunto_base: str,
    mensaje_base: str,
    fecha_texto: str,
) -> tuple[str, str]:
    subject = f"{asunto_base} | {fecha_texto}"

    body = f"""{mensaje_base.strip()}

Fecha del envío: {fecha_texto}

Se adjunta el archivo Excel con los pedidos semanales de huevo.
"""
    return subject, body


def _attach_file(msg: EmailMessage, attachment_path: Path) -> None:
    if not attachment_path.exists():
        raise FileNotFoundError(f"No encontré el archivo adjunto: {attachment_path}")

    mime_type, _ = mimetypes.guess_type(str(attachment_path))
    if mime_type:
        maintype, subtype = mime_type.split("/", 1)
    else:
        maintype, subtype = "application", "octet-stream"

    with attachment_path.open("rb") as f:
        msg.add_attachment(
            f.read(),
            maintype=maintype,
            subtype=subtype,
            filename=attachment_path.name,
        )


def send_email_with_attachment(
    *,
    to_emails: str | Iterable[str],
    subject: str,
    body: str,
    attachment_path: str | Path,
    cc_emails: str | Iterable[str] | None = None,
    bcc_emails: str | Iterable[str] | None = None,
) -> None:
    if not can_send_email():
        raise RuntimeError("SMTP no configurado. Revisa tu archivo .env.")

    attachment_path = Path(attachment_path)

    to_list = _normalize_addresses(to_emails)
    cc_list = _normalize_addresses(cc_emails)
    bcc_list = _normalize_addresses(bcc_emails)

    env_cc = _split_addresses(MAIL_CC)
    env_bcc = _split_addresses(MAIL_BCC)

    if env_cc:
        cc_list = cc_list + [x for x in env_cc if x not in cc_list]

    if env_bcc:
        bcc_list = bcc_list + [x for x in env_bcc if x not in bcc_list]

    if not to_list:
        raise ValueError("Debes indicar al menos un destinatario principal.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = ", ".join(to_list)

    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    msg.set_content(body)
    _attach_file(msg, attachment_path)

    all_recipients = to_list + cc_list + bcc_list

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(
            msg,
            from_addr=MAIL_FROM,
            to_addrs=all_recipients,
        )