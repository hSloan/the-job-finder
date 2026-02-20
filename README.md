# The Job Finder

An OpenClaw skill that automates job searching, resume tailoring, cover letter generation, and job applications.

## What It Does

1. **Intake** — Collects candidate info (name, email, phone, resume) and job preferences
2. **Search** — Queries job board APIs (The Muse, RemoteOK, USAJobs, Adzuna) and falls back to web search (LinkedIn, Indeed, Glassdoor)
3. **Tailor** — Rewords existing resume content to align with each job description — never fabricates experience
4. **Cover Letter** — Generates a targeted cover letter when required by the listing
5. **Apply** — Submits applications via browser automation when possible
6. **Email** — Notifies the candidate of results:
   - `Applied! | Job Finder Scoop: {job title}` — successfully applied, includes resume & cover letter
   - `Match | Job Finder Scoop: {job title}` — couldn't auto-apply, includes listing details and how to apply

## Requirements

- **OpenClaw** with web search, web fetch, browser, and exec tools enabled
- **Python 3** for bundled scripts
- **SMTP credentials** (env vars `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`) for sending emails
- **reportlab** (optional) — `pip3 install reportlab` for PDF resume generation; falls back to plain text without it
- **API keys** (optional) — Adzuna and USAJobs keys expand search coverage but aren't required

## Installation

Install as an OpenClaw skill:

```bash
openclaw skill install the-job-finder.skill
```

Or clone directly into your skills directory:

```bash
git clone https://github.com/hSloan/the-job-finder.git ~/.openclaw/workspace/skills/job-finder
```

## Usage

Just ask your agent something like:

> "Find me a job. Here's my resume..."

The agent will walk you through intake, search for matching roles, and handle the rest. You can also be specific:

> "Find remote senior Python developer roles and apply for me"

> "Search for product manager jobs in NYC, $120-160k range"

## Bundled Scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate_resume_pdf.py` | Generates a tailored resume PDF (or text fallback) from structured JSON |
| `scripts/send_email.py` | Sends emails with attachments via SMTP |

## License

MIT
