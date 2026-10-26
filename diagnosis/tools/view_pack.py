"""Read a sample pack one document at a time, with hidden characters made visible.

Usage:
    python view_pack.py <pack.parquet> [--start N] [--hex] [--row N] [--rows SPEC] [--sample N]

Keys:
    Enter = next document, b = back, h = toggle hex dump,
    n = next hex page, p = previous hex page, g = toggle grapheme clusters, q = quit.
"""

from __future__ import annotations

import argparse
import json
import unicodedata

import pyarrow.parquet as pq
import regex

# Rewrite VISIBLE keys as explicit unicode escape strings (prompt §4.3 item 2)
VISIBLE = {
    "\u200b": "⟦ZWSP⟧",
    "\u200c": "⟦ZWNJ⟧",
    "\u200d": "⟦ZWJ⟧",
    "\ufeff": "⟦BOM⟧",
    "\u00ad": "⟦SHY⟧",
    "\u202a": "⟦LRE⟧",
    "\u202b": "⟦RLE⟧",
    "\u202c": "⟦PDF⟧",
    "\u202d": "⟦LRO⟧",
    "\u202e": "⟦RLO⟧",
    "\u2066": "⟦LRI⟧",
    "\u2067": "⟦RLI⟧",
    "\u2068": "⟦FSI⟧",
    "\u2069": "⟦PDI⟧",
    "\ufffd": "⟦U+FFFD⟧",
    "\t": "⟦TAB⟧",
    "\r": "⟦CR⟧",
    "\u200e": "⟦LRM⟧",
    "\u200f": "⟦RLM⟧",
    "\u2060": "⟦WJ⟧",
    "\u061c": "⟦ALM⟧",
    "\u2028": "⟦LSEP⟧",
    "\u2029": "⟦PSEP⟧",
    "\u00a0": "⟦NBSP⟧",
}


def show(text: str, show_graphemes: bool = False) -> str:
    """Highlight invisible and format characters."""
    if show_graphemes:
        clusters = regex.findall(r"\X", text)
        out = []
        for cl in clusters:
            escaped_cl = "".join(VISIBLE.get(c, c) for c in cl)
            out.append(f"[{escaped_cl}]")
        return "".join(out)

    out = []
    for ch in text:
        if ch in VISIBLE:
            out.append(VISIBLE[ch])
        elif ch != "\n" and (
            unicodedata.category(ch) in ("Cc", "Cf", "Co", "Cn")
            or (unicodedata.category(ch) == "Zs" and ch != " ")
        ):
            out.append(f"⟦U+{ord(ch):04X}⟧")
        else:
            out.append(ch)
    return "".join(out)


def get_disease_mark(ch: str) -> str:
    """Return disease code for hex dump annotation."""
    cp = ord(ch)
    if ch in (
        "\u200b",
        "\ufeff",
        "\u00ad",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
        "\u2066",
        "\u2067",
        "\u2068",
        "\u2069",
    ):
        return "[A1]"
    if (0 <= cp <= 31 and ch not in ("\t", "\n")) or (127 <= cp <= 159) or ch == "\r":
        return "[A2]"
    if ch == "\ufffd":
        return "[A4]"
    return "    "


