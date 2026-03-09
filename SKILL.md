---
name: job-finder
description: >
  Automated job search, resume tailoring, cover letter generation, and job application agent.
  Use when a human asks to find jobs, search for job listings, apply for jobs, tailor a resume,
  generate a cover letter, or automate their job hunt. Handles full pipeline: intake candidate
  info (name, email, phone, resume), search job boards, tailor resume to listings, generate
  cover letters, applies directly when possible using Scrapling StealthyFetcher (primary) or
  Camoufox browser automation (fallback), and emails results to the candidate. Integrates
  gotta-captcha for CAPTCHA handoff and im-accounted-for for automatic account creation on
  login-wall sites — maximising the number of applications submitted without human intervention.
---

# Job Finder

End-to-end job search and application agent. Takes candidate information, finds matching jobs,
tailors resumes, generates cover letters, applies when possible, and emails the candidate.

## Browser Stack — Mandatory Reading

**Never use the built-in `browser` tool for job applications.** It is fingerprinted as a bot
on all major job sites.

### Routing: Scrapling (primary) → Camoufox (fallback)

| Tool | Use for |
|------|---------|
| ✅ **Scrapling** (`scrapling_apply.py`) | **Primary** — all job sites. Bypasses Cloudflare Turnstile/Interstitial, adaptive element tracking, auto-detects form fields |
| ✅ Camoufox (`camoufox_browser.py`) | **Fallback** — when Scrapling can't complete or CAPTCHA needs a human in a headed browser |
| ✅ `gotta-captcha` skill | Any CAPTCHA encountered — switches to headed browser, notifies human, resumes |
| ✅ `im-accounted-for` skill | Any login wall requiring account registration before applying |
| ❌ Built-in `browser` tool | **Never** — flagged as bot on all major job sites |
| ❌ `web_fetch` for apply flows | **Never** — cannot execute JS or maintain session state |

**Quick decision rule:**
1. Use `scrapling_apply.py` first — probe the URL, scrape the form, fill and submit
2. If Scrapling hits a CAPTCHA mid-flow → invoke `gotta-captcha` + retry with Camoufox headed
3. If both fail completely → escalate to the human operator via Discord

**Setup:**
```bash
# Activate venv
source ~/.openclaw/workspace/.venv/bin/activate

# Scrapling (primary)
python3 scripts/scrapling_apply.py probe "https://example.com"
python3 scripts/scrapling_apply.py scrape "https://example.com/apply"
python3 scripts/scrapling_apply.py fill --json /tmp/payload.json

# Camoufox (fallback)
python3 scripts/camoufox_browser.py <command>

# Full reference
cat references/browser-automation.md
```

If `scrapling[all]` or Camoufox is missing:
```bash
pip install 'scrapling[all]' && scrapling install
pip install 'camoufox[geoip]' && python3 -m camoufox fetch
```

## Workflow

### 1. Candidate Intake

Collect from the human (do not proceed until all are provided):

- **Full name**
- **Email address**
- **Phone number**
- **Resume** (file path or pasted content)
- **Job preferences** (optional but ask): target role/title, location preference (remote/hybrid/city), salary range, industry, keywords

Parse the resume and store structured data: work history, skills, education, certifications.
Save intake to `candidate.json` in the workspace for the session.

### 2. Job Search

Search for matching jobs using these sources in priority order:

#### a. API-Based Sources (preferred — structured data, apply capability)

Read `references/job-apis.md` for API integration details.

- **Adzuna API** — free tier available, covers US/UK/EU, returns structured listings
- **The Muse API** — free, no key needed, good for tech/startup roles
- **USAJobs API** — free, US government jobs, no key needed
- **RemoteOK API** — free, no key, remote tech jobs

#### b. Web Search Fallback

If APIs return insufficient results or for broader coverage:

- Use `web_search` with queries like: `"{job title}" "{location}" site:linkedin.com/jobs OR site:indeed.com OR site:glassdoor.com`
- Use `web_fetch` to extract listing details from results

#### c. Filtering & Ranking

Score each listing against the candidate's profile:
- Skill match (keywords from resume vs. job requirements)
- Location match
- Seniority/experience level alignment
- Salary range overlap (if available)

