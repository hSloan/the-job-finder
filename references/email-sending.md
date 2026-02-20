# Email Sending Reference

## Via OpenClaw Message Tool

If email is configured as a channel in OpenClaw, use the `message` tool:
```
message(action="send", channel="email", target="recipient@example.com", message="...", subject="...")
```

## Via Command Line (macOS)

### Using `mail` command
```bash
echo "Body text here" | mail -s "Subject Line" recipient@example.com
```

### With attachments (using mpack or mutt)
```bash
# mutt (if installed)
echo "Body" | mutt -s "Subject" -a /path/to/resume.pdf -a /path/to/cover_letter.pdf -- recipient@example.com

# Or use Python script
python3 scripts/send_email.py --to "email" --subject "Subject" --body "Body" --attachments resume.pdf cover_letter.pdf
```

## Via Python (SMTP)

Use `scripts/send_email.py` which handles:
- SMTP connection (Gmail, Outlook, or custom SMTP)
- HTML body with plain text fallback
- PDF attachments (resume, cover letter)
- Requires SMTP credentials in environment or config

Check if credentials exist:
```bash
echo $SMTP_HOST $SMTP_USER
```

If no email sending method is available, save the email content as a file and notify the human to send it manually.
