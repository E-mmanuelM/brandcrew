# Template Guide — Customize Your Branded Images

BrandCrew creates branded post images using HTML/CSS templates rendered to JPG. No AI image APIs, no cost per image, pixel-perfect every time.

This guide covers how the template system works and how to customize it for your brand.

---

## How It Works

1. The Social Media Designer agent reads an approved post
2. It picks a template based on the content type (data → data card, opinion → bold text, etc.)
3. It fills template variables (headline, stats, labels) from the post content
4. `scripts/render_template.py` renders the HTML to a 1080×1350 JPG via Playwright
5. The image is sent to Telegram for your approval

---

## Available Templates

| Template | Best for | Example use |
|---|---|---|
| `editorial_data_card.html` | Single stat or data point | "73% of teams report..." |
| `transformation.html` | Before→after case studies | "Manual process → automated workflow" |
| `magazine_infographic.html` | Process or framework (≤5 steps) | "The 4-step migration plan" |
| `split_comparison.html` | Two options side by side | "Build vs buy" |
| `bold_text_metaphor.html` | Opinion post with big headline | "The dashboard nobody asked for" |
| `quote_card.html` | Hot take or quotable insight | "The best process is the one you delete" |

All templates render at 1080×1350px (LinkedIn recommended image size).

---

## Customizing Your Brand — The Theme File

All templates read from a theme file for colors and fonts. The default theme is:

```
templates/themes/default.json
```

**What you can customize:**
- Primary and secondary colors
- Background color
- Text colors (heading, body, accent)
- Font families
- Brand name or tagline

**To create your own theme:**
1. Copy `default.json` to a new file: `cp default.json my-brand.json`
2. Edit the colors and fonts to match your brand
3. Update the `DEFAULT_THEME` in `scripts/render_template.py` to point to your theme

See `templates/themes/example-editorial.json` for an example of a dark navy/gold editorial theme.

---

## Testing Templates

Test a template manually with sample data:

```bash
python3 scripts/render_template.py --template editorial_data_card --test
```

This renders a test image using `templates/sample_data.json` and saves it to the outputs folder.

---

## How the Designer Agent Picks Templates

The Social Media Designer agent reads the post content and matches it to a template:

- Post has a specific number or stat → `editorial_data_card`
- Post describes a transformation or before/after → `transformation`
- Post lists steps or a framework → `magazine_infographic`
- Post compares two approaches → `split_comparison`
- Post is a strong opinion or metaphor → `bold_text_metaphor`
- Post has a quotable insight or hot take → `quote_card`

The agent fills template variables like `{{headline}}`, `{{stat}}`, `{{label}}` from the post content. See `rules/brand-guidelines.md` for the complete design system and variable reference.

---

## Creating New Templates

If you want to add a custom template:

1. Create a new HTML file in `templates/` — use an existing template as a starting point
2. Use CSS variables from the theme file for colors (e.g., `var(--primary-color)`)
3. Use `{{placeholder}}` syntax for content the agent will fill in
4. Add an entry in the Social Media Designer's SKILL.md so it knows when to use your template
5. Test with: `python3 scripts/render_template.py --template your_template --test`

All templates must render at 1080×1350px for LinkedIn. For TikTok slides (via /repurpose), templates render at 1080×1920px (vertical).

---

## Giving Image Feedback

If an image doesn't look right:

- **Want a new image now?** → `/regenerate_image make the headline bolder` (triggers the designer with your feedback)
- **Want to log feedback for future improvement?** → `/image_feedback text is too small on mobile` (saved for the Marketing Director's weekly review)

The Marketing Director reads all image feedback weekly and updates `rules/brand-guidelines.md` when patterns emerge (e.g., 3+ similar notes about text size).
