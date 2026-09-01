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
PAGES = ["index.html", "services.html", "contact.html", "404.html"]

DISPLAY_PHONE_RE = re.compile(r"\b(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b")
TEL_HREF_RE = re.compile(r"""href=["']tel:([^"']+)["']""", re.I)
JSON_LD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)


def fail(errors: list[str]) -> None:
    print("FAIL")
    for item in errors:
        print(f"- {item}")
    raise SystemExit(1)


def normalize_phone(raw: str) -> str | None:
    """Normalize a phone-like string to E.164 (+1XXXXXXXXXX) or None if invalid."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if len(digits) == 10:
        return f"+1{digits}"
    return None


def collect_schema_telephones(node: object, found: list[str] | None = None) -> list[str]:
    if found is None:
        found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "telephone" and isinstance(value, str):
                found.append(value)
            else:
                collect_schema_telephones(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_schema_telephones(item, found)
    return found


def nap_mismatches(text: str, source: str) -> list[str]:
    """Return errors for every phone occurrence that is not the canonical number."""
    errors: list[str] = []
    canonical = normalize_phone(PHONE_TEL)
    assert canonical is not None

    for match in DISPLAY_PHONE_RE.finditer(text):
        raw = match.group(1)
        normalized = normalize_phone(raw)
        if normalized != canonical:
            errors.append(f"{source}: non-canonical display phone {raw!r} -> {normalized}")

    for match in TEL_HREF_RE.finditer(text):
        raw = match.group(1)
        normalized = normalize_phone(raw)
        if normalized != canonical:
            errors.append(f"{source}: non-canonical tel: target {raw!r} -> {normalized}")

    for block in JSON_LD_RE.findall(text):
        try:
            data = json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"{source}: invalid JSON-LD ({exc})")
            continue
        for raw in collect_schema_telephones(data):
            normalized = normalize_phone(raw)
            if normalized != canonical:
                errors.append(
                    f"{source}: non-canonical schema telephone {raw!r} -> {normalized}"
                )

    return errors


def run_negative_nap_regression() -> list[str]:
    """Prove stray/stale numbers fail the NAP matcher."""
    errors: list[str] = []
    fixtures = [
        (
            "stray display phone",
            '<a href="tel:+12505088820">Call 250-508-8820</a><span>250-555-0199</span>',
            "250-555-0199",
        ),
        (
            "stale tel target",
            '<a href="tel:+12505088821">Call 250-508-8820</a>',
            "+12505088821",
        ),
        (
            "stale ContactPage schema telephone",
            """
            <a href="tel:+12505088820">250-508-8820</a>
            <script type="application/ld+json">
            {
              "@type": "ContactPage",
              "mainEntity": {"@type": "RoofingContractor", "telephone": "+12505088821"}
            }
            </script>
            """,
            "+12505088821",
        ),
    ]

    for label, html, expected_token in fixtures:
        mismatches = nap_mismatches(html, f"negative:{label}")
        if not mismatches:
            errors.append(f"negative regression did not fail for {label}")
            continue
        joined = " ".join(mismatches)
        if expected_token not in joined and normalize_phone(expected_token) not in joined:
            errors.append(
                f"negative regression for {label} missed expected token {expected_token!r}: {mismatches}"
            )

    # Canonical-only fixture must pass.
    clean = (
        '<a href="tel:+12505088820">Call 250-508-8820</a>'
        '<script type="application/ld+json">'
        '{"telephone": "+12505088820"}'
        "</script>"
    )
    clean_errors = nap_mismatches(clean, "negative:canonical-control")
    if clean_errors:
        errors.append(f"negative regression false positive on canonical fixture: {clean_errors}")

    return errors


def main() -> None:
    errors: list[str] = []

    for page in PAGES:
        path = ROOT / page
        if not path.exists():
            errors.append(f"{page}: missing file")
            continue
        text = path.read_text(encoding="utf-8")

        errors.extend(nap_mismatches(text, page))

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
    if "Project Gallery" not in index:
        errors.append("index.html: missing Project Gallery heading")
    if re.search(r"recent\s+work", index, flags=re.I):
        errors.append("index.html: unsupported Recent Work freshness claim remains")
    if re.search(r"locally\s+owned", index, flags=re.I):
        errors.append("index.html: unsupported locally owned claim remains")
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
        if normalize_phone(str(data.get("telephone", ""))) != normalize_phone(PHONE_TEL):
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

    # Repo-wide NAP scan for HTML/CSS/XML/TXT (skip check script itself docs that mention placeholders in fixtures).
    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in {".html", ".css", ".xml", ".txt", ".md"}:
            continue
        if ".git" in path.parts or path.name == "check-site.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = str(path.relative_to(ROOT))
        errors.extend(nap_mismatches(text, rel))
        if re.search(r"locally\s+owned", text, flags=re.I):
            errors.append(f"{rel}: unsupported locally owned claim remains")

    errors.extend(run_negative_nap_regression())

    if errors:
        fail(errors)

    print("PASS: conversion, NAP, form, landmark, and negative NAP regression checks")


if __name__ == "__main__":
    main()
