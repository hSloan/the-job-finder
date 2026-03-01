---
name: job-finder
description: >
  Automated job search, resume tailoring, cover letter generation, and job application agent.
  Use when a human asks to find jobs, search for job listings, apply for jobs, tailor a resume,
  generate a cover letter, or automate their job hunt. Handles full pipeline: intake candidate
  info (name, email, phone, resume), search job boards, tailor resume to listings, generate
  cover letters, applies directly when possible using Camoufox browser automation, and emails
  results to the candidate. Integrates gotta-captcha for CAPTCHA handoff and im-accounted-for
  for automatic account creation on login-wall sites — maximising the number of applications
  submitted without human intervention.
---

# Job Finder

End-to-end job search and application agent. Takes candidate information, finds matching jobs,
tailors resumes, generates cover letters, applies when possible, and emails the candidate.

## Browser Stack — Mandatory Reading

**Always use Camoufox for every browser interaction in this skill. No exceptions.**

The built-in `browser` tool uses Chromium and is fingerprinted as a bot by most modern job
sites — resulting in blocked page loads, invisible form fields, broken uploads, and silent
submission failures. Camoufox presents as a real, human Firefox browser at the C++ level
and bypasses these protections reliably.

| Tool | Use for |
|------|---------|
| ✅ Camoufox (`camoufox_browser.py`) | All job site navigation, form filling, file uploads, DOM inspection |
| ✅ `gotta-captcha` skill | Any CAPTCHA encountered during apply or account creation |
| ✅ `im-accounted-for` skill | Any login wall requiring account registration before applying |
| ❌ Built-in `browser` tool | **Never** — flagged as bot on all major job sites |
| ❌ `web_fetch` for apply flows | **Never** — cannot execute JS or maintain session state |

**Setup (must be in place before any apply step):**
```bash
# venv
source ~/.openclaw/workspace/.venv/bin/activate

# Camoufox runner
python3 scripts/camoufox_browser.py <command>

# Full reference
cat ~/.openclaw/workspace/skills/job-finder/references/browser-automation.md
```

If the venv or Camoufox binary is missing, stop and install before proceeding:
```bash
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

Use Camoufox (anti-detect Firefox) for all browser automation. See `references/browser-automation.md`
for full usage. **Do not use the built-in `browser` tool** — it is flagged by anti-bot systems.

#### 5a. Open Application — Submit Directly

1. Navigate to the apply URL with Camoufox
2. Inspect the form (capture DOM if needed)
3. Fill candidate details (name, email, phone) and upload resume + cover letter
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
