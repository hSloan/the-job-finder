# Credentials Reference

Single source of truth for all credentials and configuration used by this skill and
its dependencies. **Never hardcode values here or in any script.** Read from environment
variables at runtime, or consult the caller's `TOOLS.md` for the actual values.

---

## How to Set Credentials

Set environment variables before running any script:

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASS="your-app-password"
export IMAP_EMAIL="your-registration-email@gmail.com"
export IMAP_PASS="your-app-password"
```

Or prefix individual commands:

```bash
SMTP_USER="..." SMTP_PASS="..." python3 scripts/send_email.py ...
```

The actual credential values live in the caller's `TOOLS.md` workspace file, which is
never committed to any repository.

---

## All Required Variables

### Email Sending (SMTP)

Used by: `scripts/send_email.py`, candidate notification emails

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP login / From address | *(required)* |
| `SMTP_PASS` | SMTP password or app password | *(required)* |

### Account Registration Email (IMAP)

Used by: `im-accounted-for` skill (`check_inbox.py`) for polling verification emails

| Variable | Description | Default |
|----------|-------------|---------|
| `IMAP_EMAIL` | Email address used to register accounts on job sites | *(required)* |
| `IMAP_PASS` | IMAP password or app password (same provider as SMTP is fine) | *(required)* |
| `IMAP_HOST` | IMAP server hostname | `imap.gmail.com` |
| `IMAP_PORT` | IMAP server port (SSL) | `993` |

> **Gmail tip:** Use the same app password for both SMTP and IMAP. Generate one at
> myaccount.google.com → Security → App passwords. IMAP must be enabled in Gmail settings.

> **Plus addressing:** Use `your-email+sitename@gmail.com` for account registration —
> all variants deliver to the same inbox, but look unique to each job site.

### Account Storage

Used by: `im-accounted-for` skill for logging created accounts

| Variable | Description | Default |
|----------|-------------|---------|
| `ACCOUNTS_FILE` | Path to the JSON file where created accounts are logged | `~/.openclaw/workspace/accounts.json` |

The accounts file is local only — never committed, never logged to stdout.

---

## Dependency Credential Map

| Script / Skill | Variables needed |
|----------------|-----------------|
| `scripts/send_email.py` | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` |
| `scripts/camoufox_browser.py` | *(none — no auth needed)* |
| `gotta-captcha` skill | *(none — uses local browser + TUI)* |
| `im-accounted-for` / `check_inbox.py` | `IMAP_EMAIL`, `IMAP_PASS`, `IMAP_HOST`, `IMAP_PORT`, `ACCOUNTS_FILE` |
| `im-accounted-for` / `create_account.py` | `IMAP_EMAIL` (as `--email` default) |
