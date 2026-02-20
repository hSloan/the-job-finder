---
name: job-finder
description: >
  Automated job search, resume tailoring, cover letter generation, and job application agent.
  Use when a human asks to find jobs, search for job listings, apply for jobs, tailor a resume,
  generate a cover letter, or automate their job hunt. Handles full pipeline: intake candidate
  info (name, email, phone, resume), search job boards, tailor resume to listings, generate
  cover letters, apply when possible, and email results to the candidate.
---

# Job Finder

End-to-end job search and application agent. Takes candidate information, finds matching jobs,
tailors resumes, generates cover letters, applies when possible, and emails the candidate.

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

#### If direct application is possible:
- Use browser automation to fill application forms on job sites
- Upload tailored resume and cover letter
- Fill in candidate details (name, email, phone)
- Screenshot confirmation page as proof

After successful application, send email:
- **To:** candidate's email
- **Subject:** `Applied! | Job Finder Scoop: {job listing title}`
- **Body:** Job description summary, company name, link to listing, and attach the tailored resume and cover letter that were submitted

#### If direct application is not possible:
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
- If an application form has CAPTCHA or complex auth, mark as "Match" instead and email the link
- If resume parsing fails, ask the human to provide info in plain text
- Always save progress — if interrupted, the session can resume from `candidate.json`
