#!/usr/bin/env python3
"""
scrapling_apply.py — Scrapling-powered job application browser automation.

Strategy:
  1. StealthyFetcher (Scrapling) for anti-bot / Cloudflare-protected sites
  2. Camoufox fallback for anything that needs a headed browser for CAPTCHA handoff

Usage:
  python3 scrapling_apply.py <command> [--json <payload_file>]

Commands:
  probe   <url>              Check if a URL is reachable (returns status + page title)
  fill    <url>              Fill + submit a job application form
  scrape  <url>              Scrape visible text/form info from a page

Payload (for 'fill') — JSON file or stdin:
  {
    "url": "https://...",
    "fields": {
      "first_name": "Ashley",
      "last_name": "Agata",
      "email": "Alagata@icloud.com",
      "phone": "(954) 849-1263",
      "message": "Cover letter text here...",
      "resume_path": "/tmp/ashley_resume.pdf"   // optional, for file inputs
    },
    "selectors": {            // optional overrides — auto-detected if omitted
      "first_name": "#input_first",
      "submit": "button[aria-label='Send']"
    },
    "solve_cloudflare": true, // default: true
    "screenshot_path": "/tmp/result.png",
    "timeout": 60000
  }
"""

import sys
import json
import time
import random
import argparse
import traceback
from pathlib import Path

def log(obj: dict):
    print(json.dumps(obj), flush=True)

def human_type(page, selector: str, text: str, delay_range=(0.04, 0.10)):
    """Type into an element with human-like delays."""
    el = page.locator(selector).first
    el.scroll_into_view_if_needed(timeout=10000)
    el.click()
    time.sleep(random.uniform(0.2, 0.4))
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(*delay_range))

