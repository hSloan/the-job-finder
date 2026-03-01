# Browser Automation — Camoufox

Use Camoufox (anti-detect Firefox) for all job application browser automation.
**Do NOT use the built-in `browser` tool for form filling** — it gets flagged by anti-bot systems.

## Setup

- **Bundled script:** `scripts/camoufox_browser.py` (included in this skill)
- **venv:** `~/.openclaw/workspace/.venv`
- **Credentials:** See `references/credentials.md` for all required env vars

## How to Call It (via exec tool)

Always prefix commands with the venv activation and run from the workspace root:

```bash
cd ~/.openclaw/workspace && source .venv/bin/activate && \
python3 skills/job-finder/scripts/camoufox_browser.py <command> [options]
```

## Commands

### Navigate to a page + screenshot
```bash
python3 scripts/camoufox_browser.py navigate \
  --url "https://example.com/careers" \
  --screenshot "/tmp/page.png"
```

### Read page text (for scraping job details)
```bash
python3 scripts/camoufox_browser.py get_text \
  --url "https://example.com/job/123"
```
With a CSS selector:
```bash
python3 scripts/camoufox_browser.py get_text \
  --url "https://example.com/job/123" \
  --selector ".job-description"
```

### Fill and submit a form
```bash
python3 scripts/camoufox_browser.py fill_form \
  --url "https://example.com/apply" \
  --fields '{"#first_name": "John", "#last_name": "Doe", "#email": "john@example.com"}' \
  --submit \
  --screenshot "/tmp/confirmation.png"
```

### Upload resume + fill application
```bash
python3 scripts/camoufox_browser.py upload_apply \
  --url "https://example.com/apply" \
  --fields '{"#first_name": "John", "#email": "john@example.com"}' \
  --resume "/path/to/resume.pdf" \
  --cover_letter "/path/to/cover_letter.pdf" \
  --screenshot "/tmp/confirmation.png"
```

## Field Selector Prefixes

| Prefix | Element type | Example |
|--------|-------------|---------|
| (none) | Text/textarea | `"#email": "me@example.com"` |
| `select:` | `<select>` dropdown | `"select:#country": "US"` |
| `check:` | Checkbox | `"check:#agree": true` |
| `file:` | File input | `"file:#resume-input": "/path/file.pdf"` |

## Output Format

All commands return JSON:
```json
{
  "url": "final page url after navigation",
  "title": "page title",
  "status": "ok",
  "fill_results": [{"selector": "#email", "status": "ok"}],
  "submitted": true,
  "screenshot": "/tmp/confirmation.png"
}
```

Error:
```json
{"error": "message", "command": "fill_form", "status": "error"}
```

## Workflow for Job Applications

1. Use `get_text` to scrape the job listing if needed
2. Inspect the form — use `navigate` with `--html /tmp/form.html` to capture the DOM, then `read` the HTML file to identify selectors
3. Build the `--fields` JSON mapping selectors to candidate data from `candidate.json`
4. Run `upload_apply` with resume + cover letter
5. Check `submitted: true` in output
6. Use the screenshot as confirmation proof

## CAPTCHA Handling

When a CAPTCHA is detected mid-application, do **not** bail to "Match". Use the `gotta-captcha` skill:

```bash
# 1. Save current session cookies
python3 -c "
import json
from camoufox.sync_api import Camoufox
# ... your running session ...
cookies = page.context.cookies()
open('/tmp/apply_cookies.json','w').write(json.dumps(cookies))
"

# 2. Invoke gotta-captcha handoff
cd ~/.openclaw/workspace && source .venv/bin/activate
python3 skills/gotta-captcha/scripts/captcha_handoff.py \
  --url <current_apply_url> \
  --cookies /tmp/apply_cookies.json \
  --captcha-type recaptcha_v2 \
  --notify tui

# Exit 0 = solved. Reload cookies and resume form submission.
```

The TUI will display a handoff banner. Relay it to the human and wait. The script polls
every 3 seconds and exits 0 when the CAPTCHA is cleared. Then reload the cookies and submit.

Detection before submission:
```bash
python3 skills/gotta-captcha/scripts/captcha_detect.py --url <apply_url>
# {"detected": true, "type": "recaptcha_v2", ...}
```

Reference: `~/.openclaw/workspace/skills/gotta-captcha/`

---

## Login Wall Handling

When navigating to an apply page redirects to a sign-in/register page, use the
`im-accounted-for` skill to auto-create and verify an account:

```bash
SITE="sitename"
COOKIES="/tmp/${SITE}_cookies.json"

# 1. Register account (reads IMAP_EMAIL env var)
python3 skills/account-creator/scripts/create_account.py \
  --url "https://site.com/register" \
  --email "$IMAP_EMAIL" \
  --name-first "$CANDIDATE_FIRST" \
  --name-last "$CANDIDATE_LAST" \
  --password "$ACCOUNT_PASS" \
  --site-key "$SITE" \
  --cookies "$COOKIES"
# Exit 3 = CAPTCHA on signup → invoke gotta-captcha first, then retry

# 2. Self-verify via inbox
python3 skills/account-creator/scripts/check_inbox.py \
  --email "$IMAP_EMAIL" \
  --password "$IMAP_PASS" \
  --from-domain "site.com" \
  --wait 120 \
  --auto-verify \
  --cookies "$COOKIES"

# 3. Resume application with verified session cookies
# (pass cookies to next Camoufox context)
```

Reference: `~/.openclaw/workspace/skills/account-creator/`

---

## Hard Fallback

Only fall back to "Match" (email link, no submission) when:
- Camoufox form fill failed, AND
- CAPTCHA could not be resolved via `gotta-captcha`, AND
- Account creation via `im-accounted-for` failed or no registration path exists (OAuth/SSO only)

In that case, follow the "Match" email path in SKILL.md Step 5b.
