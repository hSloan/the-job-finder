#!/usr/bin/env python3
"""
camoufox_browser.py — Camoufox-powered browser helper for OpenClaw skills.

Usage:
  python3 camoufox_browser.py <command> [options]

Commands:
  navigate      --url <url> [--screenshot <path>] [--html <path>]
  fill_form     --url <url> --fields <json> [--submit] [--screenshot <path>]
  upload_apply  --url <url> --fields <json> --resume <path> [--cover_letter <path>] [--screenshot <path>]
  get_text      --url <url> [--selector <css>]
  check_url     --url <url>   (returns page title + status)

All commands output JSON to stdout.
Exit code 0 = success, 1 = error.
"""

import sys
import json
import argparse
import time
import random
from pathlib import Path

try:
    from camoufox.sync_api import Camoufox
except ImportError:
    print(json.dumps({"error": "camoufox not installed. Run: pip install camoufox"}))
    sys.exit(1)


# ── Helpers ─────────────────────────────────────────────────────────────────

def human_delay(min_ms=80, max_ms=300):
    """Simulate human-like pause."""
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


def safe_screenshot(page, path):
    """Take a screenshot, return the path or None on failure."""
    if not path:
        return None
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=path, full_page=True)
        return path
    except Exception as e:
        return f"screenshot_failed: {e}"


def fill_fields(page, fields: dict):
    """
    Fill form fields. fields is a dict:
      {
        "selector": "value",           # CSS selector → value (type text)
        "#email": "me@example.com",
        "select:#country": "US",       # prefix 'select:' for <select> elements
        "check:#agree": true,          # prefix 'check:' for checkboxes
        "file:#resume": "/path/file",  # prefix 'file:' for file inputs
      }
    Returns list of {selector, status} results.
    """
    results = []
    for raw_selector, value in fields.items():
        kind = "text"
        selector = raw_selector

        if raw_selector.startswith("select:"):
            kind = "select"
            selector = raw_selector[7:]
        elif raw_selector.startswith("check:"):
            kind = "check"
            selector = raw_selector[6:]
        elif raw_selector.startswith("file:"):
            kind = "file"
            selector = raw_selector[5:]

        try:
            el = page.locator(selector).first
            el.scroll_into_view_if_needed(timeout=5000)
            human_delay()

            if kind == "text":
                el.click()
                human_delay(50, 150)
                el.fill(str(value))
            elif kind == "select":
                el.select_option(value=str(value))
            elif kind == "check":
                if value and not el.is_checked():
                    el.check()
                elif not value and el.is_checked():
                    el.uncheck()
            elif kind == "file":
                el.set_input_files(str(value))

            human_delay(100, 400)
            results.append({"selector": raw_selector, "status": "ok"})
        except Exception as e:
            results.append({"selector": raw_selector, "status": "error", "detail": str(e)})

    return results


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_navigate(args):
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.goto(args.url, wait_until="networkidle", timeout=30000)
        human_delay(500, 1000)
        result = {
            "url": page.url,
            "title": page.title(),
            "status": "ok",
        }
        if args.screenshot:
            result["screenshot"] = safe_screenshot(page, args.screenshot)
        if args.html:
            Path(args.html).parent.mkdir(parents=True, exist_ok=True)
            Path(args.html).write_text(page.content(), encoding="utf-8")
            result["html"] = args.html
        return result


def cmd_fill_form(args):
    fields = json.loads(args.fields)
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.goto(args.url, wait_until="networkidle", timeout=30000)
        human_delay(800, 1500)

        fill_results = fill_fields(page, fields)

        submitted = False
        if args.submit:
            try:
                human_delay(300, 800)
                # Try common submit patterns
                for submit_sel in [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Submit")',
                    'button:has-text("Apply")',
                    'button:has-text("Continue")',
                    'button:has-text("Next")',
                ]:
                    btn = page.locator(submit_sel).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click()
                        human_delay(1000, 2000)
                        submitted = True
                        break
            except Exception as e:
                pass

        result = {
            "url": page.url,
            "title": page.title(),
            "fill_results": fill_results,
            "submitted": submitted,
            "status": "ok",
        }
        if args.screenshot:
            result["screenshot"] = safe_screenshot(page, args.screenshot)
        return result


def cmd_upload_apply(args):
    fields = json.loads(args.fields)

    # Inject file uploads into fields
    if args.resume:
        # Try to find resume input — user can also explicitly pass 'file:#resume-input': path
        fields.setdefault("file:input[type='file']", args.resume)
    if args.cover_letter:
        # If there's a second file input, use it for cover letter
        # This is a heuristic — explicit selector in fields overrides
        pass

    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.goto(args.url, wait_until="networkidle", timeout=30000)
        human_delay(800, 1500)

        fill_results = fill_fields(page, fields)

        # Attempt submit
        submitted = False
        try:
            human_delay(500, 1000)
            for submit_sel in [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit Application")',
                'button:has-text("Submit")',
                'button:has-text("Apply Now")',
                'button:has-text("Apply")',
            ]:
                btn = page.locator(submit_sel).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                    human_delay(1500, 3000)
                    submitted = True
                    break
        except Exception as e:
            pass

        result = {
            "url": page.url,
            "title": page.title(),
            "fill_results": fill_results,
            "submitted": submitted,
            "status": "ok",
        }
        if args.screenshot:
            result["screenshot"] = safe_screenshot(page, args.screenshot)
        return result


def cmd_get_text(args):
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.goto(args.url, wait_until="networkidle", timeout=30000)
        human_delay(500, 1000)
        if args.selector:
            text = page.locator(args.selector).first.inner_text()
        else:
            text = page.inner_text("body")
        return {"url": page.url, "title": page.title(), "text": text, "status": "ok"}


def cmd_check_url(args):
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        resp = page.goto(args.url, timeout=30000)
        return {
            "url": page.url,
            "title": page.title(),
            "http_status": resp.status if resp else None,
            "status": "ok",
        }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Camoufox browser helper")
    subparsers = parser.add_subparsers(dest="command")

    # navigate
    p = subparsers.add_parser("navigate")
    p.add_argument("--url", required=True)
    p.add_argument("--screenshot")
    p.add_argument("--html")

    # fill_form
    p = subparsers.add_parser("fill_form")
    p.add_argument("--url", required=True)
    p.add_argument("--fields", required=True, help='JSON object of selector→value')
    p.add_argument("--submit", action="store_true")
    p.add_argument("--screenshot")

    # upload_apply
    p = subparsers.add_parser("upload_apply")
    p.add_argument("--url", required=True)
    p.add_argument("--fields", required=True, help='JSON object of selector→value')
    p.add_argument("--resume", required=True)
    p.add_argument("--cover_letter")
    p.add_argument("--screenshot")

    # get_text
    p = subparsers.add_parser("get_text")
    p.add_argument("--url", required=True)
    p.add_argument("--selector")

    # check_url
    p = subparsers.add_parser("check_url")
    p.add_argument("--url", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        dispatch = {
            "navigate": cmd_navigate,
            "fill_form": cmd_fill_form,
            "upload_apply": cmd_upload_apply,
            "get_text": cmd_get_text,
            "check_url": cmd_check_url,
        }
        result = dispatch[args.command](args)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"error": str(e), "command": args.command, "status": "error"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
