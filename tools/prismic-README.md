# Prismic publisher

Shared tooling for pushing Markdown from any local project into Prismic as
drafts. Used by the `prismic-publisher` agent, and usable directly.

    ./prismic --check                  # which APIs the token can use
    ./prismic --list-types             # types, fields and slice zones
    ./prismic path/to/*.md --publish -n   # dry run
    ./prismic path/to/*.md --publish      # upload images, create drafts

`prismic` is a wrapper around `.venv/bin/python to_prismic.py`, so it carries
its own `requests` and `Pillow` and does not depend on the project it runs in.

Created pages land in the **Migration Release**, not in the main document list -
review and publish them from there. Uploaded images go straight to the media
library, so images showing up while the page appears missing is expected.

`--verify UID` reads a created page back and reports which release holds it and
what actually landed. It needs `PRISMIC_READ_TOKEN`, a Content API access token,
since a write token cannot read.

Credentials are read from the first of: `$PRISMIC_ENV`, `./.env` in the project
being published, `.env` here, then `~/.prismic.env`. The copy here is mode 600
and holds a write token - Prismic → Settings → API & Security → **Write APIs**,
not the access token above it.

`to_prismic.py` and `prismic_slices.py` are kept identical to the copies in the
BirthRate project, which is where they are developed. To reinstall after a
change there:

    cp ~/PycharmProjects/BirthRate/posts/{to_prismic,prismic_slices}.py \
       ~/.claude/tools/prismic/
