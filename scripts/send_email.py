#!/usr/bin/env python3
"""Send email with optional attachments via SMTP.

Usage:
    python3 send_email.py --to "user@example.com" --subject "Subject" --body "Body text" \
        [--attachments file1.pdf file2.pdf] [--html]

Environment variables (or pass via args):
    SMTP_HOST     - SMTP server (default: smtp.gmail.com)
    SMTP_PORT     - SMTP port (default: 587)
    SMTP_USER     - SMTP username/email
    SMTP_PASS     - SMTP password or app password
    SMTP_FROM     - From address (defaults to SMTP_USER)
"""

import argparse
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


def send_email(to: str, subject: str, body: str, attachments: list = None,
               html: bool = False, smtp_host: str = None, smtp_port: int = None,
               smtp_user: str = None, smtp_pass: str = None, from_addr: str = None):
    smtp_host = smtp_host or os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = smtp_user or os.environ.get("SMTP_USER")
    smtp_pass = smtp_pass or os.environ.get("SMTP_PASS")
    from_addr = from_addr or os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        print("[ERROR] SMTP_USER and SMTP_PASS must be set (env vars or args)")
        sys.exit(1)

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to
    msg["Subject"] = subject

    content_type = "html" if html else "plain"
    msg.attach(MIMEText(body, content_type))

    for filepath in (attachments or []):
        path = Path(filepath)
        if not path.exists():
            print(f"[WARN] Attachment not found: {filepath}")
            continue
        part = MIMEBase("application", "octet-stream")
        part.set_payload(path.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={path.name}")
        msg.attach(part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print(f"[OK] Email sent to {to}: {subject}")


def main():
    parser = argparse.ArgumentParser(description="Send email with attachments")
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--attachments", nargs="*", default=[])
    parser.add_argument("--html", action="store_true")
    parser.add_argument("--smtp-host", default=None)
    parser.add_argument("--smtp-port", type=int, default=None)
    parser.add_argument("--smtp-user", default=None)
    parser.add_argument("--smtp-pass", default=None)
    parser.add_argument("--from-addr", default=None)
    args = parser.parse_args()

    send_email(args.to, args.subject, args.body, args.attachments, args.html,
               args.smtp_host, args.smtp_port, args.smtp_user, args.smtp_pass, args.from_addr)


if __name__ == "__main__":
    main()
