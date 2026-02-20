# Job Board API Reference

## Free / No-Key APIs

### The Muse API
- **Base URL:** `https://www.themuse.com/api/public/jobs`
- **Auth:** None required
- **Params:** `page`, `descending=true`, `category={category}`, `level={level}`, `location={location}`
- **Categories:** Software Engineering, Data Science, Design, Marketing, Finance, etc.
- **Levels:** Entry Level, Mid Level, Senior Level, Management
- **Response:** JSON with `results[]` containing `name`, `company.name`, `locations[].name`, `levels[].name`, `refs.landing_page`, `contents` (HTML description)
- **Rate limit:** Reasonable use, no published limit
- **Example:**
  ```
  GET https://www.themuse.com/api/public/jobs?category=Software%20Engineering&level=Senior%20Level&location=Remote&page=0
  ```

### RemoteOK API
- **URL:** `https://remoteok.com/api`
- **Auth:** None required
- **Response:** JSON array of jobs. First element is metadata, rest are jobs with: `slug`, `company`, `position`, `description`, `location`, `salary_min`, `salary_max`, `url`, `apply_url`, `tags[]`
- **Filtering:** Client-side only — filter results by tags/keywords after fetching
- **Rate limit:** Add `User-Agent` header, don't hammer it
- **Example:**
  ```
  GET https://remoteok.com/api
  ```

### USAJobs API
- **Base URL:** `https://data.usajobs.gov/api/search`
- **Auth:** API key required (free) — register at https://developer.usajobs.gov/APIRequest/Index
- **Headers:** `Authorization-Key: {key}`, `User-Agent: {email}`
- **Params:** `Keyword`, `LocationName`, `PayGradeHigh`, `PayGradeLow`, `ResultsPerPage`
- **Response:** JSON `SearchResult.SearchResultItems[]` with `MatchedObjectDescriptor` containing title, org, location, salary, URL, qualifications
- **Example:**
  ```
  GET https://data.usajobs.gov/api/search?Keyword=software+engineer&LocationName=Remote&ResultsPerPage=25
  ```

## Key-Required APIs (Free Tier)

### Adzuna API
- **Base URL:** `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}`
- **Auth:** `app_id` and `app_key` params — register free at https://developer.adzuna.com/
- **Countries:** `us`, `gb`, `au`, `ca`, `de`, `fr`, `in`, `nl`, etc.
- **Params:** `what` (keywords), `where` (location), `salary_min`, `salary_max`, `full_time`, `permanent`, `results_per_page`
- **Response:** JSON with `results[]` containing `title`, `company.display_name`, `location.display_name`, `salary_min`, `salary_max`, `redirect_url`, `description`
- **Rate limit:** 250 requests/day on free tier
- **Example:**
  ```
  GET https://api.adzuna.com/v1/api/jobs/us/search/1?app_id=XXX&app_key=YYY&what=python+developer&where=new+york&results_per_page=20
  ```

## Web Scraping Targets (Fallback)

When APIs are insufficient, use `web_search` + `web_fetch`:

- **LinkedIn:** `site:linkedin.com/jobs "{title}" "{location}"`
- **Indeed:** `site:indeed.com/viewjob "{title}" "{location}"`
- **Glassdoor:** `site:glassdoor.com/job-listing "{title}"`

Note: These sites have anti-scraping measures. Prefer API sources. Use web search for discovery, then `web_fetch` for individual listing details.
