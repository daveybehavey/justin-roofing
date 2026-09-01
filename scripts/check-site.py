#!/usr/bin/env python3
"""Static conversion / NAP / accessibility smoke checks for VIP Roofing site."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHONE_DISP = "250-508-8820"
PHONE_TEL = "+12505088820"
PLACEHOLDER = "250-555-0199"
PAGES = ["index.html", "services.html", "contact.html", "404.html"]


def fail(errors: list[str]) -> None:
    print("FAIL")
    for item in errors:
        print(f"- {item}")
    raise SystemExit(1)


def main() -> None:
    errors: list[str] = []

    for page in PAGES:
        path = ROOT / page
        if not path.exists():
            errors.append(f"{page}: missing file")
            continue
        text = path.read_text(encoding="utf-8")

        if PLACEHOLDER in text or "12505550199" in text:
            errors.append(f"{page}: placeholder phone still present")
        if PHONE_DISP not in text:
            errors.append(f"{page}: missing display phone {PHONE_DISP}")
        if f"tel:{PHONE_TEL}" not in text:
            errors.append(f"{page}: missing tel:{PHONE_TEL}")
        if 'class="header-cta"' not in text:
            errors.append(f"{page}: missing header CTA cluster")
        if 'class="mobile-cta-bar"' not in text:
            errors.append(f"{page}: missing mobile CTA bar")
        if 'class="skip-link"' not in text:
            errors.append(f"{page}: missing skip link")
        if 'id="main-content"' not in text:
            errors.append(f"{page}: missing main landmark id")

        if page != "404.html":
            if "formspree.io/f/xzzeboly" not in text:
                errors.append(f"{page}: missing Formspree action")
            if 'name="city"' not in text:
                errors.append(f"{page}: missing city/area intent field")
            if 'type="checkbox"' not in text or 'name="service-opt"' not in text:
                errors.append(f"{page}: expected checkbox service options")
            for required in ("name", "email", "message"):
                if f'name="{required}"' not in text:
                    errors.append(f"{page}: missing {required} field")

    index = (ROOT / "index.html").read_text(encoding="utf-8")
    if "Roofing project photo" in index:
        errors.append("index.html: generic gallery alt text remains")
    if "Recent Work" not in index:
        errors.append("index.html: missing Recent Work heading")
    if "locally owned" not in index.lower():
        errors.append("index.html: missing verified locally-owned claim")
    if 'class="hero-cta"' not in index:
        errors.append("index.html: missing hero CTA")

    match = re.search(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        index,
        flags=re.S,
    )
    if not match:
        errors.append("index.html: missing JSON-LD")
    else:
        data = json.loads(match.group(1))
        if data.get("telephone") != PHONE_TEL:
            errors.append(f"index schema telephone mismatch: {data.get('telephone')}")
        if str(data.get("email", "")).startswith("mailto:"):
            errors.append("index schema email should not use mailto:")
        if not data.get("url"):
            errors.append("index schema missing url")

    services = (ROOT / "services.html").read_text(encoding="utf-8")
    for service_id in (
        "new-roofs",
        "tear-off",
        "cedar-shakes",
        "metal-roofing",
        "enviroshakes",
        "repairs",
        "gutter-cleaning",
    ):
        if f'id="{service_id}"' not in services:
            errors.append(f"services.html: missing #{service_id}")
    if "service-quote" not in services:
        errors.append("services.html: missing per-service quote links")

    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    for needle in (
        ".mobile-cta-bar",
        ".header-cta",
        ".hero-cta",
        ".service-quote",
        ".skip-link",
    ):
        if needle not in css:
            errors.append(f"styles.css missing {needle}")

    # Repo should not contain fabricated placeholder phone anywhere in HTML/CSS/XML.
    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in {".html", ".css", ".xml", ".txt", ".md"}:
            continue
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PLACEHOLDER in text or "12505550199" in text:
            errors.append(f"{path.relative_to(ROOT)}: placeholder phone leak")

    if errors:
        fail(errors)

    print("PASS: conversion, NAP, form, and landmark checks")


if __name__ == "__main__":
    main()