def hexdump(text: str, offset: int = 0, limit: int = 2000) -> str:
    """Hex dump with paging support (prompt §4.3 item 3 and 5)."""
    rows = []
    window = text[offset : offset + limit]
    for i, ch in enumerate(window):
        global_idx = offset + i
        if ord(ch) > 127 or unicodedata.category(ch)[0] in "CZ" or ch in VISIBLE:
            mark = get_disease_mark(ch)
            name = unicodedata.name(ch, "?")
            rows.append(f"{global_idx:6d}  U+{ord(ch):04X}  {mark}  {name}")
    header = f"--- HEX DUMP (chars {offset} to {min(len(text), offset + limit)} of {len(text)}) ---"
    body = "\n".join(rows) or "(no non-ASCII or control characters in this window)"
    return f"{header}\n{body}"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Read sample pack with invisible characters highlighted."
    )
    ap.add_argument("pack", help="Parquet pack or audit file")
    ap.add_argument("--start", type=int, default=0, help="Start at row N (0-based alias)")
    ap.add_argument("--hex", action="store_true", help="Show hex dump")
    ap.add_argument(
        "--raw", action="store_true", help="Show raw_text instead of clean_text for audit files"
    )
    ap.add_argument("--hex-window", type=int, default=2000, help="Hex dump window size")
    ap.add_argument("--json-line", action="store_true", help="Print json lines non-interactively")

    # Add selectors from datadx if available
    try:
        from datadx.selectors import add_selector_arguments, resolve

        add_selector_arguments(ap)
        has_datadx = True
    except ImportError:
        has_datadx = False

    a = ap.parse_args()

    # Load file with row-group iteration if > 5000 rows (prompt §4.3 item 8)
    pf = pq.ParquetFile(a.pack)
    num_rows = pf.metadata.num_rows

    table = pf.read_row_group(0) if num_rows > 5000 else pf.read()
    records = table.to_pylist()

    if has_datadx:
        indices = resolve(records, a)
        # Handle --start if given and no other specific selector was used
        if a.start > 0 and not any([a.row, a.doc_id, a.rows, a.doc_ids, a.sample]):
            indices = [i for i in indices if i >= a.start]
    else:
        indices = list(range(a.start, len(records)))

    if a.json_line:
        for idx in indices:
            d = records[idx]
            txt = (
                d.get("raw_text")
                if a.raw and "raw_text" in d
                else d.get("text") or d.get("clean_text") or d.get("raw_text") or ""
            )
            print(
                json.dumps(
                    {"row": idx + 1, "doc_id": d.get("doc_id", ""), "text": txt},
                    ensure_ascii=False,
                )
            )
        return

    i_ptr = 0
    hx = a.hex
    hex_offset = 0
    show_graphemes = False

    while 0 <= i_ptr < len(indices):
        idx = indices[i_ptr]
        d = records[idx]

        # Extract text field (supports original pack, audit file, and public audit)
        if a.raw and "raw_text" in d:
            text = d["raw_text"] or ""
            text_type = "raw_text"
        elif "text" in d:
            text = d["text"] or ""
            text_type = "text"
        elif "clean_text" in d:
            text = d["clean_text"] or ""
            text_type = "clean_text"
            if not text and d.get("dropped"):
                text = "[DOCUMENT DROPPED BY MEDICINE] (Pass --raw to view original raw_text)"
        elif "raw_text" in d:
            text = d["raw_text"] or ""
            text_type = "raw_text"
        else:
            text = "[Public sanitized audit file - text stripped for privacy]"
            text_type = "sanitized"

        print("\n" + "=" * 100)
        chars_cnt = len(text) if not text.startswith("[") else 0
        header_line = (
            f"[{idx + 1}/{len(records)}] doc_id={d.get('doc_id')}  "
            f"source={d.get('source')}  lang_label={d.get('lang_label')}  "
            f"chars={chars_cnt} ({text_type})"
        )
        if "verdict" in d:
            header_line += f"  verdict={d.get('verdict')}"
        print(header_line)
        if "applied_filters" in d:
            print(
                f"audit: filters={d.get('applied_filters')}  bytes_removed={d.get('bytes_removed')}  dropped={d.get('dropped')}"
            )
        if d.get("url"):
            print("url:", d["url"])
        print("-" * 100)
        print(show(text, show_graphemes=show_graphemes))

        # End of document tail block (last 300 chars, prompt §4.3 item 9)
        if len(text) > 300 and not text.startswith("["):
            print("\n" + "-" * 40 + " END OF DOCUMENT " + "-" * 40)
            print(show(text[-300:], show_graphemes=show_graphemes))

        if hx and not text.startswith("["):
            print("-" * 100)
            print(hexdump(text, offset=hex_offset, limit=a.hex_window))

        prompt_str = "\n[Enter]=next  b=back  h=hex  n=hex-next  p=hex-prev  g=graphemes  q=quit > "
        k = input(prompt_str).strip().lower()

        if k == "q":
            break
        elif k == "b":
            i_ptr -= 1
            hex_offset = 0
        elif k == "h":
            hx = not hx
        elif k == "n":
            hex_offset = min(len(text), hex_offset + a.hex_window)
        elif k == "p":
            hex_offset = max(0, hex_offset - a.hex_window)
        elif k == "g":
            show_graphemes = not show_graphemes
        else:
            i_ptr += 1
            hex_offset = 0


if __name__ == "__main__":
    main()
