"""Tiny stdlib SMTP helper. Sends transactional email when SMTP_HOST is configured;
otherwise returns False so callers can fall back to admin alerts.

Configuration via env (all optional except SMTP_HOST):
  SMTP_HOST       — e.g. smtp.gmail.com
  SMTP_PORT       — default 587 (STARTTLS); use 465 for implicit SSL
  SMTP_USER       — auth username (often the from-address)
  SMTP_PASSWORD   — auth password / app-password
  SMTP_FROM       — From: header (default = SMTP_USER)
  SMTP_FROM_NAME  — display name (default "Servia")
  SMTP_USE_SSL    — "1" for implicit SSL on port 465; default STARTTLS on 587

Designed so the rest of the app can call mail.send(...) without caring which
provider we end up using (Gmail SMTP / Postmark SMTP / SES SMTP all just work).
"""
from __future__ import annotations
import os, smtplib, ssl, logging
from email.message import EmailMessage

log = logging.getLogger("servia.mail")


def configured() -> bool:
    return bool(os.getenv("SMTP_HOST"))


def send(to: str, subject: str, body_text: str, body_html: str | None = None) -> bool:
    """Returns True if accepted by the SMTP server, False otherwise (no exception)."""
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        return False
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    pw = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", user) or user
    from_name = os.getenv("SMTP_FROM_NAME", "Servia")
    use_ssl = os.getenv("SMTP_USE_SSL", "0") == "1" or port == 465

    if not from_addr or not to:
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        ctx = ssl.create_default_context()
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=10) as s:
                if user: s.login(user, pw)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as s:
                s.ehlo()
                try: s.starttls(context=ctx); s.ehlo()
                except smtplib.SMTPException: pass  # plain submission allowed
                if user: s.login(user, pw)
                s.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("mail.send failed (host=%s to=%s): %s", host, to, e)
        return False
