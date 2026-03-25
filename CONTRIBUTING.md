# Contributing to BrandCrew

Thanks for wanting to help. Here's how.

---

## Report a Bug

Open a GitHub Issue. Include what happened, what you expected, and any error messages or log output.

## Suggest an Improvement

Open a GitHub Issue with the label `enhancement`. Describe what you'd like and why it would help.

---

## Easiest Ways to Contribute

**New image templates** — Create an HTML template following the format in `templates/`. Each template uses `{{placeholder}}` variables and `/* THEME_VARIABLES */` for theming. Submit a PR with your `.html` file and a matching entry in `templates/sample_data.json`.

**Niche config examples** — If you've configured BrandCrew for your industry (real estate, fitness, SaaS, finance, etc.), share your `config/niche.md`, `config/voice.md`, and `config/audience.md` as an example. We'll add it to the docs so others can learn from it.

**Documentation improvements** — Typos, clearer instructions, better examples. Every improvement helps someone get set up faster.

**New themes** — Create a new JSON theme file in `templates/themes/` with your color palette and fonts. See `themes/default.json` for the format.

---

## Submitting Changes

1. Fork the repo
2. Create a branch (`git checkout -b my-change`)
3. Make your changes
4. Test that nothing breaks
5. Submit a Pull Request with a clear description of what you changed and why

---

## Code Style

- Agent SKILL.md files follow the existing format — read a few before writing one
- Shell scripts use `set -e` and `$PROJECT_DIR` for paths
- Python follows standard formatting — nothing exotic
- Markdown config files are designed to be readable by both humans and AI agents

---

## Questions?

Open a Discussion on GitHub. We're friendly.
