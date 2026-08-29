# Cross-project tooling

These are the source copies of things installed outside the repo, kept here so
they are version-controlled and reproducible.

| File | Installed to |
|---|---|
| `prismic-publisher.agent.md` | `~/.claude/agents/prismic-publisher.md` |
| `prismic-README.md` | `~/.claude/tools/prismic/README.md` |
| `../posts/to_prismic.py` | `~/.claude/tools/prismic/to_prismic.py` |
| `../posts/prismic_slices.py` | `~/.claude/tools/prismic/prismic_slices.py` |

Reinstall after changing any of them:

```bash
cp tools/prismic-publisher.agent.md ~/.claude/agents/prismic-publisher.md
cp tools/prismic-README.md          ~/.claude/tools/prismic/README.md
cp posts/{to_prismic,prismic_slices}.py ~/.claude/tools/prismic/
```

The install also carries its own virtualenv (`~/.claude/tools/prismic/.venv`
with `requests` and `pillow`) and a `prismic` wrapper, so it runs from any
project. Credentials live in `~/.claude/tools/prismic/.env`, mode 600, and are
not in this repository.
