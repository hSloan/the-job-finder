# The Job Finder

An OpenClaw skill that automates job searching, resume tailoring, cover letter generation, and job applications end-to-end — including navigating CAPTCHAs and login-wall sites.

---

## What It Does

1. **Intake** — Collects candidate info (name, email, phone, resume) and job preferences
2. **Search** — Queries job board APIs (The Muse, RemoteOK, USAJobs, Adzuna) and falls back to web search (LinkedIn, Indeed, Glassdoor)
3. **Tailor** — Rewords existing resume content to align with each job description — never fabricates experience
4. **Cover Letter** — Generates a targeted cover letter when required by the listing
5. **Apply** — Submits applications via Camoufox browser automation with a full escalation ladder:
   - Direct form submission
   - CAPTCHA? → `gotta-captcha` hands it off to the human, then resumes automatically
   - Login wall? → `im-accounted-for` auto-creates and verifies an account, then continues
   - OAuth/SSO only? → Falls back to "Match" email as a last resort
6. **Email** — Notifies the candidate of results:
   - `Applied! | Job Finder Scoop: {job title}` — successfully applied, resume & cover letter attached
   - `Match | Job Finder Scoop: {job title}` — couldn't auto-apply, includes listing details and apply instructions

---

## Browser Stack

**All browser automation uses [Camoufox](https://github.com/daijro/camoufox) — an anti-detect Firefox fork.** The built-in OpenClaw `browser` tool is not used for job applications; it is fingerprinted as a bot by modern job sites and results in blocked pages, broken forms, and silent failures.

Camoufox spoofs browser fingerprints at the C++ level — device, OS, WebGL, WebRTC, fonts, screen size — and presents as a real Firefox user. This is required for reliable form submission across major job boards.

### Skill Dependencies

| Skill | Purpose | Repo |
|-------|---------|------|
| `gotta-captcha` | Detect CAPTCHAs, open headed browser on human's screen, wait for solve, resume | [hSloan/gotta-captcha](https://github.com/hSloan/gotta-captcha) |
| `im-accounted-for` | Auto-register on login-wall sites, self-verify via IMAP email polling | [hSloan/im-accounted-for](https://github.com/hSloan/im-accounted-for) |

These skills are required for maximum application coverage. Without them, sites with CAPTCHAs or account requirements fall back to "Match" emails instead of completed applications.

---

## Application Escalation Ladder

```
Navigate to apply URL (Camoufox)
          │
   Form accessible?
  ┌───────┴────────┐
 Yes               No (login wall)
  │                │
  │           im-accounted-for
  │          (register + verify)
  │                │
  └───────┬────────┘
          │
    Fill form (Camoufox)
          │
      CAPTCHA?
  ┌────────┴────────┐
 No                Yes
  │                │
  │          gotta-captcha
  │         (human solves,
  │          auto-resumes)
  │                │
  └───────┬────────┘
          │
       Submit ✅
          │
     Email candidate
     "Applied!"

If all paths fail → Email candidate "Match" + apply link
```

---

## Requirements

- **OpenClaw** with `web_search`, `web_fetch`, and `exec` tools enabled
- **Python 3.11+**
- **Camoufox** + **PDF generation deps** installed in the workspace venv:
  ```bash
  cd ~/.openclaw/workspace
  python3 -m venv .venv
  source .venv/bin/activate
  pip install 'camoufox[geoip]' fpdf2 markdown
  python3 -m camoufox fetch
  ```
  - `fpdf2` — generates resume and cover letter PDFs from the tailored markdown content (replaces `reportlab`; lighter weight, no system dependencies)
  - `markdown` — converts markdown-formatted resume/cover letter files to HTML as an intermediate step before PDF rendering
- **`gotta-captcha` skill** — installed at `skills/gotta-captcha/`
- **`im-accounted-for` skill** — installed at `skills/account-creator/`
- **Credentials** — SMTP (email sending) and IMAP (account verification). See `references/credentials.md` for the full variable list and setup instructions — that is the single source of truth; do not configure credentials from README examples.
- **API keys** (optional) — Adzuna and USAJobs expand search coverage but aren't required

---

## Installation

Clone into your skills directory:

```bash
git clone https://github.com/hSloan/the-job-finder.git ~/.openclaw/workspace/skills/job-finder
```

Then install dependencies:

```bash
git clone https://github.com/hSloan/gotta-captcha.git ~/.openclaw/workspace/skills/gotta-captcha
git clone https://github.com/hSloan/im-accounted-for.git ~/.openclaw/workspace/skills/account-creator
cd ~/.openclaw/workspace && python3 -m venv .venv
source .venv/bin/activate && pip install 'camoufox[geoip]' fpdf2 markdown
python3 -m camoufox fetch
```

---

## Usage

Just ask your agent:

> "Find me a job. Here's my resume..."

The agent walks through intake, searches for matching roles, tailors the resume and cover letter, and handles application submission — including solving CAPTCHAs and creating accounts — automatically.

You can also be specific:

> "Find remote senior Python developer roles and apply for me"

> "Search for retail cashier jobs near Palm Coast FL and apply to the top 10"

When a CAPTCHA appears, you'll see a handoff banner in the TUI and a browser window opens on your screen. Solve it and the agent resumes automatically.

---

## Reference Files

| File | Purpose |
|------|---------|
| `references/credentials.md` | **Single source of truth** for all env vars — SMTP, IMAP, storage paths |
| `references/browser-automation.md` | Camoufox CLI usage, CAPTCHA handling, login wall handling |
| `references/email-sending.md` | SMTP email sending instructions |
| `references/job-apis.md` | Job board API integration details |

## Bundled Scripts

| Script | Purpose |
|--------|---------|
| `scripts/camoufox_browser.py` | Anti-detect Firefox browser runner — navigate, fill forms, upload files |
| `scripts/generate_resume_pdf.py` | Generates tailored resume/cover letter PDFs using `fpdf2` (replaces `reportlab`) |
| `scripts/send_email.py` | Sends candidate notification emails with attachments via SMTP |

---

## License

MIT