Present top 5-10 matches to the human for approval before proceeding.
If the human says "apply to all" or similar, proceed with all matches.

### 3. Resume Tailoring

For each approved listing:

- **Only modify within the bounds of existing experience** — reword responsibilities and achievements to better align with the job description's language and keywords
- Never fabricate experience, skills, or credentials
- Adjust the professional summary/objective to target the specific role
- Reorder skills to prioritize those mentioned in the job description
- Save tailored resume as PDF using the script: `scripts/generate_resume_pdf.py`

### 4. Cover Letter Generation

Generate a cover letter when:
- The listing explicitly requires one
- The human requests it
- Applying via email (always include one)

Cover letter guidelines:
- 3-4 paragraphs, under 400 words
- Reference specific company name and role
- Connect candidate's experience to job requirements
- Professional but not generic — show genuine interest
- Save as PDF alongside the resume

### 5. Application Submission

Use Scrapling (`scrapling_apply.py`) as the primary browser tool. Fall back to Camoufox only if
Scrapling fails or a CAPTCHA requires a headed browser. See `references/browser-automation.md`
for full routing details. **Never use the built-in `browser` tool** — flagged as bot on all major job sites.

#### 5a. Open Application — Submit Directly

1. `probe` the apply URL with Scrapling to confirm reachability and detect Cloudflare
2. `scrape` the form to identify field selectors
3. `fill` the form with candidate details (name, email, phone, cover letter) and upload resume if supported
4. Screenshot the confirmation page as proof

**If a CAPTCHA appears during form fill or submission:**
- Invoke the `gotta-captcha` skill — it opens a visible browser on the human's screen,
  notifies via TUI, waits for the human to solve, then resumes the session
- See `references/browser-automation.md` → CAPTCHA Handling

**If the site requires an account (login wall) before showing the apply form:**
- Invoke the `im-accounted-for` skill — it auto-registers using the configured email,
  polls the inbox via IMAP, self-verifies via code or link, and returns live session cookies
- Resume the application using the verified session
- See `references/browser-automation.md` → Login Wall Handling

After successful submission, send email:
- **To:** candidate's email
- **Subject:** `Applied! | Job Finder Scoop: {job listing title}`
- **Body:** Job description summary, company name, link to listing, tailored resume and cover letter attached

#### 5b. Hard Fallback — Match Only

Only fall back to "Match" (no application) when all of the following fail:
- Direct form submission with Camoufox
- CAPTCHA solved via `gotta-captcha`
- Account created via `im-accounted-for`
- Application requires OAuth/SSO login only (no email registration path exists)

Send email:
- **To:** candidate's email
- **Subject:** `Match | Job Finder Scoop: {job listing title}`
- **Body:** Job description summary, company name, application URL, what makes it a good match, and any application instructions

### 6. Batch Processing

When processing multiple listings:
- Apply/email for each listing individually
- Track status in a summary table
- At the end, send a summary email with all results:
  - **Subject:** `Job Finder Scoop: Session Summary — {date}`
  - **Body:** Table of all listings with status (Applied/Match), links, and next steps

## Email Sending

Use the `exec` tool to send emails via the command line. Read `references/email-sending.md` for platform-specific instructions.

## Error Handling

- If a job board API requires a key the human hasn't provided, note it and fall back to web search
- If resume parsing fails, ask the human to provide info in plain text
- Always save progress — if interrupted, the session can resume from `candidate.json`

### Application Blockers — Escalation Order

| Blocker | Resolution | Skill |
|---------|-----------|-------|
| CAPTCHA on apply form | Open headed browser, notify human via TUI, wait for solve, resume | `gotta-captcha` |
| Login wall (email registration) | Auto-register + IMAP self-verify, resume with session cookies | `im-accounted-for` |
| CAPTCHA on signup form | gotta-captcha handoff during account creation | `gotta-captcha` + `im-accounted-for` |
| OAuth/SSO only (no email path) | Hard fallback → "Match" email with apply link | — |
| Site fully broken / 404 | Note in results, skip, flag for URL refresh | — |

Never mark a listing as "Match" until all applicable escalation steps have been attempted.
