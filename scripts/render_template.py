#!/usr/bin/env python3
"""
render_template.py — HTML/CSS template → JPG image renderer for BrandCrew.

Uses Playwright to screenshot HTML templates at 1080x1350 (LinkedIn portrait).
Zero API cost. Pixel-perfect. Fully controllable.

OUTPUT: JPG at 1080x1350, ~80-150KB. LinkedIn-ready.
DO NOT use 2x device_scale_factor — LinkedIn chokes on oversized images.

Usage:
    python3 scripts/render_template.py --template editorial_data_card --vars '{"headline": "..."}'
    python3 scripts/render_template.py --template editorial_data_card --vars-file /tmp/template-vars.json
    python3 scripts/render_template.py --draft-id <uuid>  # reads template_name + template_vars from Supabase
    python3 scripts/render_template.py --list  # list available templates
    python3 scripts/render_template.py --preview editorial_data_card  # render with sample data

Requirements:
    pip install playwright Pillow --break-system-packages
    playwright install chromium
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(REPO_DIR, "templates")
THEME_DIR = os.path.join(TEMPLATE_DIR, "themes")
IMAGE_DIR = os.path.join(REPO_DIR, "generated_images")

# LinkedIn portrait dimensions — EXACT output size, no retina scaling
WIDTH = 1080
HEIGHT = 1350
DEVICE_SCALE = 1  # 1x ONLY. 2x produces 2160x2700 which LinkedIn rejects/hangs on upload.
JPG_QUALITY = 90  # Good quality, small file size (~80-150KB)

DEFAULT_THEME = "default"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_theme(theme_name=None):
    """Load a theme JSON file. Returns dict of CSS variables and font imports."""
    name = theme_name or DEFAULT_THEME
    theme_path = os.path.join(THEME_DIR, f"{name}.json")
    if not os.path.exists(theme_path):
        print(f"WARNING: Theme '{name}' not found at {theme_path}, using defaults")
        return {}
    with open(theme_path, "r") as f:
        return json.load(f)


def list_templates():
    """List all available template HTML files."""
    templates = []
    for f in sorted(Path(TEMPLATE_DIR).glob("*.html")):
        templates.append(f.stem)
    return templates


def load_template(template_name):
    """Load an HTML template file."""
    path = os.path.join(TEMPLATE_DIR, f"{template_name}.html")
    if not os.path.exists(path):
        print(f"ERROR: Template '{template_name}' not found at {path}")
        print(f"Available templates: {', '.join(list_templates())}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def inject_variables(html, variables, theme):
    """Replace {{variable}} placeholders in HTML with actual values.
    Also injects theme CSS variables into the <style> block.
    """
    # Inject theme CSS variables
    if theme and "css_variables" in theme:
        css_vars = "\n".join(
            f"    {k}: {v};" for k, v in theme["css_variables"].items()
        )
        css_root = f":root {{\n{css_vars}\n  }}"
        html = html.replace("/* THEME_VARIABLES */", css_root)

    # Inject Google Fonts import if theme specifies it
    if theme and "font_import" in theme:
        html = html.replace("/* FONT_IMPORT */", theme["font_import"])

    # Replace {{variable}} placeholders
    for key, value in variables.items():
        if isinstance(value, list):
            continue
        placeholder = "{{" + key + "}}"
        html = html.replace(placeholder, str(value))

    # Handle list items: {{items}} becomes repeated HTML blocks
    # Templates use <!-- REPEAT:items --> ... <!-- END:items --> markers
    for key, value in variables.items():
        if not isinstance(value, list):
            continue
        repeat_pattern = f"<!-- REPEAT:{key} -->(.+?)<!-- END:{key} -->"
        match = re.search(repeat_pattern, html, re.DOTALL)
        if match:
            item_template = match.group(1)
            rendered_items = []
            for i, item in enumerate(value):
                rendered = item_template
                if isinstance(item, dict):
                    for ik, iv in item.items():
                        rendered = rendered.replace("{{" + ik + "}}", str(iv))
                else:
                    rendered = rendered.replace("{{item}}", str(item))
                rendered = rendered.replace("{{index}}", str(i + 1))
                rendered_items.append(rendered)
            html = html[:match.start()] + "\n".join(rendered_items) + html[match.end():]

    return html


def render_to_image(html, output_path):
    """Use Playwright to render HTML to JPG at LinkedIn dimensions.

    Renders at exactly 1080x1350 (1x scale), converts to JPG for
    maximum LinkedIn compatibility and fast upload.
    """
    from playwright.sync_api import sync_playwright
    from PIL import Image

    # Render to temporary PNG first (Playwright only does PNG)
    temp_png = output_path + ".tmp.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=DEVICE_SCALE,
        )
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(1500)  # Wait for fonts to load
        page.screenshot(path=temp_png, type="png")
        browser.close()

    # Convert to JPG for LinkedIn compatibility
    img = Image.open(temp_png)
    img = img.convert("RGB")

    # Determine output format from extension
    if output_path.lower().endswith(".png"):
        img.save(output_path, "PNG", optimize=True)
    else:
        # Default to JPG
        if not output_path.lower().endswith((".jpg", ".jpeg")):
            output_path = output_path.rsplit(".", 1)[0] + ".jpg" if "." in output_path else output_path + ".jpg"
        img.save(output_path, "JPEG", quality=JPG_QUALITY, optimize=True)

    # Clean up temp file
    if os.path.exists(temp_png):
        os.remove(temp_png)

    file_size = os.path.getsize(output_path)
    print(f"  Rendered: {output_path} ({file_size:,} bytes, {img.size[0]}x{img.size[1]})")

    # Warn if file seems too large for LinkedIn
    if file_size > 5_000_000:
        print(f"  WARNING: File size {file_size:,} bytes exceeds LinkedIn's 5MB limit!")
    elif file_size > 2_000_000:
        print(f"  WARNING: File size {file_size:,} bytes is large — may upload slowly on mobile")

    return output_path


def get_supabase():
    """Initialize Supabase client."""
    from dotenv import load_dotenv
    from supabase import create_client
    load_dotenv(os.path.join(REPO_DIR, ".env"))
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_SECRET_KEY not set in .env")
        sys.exit(1)
    return create_client(url, key)


def log_to_supabase(sb, status, details, image_path=None):
    """Write a row to agent_logs."""
    try:
        row = {
            "agent_name": "social_media_designer",
            "action": "render_template",
            "status": status,
            "details": details[:2000] if details else None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if image_path:
            row["output_summary"] = image_path
        sb.table("agent_logs").insert(row).execute()
    except Exception as e:
        print(f"WARNING: Failed to write agent_logs: {e}")


def load_sample_data(template_name):
    """Load sample data for preview mode."""
    samples_path = os.path.join(TEMPLATE_DIR, "sample_data.json")
    if os.path.exists(samples_path):
        with open(samples_path, "r") as f:
            samples = json.load(f)
        if template_name in samples:
            return samples[template_name]
    print(f"WARNING: No sample data for '{template_name}', using empty vars")
    return {}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Render HTML template to image for LinkedIn")
    parser.add_argument("--template", "-t", help="Template name (without .html)")
    parser.add_argument("--vars", "-v", help="JSON string of template variables")
    parser.add_argument("--vars-file", help="Path to JSON file with template variables")
    parser.add_argument("--draft-id", help="Read template_name + template_vars from Supabase draft")
    parser.add_argument("--theme", default=DEFAULT_THEME, help=f"Theme name (default: {DEFAULT_THEME})")
    parser.add_argument("--output", "-o", help="Output file path (default: generated_images/timestamp.jpg)")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--preview", help="Render template with sample data")
    parser.add_argument("--png", action="store_true", help="Output PNG instead of JPG (larger file)")
    args = parser.parse_args()

    ext = ".png" if args.png else ".jpg"

    # List mode
    if args.list:
        templates = list_templates()
        print(f"Available templates ({len(templates)}):")
        for t in templates:
            print(f"  - {t}")
        return

    # Preview mode
    if args.preview:
        template_name = args.preview
        variables = load_sample_data(template_name)
        theme = load_theme(args.theme)
        html = load_template(template_name)
        html = inject_variables(html, variables, theme)
        os.makedirs(IMAGE_DIR, exist_ok=True)
        output = args.output or os.path.join(IMAGE_DIR, f"preview_{template_name}{ext}")
        render_to_image(html, output)
        print(f"\nSUCCESS: {output}")
        return

    # Draft mode — read from Supabase
    if args.draft_id:
        sb = get_supabase()
        result = sb.table("content_drafts").select(
            "id, template_name, template_vars, status"
        ).eq("id", args.draft_id).limit(1).execute()

        if not result.data:
            print(f"ERROR: Draft {args.draft_id} not found")
            sys.exit(1)

        draft = result.data[0]
        template_name = draft.get("template_name")
        variables = draft.get("template_vars") or {}
        if isinstance(variables, str):
            variables = json.loads(variables)

        if not template_name:
            print(f"ERROR: Draft {args.draft_id} has no template_name set")
            log_to_supabase(sb, "failed", f"Draft {args.draft_id} missing template_name")
            sys.exit(1)

        theme = load_theme(args.theme)
        html = load_template(template_name)
        html = inject_variables(html, variables, theme)

        os.makedirs(IMAGE_DIR, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_id = args.draft_id[:8]
        output = args.output or os.path.join(IMAGE_DIR, f"{timestamp}_{short_id}{ext}")

        print(f"\n--- Rendering template '{template_name}' for draft {args.draft_id} ---")
        render_to_image(html, output)

        # Update Supabase
        sb.table("content_drafts").update({
            "image_url": output,
        }).eq("id", args.draft_id).execute()
        print(f"  Updated content_drafts.image_url for {args.draft_id}")

        log_to_supabase(sb, "completed", f"Rendered {template_name} for draft {args.draft_id}", output)
        print(f"\nSUCCESS: {output}")
        return

    # Direct mode — template + vars
    if not args.template:
        print("ERROR: --template, --draft-id, --list, or --preview required")
        parser.print_help()
        sys.exit(1)

    template_name = args.template
    variables = {}
    if args.vars:
        variables = json.loads(args.vars)
    elif args.vars_file:
        with open(args.vars_file, "r") as f:
            variables = json.load(f)

    theme = load_theme(args.theme)
    html = load_template(template_name)
    html = inject_variables(html, variables, theme)

    os.makedirs(IMAGE_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = args.output or os.path.join(IMAGE_DIR, f"{timestamp}_{template_name}{ext}")

    print(f"\n--- Rendering template '{template_name}' ---")
    render_to_image(html, output)
    print(f"\nSUCCESS: {output}")


if __name__ == "__main__":
    main()