def probe(url: str, solve_cloudflare: bool = True, timeout: int = 45000) -> dict:
    """Check if a URL is reachable and return basic page info."""
    from scrapling.fetchers import StealthyFetcher

    try:
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            solve_cloudflare=solve_cloudflare,
            timeout=timeout,
            network_idle=False,   # most job sites have infinite analytics — don't wait
            load_dom=True,
            google_search=True,
        )
        return {
            "status": "ok",
            "http_status": page.status,
            "title": page.css("title::text").get() or "",
            "url": url,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def auto_detect_selectors(page) -> dict:
    """
    Try to auto-detect common form field selectors on the current page.
    Returns a dict of field_name -> css_selector.
    """
    detected = {}
    candidates = {
        "first_name": [
            'input[name="first-name"]', 'input[name="firstName"]',
            'input[id*="first"]', 'input[placeholder*="First"]',
            'input[aria-label*="First"]',
        ],
        "last_name": [
            'input[name="last-name"]', 'input[name="lastName"]',
            'input[id*="last"]', 'input[placeholder*="Last"]',
            'input[aria-label*="Last"]',
        ],
        "email": [
            'input[type="email"]', 'input[name="email"]',
            'input[id*="email"]', 'input[placeholder*="email" i]',
            'input[aria-label*="email" i]',
        ],
        "phone": [
            'input[type="tel"]', 'input[name="phone"]',
            'input[id*="phone"]', 'input[placeholder*="phone" i]',
            'input[aria-label*="phone" i]',
        ],
        "message": [
            'textarea[name="message"]', 'textarea[id*="message"]',
            'textarea[placeholder*="message" i]', 'textarea[aria-label*="message" i]',
            'textarea',
        ],
        "resume": [
            'input[type="file"][name*="resume" i]',
            'input[type="file"][accept*="pdf"]',
            'input[type="file"]',
        ],
        "submit": [
            'button[type="submit"]', 'input[type="submit"]',
            'button[aria-label*="send" i]', 'button[aria-label*="submit" i]',
            'button[aria-label*="apply" i]',
            'button:has-text("Submit")', 'button:has-text("Send")',
            'button:has-text("Apply")',
        ],
    }

    for field, selectors in candidates.items():
        for sel in selectors:
            try:
                count = page.locator(sel).count()
                if count > 0:
                    detected[field] = sel
                    break
            except Exception:
                continue

    return detected

def fill_and_submit(payload: dict) -> dict:
    """Fill a job application form and submit it using StealthyFetcher."""
    from scrapling.fetchers import StealthyFetcher
    from playwright.sync_api import Page

    url = payload["url"]
    fields = payload.get("fields", {})
    selector_overrides = payload.get("selectors", {})
    solve_cf = payload.get("solve_cloudflare", True)
    timeout = payload.get("timeout", 60000)
    screenshot_path = payload.get("screenshot_path", "/tmp/scrapling_result.png")

    result = {
        "url": url,
        "fields_filled": [],
        "errors": [],
        "screenshot": screenshot_path,
        "success": False,
        "body_snippet": "",
    }

    page_ref = {}  # mutable container to share page reference

    def page_action(page: Page):
        page_ref["page"] = page
        time.sleep(2)  # let JS settle after Cloudflare solve

        # Auto-detect selectors, then apply overrides
        detected = auto_detect_selectors(page)
        selectors = {**detected, **selector_overrides}
        log({"status": "selectors_detected", "selectors": selectors})

        field_map = {
            "first_name": fields.get("first_name", ""),
            "last_name": fields.get("last_name", ""),
            "email": fields.get("email", ""),
            "phone": fields.get("phone", ""),
            "message": fields.get("message", ""),
        }

        # Fill text fields
        for field_name, value in field_map.items():
            if not value:
                continue
            sel = selectors.get(field_name)
            if not sel:
                result["errors"].append(f"No selector found for {field_name}")
                continue
            try:
                human_type(page, sel, value)
                result["fields_filled"].append(field_name)
                time.sleep(random.uniform(0.2, 0.4))
                log({"status": "field_filled", "field": field_name})
            except Exception as e:
                result["errors"].append(f"{field_name}: {str(e)[:100]}")

        # Upload resume if provided
        resume_path = fields.get("resume_path")
        if resume_path and Path(resume_path).exists():
            sel = selectors.get("resume")
            if sel:
                try:
                    page.locator(sel).first.set_input_files(resume_path)
                    result["fields_filled"].append("resume")
                    log({"status": "resume_uploaded", "path": resume_path})
                except Exception as e:
                    result["errors"].append(f"resume: {str(e)[:100]}")

        # Screenshot before submit
        page.screenshot(path=screenshot_path.replace(".png", "_prefilled.png"))
        log({"status": "pre_submit_screenshot"})

        # Submit
        submit_sel = selectors.get("submit")
        if submit_sel:
            try:
                btn = page.locator(submit_sel).first
                btn.scroll_into_view_if_needed(timeout=8000)
                time.sleep(0.5)
                btn.click()
                log({"status": "submit_clicked"})
                time.sleep(7)
            except Exception as e:
                result["errors"].append(f"submit: {str(e)[:100]}")
        else:
            result["errors"].append("No submit button selector found")

    try:
        response = StealthyFetcher.fetch(
            url,
            headless=True,
            solve_cloudflare=solve_cf,
            timeout=timeout,
            network_idle=False,
            load_dom=True,
            google_search=True,
            page_action=page_action,
        )

        # Check for success indicators in final page
        body_text = ""
        if "page" in page_ref:
            try:
                body_text = page_ref["page"].locator("body").inner_text()[:800]
                page_ref["page"].screenshot(path=screenshot_path)
            except Exception:
                pass

        result["body_snippet"] = body_text
        success_keywords = [
            "thanks for submitting", "thank you", "message sent",
            "we'll be in touch", "successfully", "application received",
            "application submitted",
        ]
        result["success"] = any(kw in body_text.lower() for kw in success_keywords)

    except Exception as e:
        result["errors"].append(f"fetch: {str(e)[:200]}")
        result["traceback"] = traceback.format_exc()[-400:]

    return result

def scrape_page(url: str, solve_cloudflare: bool = True, timeout: int = 45000) -> dict:
    """Scrape visible text and form info from a page."""
    from scrapling.fetchers import StealthyFetcher

    try:
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            solve_cloudflare=solve_cloudflare,
            timeout=timeout,
            network_idle=False,
            load_dom=True,
            google_search=True,
        )
        title = page.css("title::text").get() or ""
        # Find all form inputs
        inputs = []
        for inp in page.css("input, textarea, select"):
            inputs.append({
                "tag": inp.tag,
                "type": inp.attrib.get("type", ""),
                "name": inp.attrib.get("name", ""),
                "id": inp.attrib.get("id", ""),
                "placeholder": inp.attrib.get("placeholder", ""),
                "aria_label": inp.attrib.get("aria-label", ""),
            })
        # Find buttons
        buttons = []
        for btn in page.css("button, input[type='submit']"):
            buttons.append({
                "tag": btn.tag,
                "type": btn.attrib.get("type", ""),
                "text": btn.get_all_text(strip=True)[:60],
                "aria_label": btn.attrib.get("aria-label", ""),
            })
        return {
            "status": "ok",
            "http_status": page.status,
            "title": title,
            "inputs": inputs,
            "buttons": buttons,
            "url": url,
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()[-300:]}

def main():
    parser = argparse.ArgumentParser(description="Scrapling job application browser")
    parser.add_argument("command", choices=["probe", "fill", "scrape"])
    parser.add_argument("url", nargs="?", help="Target URL")
    parser.add_argument("--json", help="Path to JSON payload file (for 'fill')")
    parser.add_argument("--solve-cloudflare", action="store_true", default=True)
    parser.add_argument("--timeout", type=int, default=60000)
    args = parser.parse_args()

    if args.command == "probe":
        result = probe(args.url, args.solve_cloudflare, args.timeout)
        log(result)

    elif args.command == "scrape":
        result = scrape_page(args.url, args.solve_cloudflare, args.timeout)
        log(result)

    elif args.command == "fill":
        if args.json:
            with open(args.json) as f:
                payload = json.load(f)
        else:
            payload = json.load(sys.stdin)
        result = fill_and_submit(payload)
        log(result)

if __name__ == "__main__":
    main()
