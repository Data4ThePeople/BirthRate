"""Inline the data payload into the template to produce the publishable artifact."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    template = (HERE / "template.html").read_text()
    data = (HERE / "fertility_data.json").read_text()

    # The payload sits inside a <script type="application/json"> block, so the
    # only sequence that could break out of it is a literal closing script tag.
    if "</script" in data.lower():
        raise ValueError("payload contains a closing script tag")

    page = template.replace("__DATA__", data)
    out = HERE / "fertility.html"
    out.write_text(page)
    print(f"wrote {out}  {out.stat().st_size/1e6:.2f} MB")

    obj = json.loads(data)
    print(f"  years {obj['years'][0]}-{obj['years'][-1]}, "
          f"{len(obj['units'])} units, {len(obj['geo'])} geometries")


if __name__ == "__main__":
    main()
