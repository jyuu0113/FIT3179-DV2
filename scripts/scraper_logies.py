"""Scrape Logie Awards per-year Wikipedia pages into logies_winners.csv.

Contract (verified on 2010 page): each awards table row has a <th> holding the
category name and a <td> holding a <ul> of <li> entries; winners are wrapped
in <b>, nominees are plain. Entries read 'Name in Program (Network)'.
"""
import re, time, sys, csv, requests

H = {"User-Agent": "FIT3179-student-coursework/1.0 (educational data visualisation; contact: student)"}
OUT = "/root/work/data/logies_winners.csv"
ENTRY = re.compile(r"^(.*?)\s+in\s+(.*?)\s*\(([^()]*)\)\s*$")

def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("&amp;", "&").replace("&apos;", "'").replace("&#160;", " ").replace("&nbsp;", " ").strip()

def split_top(html, tag):
    """Split html into top-level <tag>...</tag> chunks (no nesting)."""
    return re.findall(rf"<{tag}\b[^>]*>(.*?)</{tag}>", html, flags=re.S)

def strip_navboxes(html):
    html = re.sub(r'<table[^>]*navbox[^>]*>.*?</table>', '', html, flags=re.S)
    return html

def parse_page(html):
    html = strip_navboxes(html)
    rows = []
    # Award categories (<th>) pair FIFO with their entry cells (<td>):
    # two-column tables emit th,th,td,td — the first td belongs to the first th.
    marks = [(m.start(), m.end(), m.group(1), strip_tags(m.group(2)))
             for m in re.finditer(r"<(th|td)\b[^>]*>(.*?)</\1>", html, flags=re.S)]
    pending = []
    for start, end, kind, text in marks:
        if kind == "th":
            if ((text.startswith("Most ") or "Gold Logie" in text
                 or "Award" in text or "Hall of Fame" in text)
                    and len(text) <= 80 and text not in ("Most awards", "Most nominations")):
                pending.append(text)
            continue
        if not pending:
            continue
        category = pending.pop(0)
        cell = html[start:end]

        def emit(li_html, winner):
            text = strip_tags(re.split(r"<ul", li_html)[0])
            text = re.sub(r"\[.*?\]", "", text)
            m = ENTRY.match(text)
            person, program, network = ([x.strip() for x in m.groups()] if m
                                        else (text, "", ""))
            if person and not person.startswith(("←", "Logie Awards", "20")):
                rows.append({"category": category, "person": person,
                             "program": program, "network": network,
                             "is_winner": winner})

        for li in split_top(cell, "li"):
            if "<ul" in li:      # winner entry followed by nested nominee list
                emit(li, True)
                for sub in split_top(re.split(r"<ul", li, 1)[1], "li"):
                    emit(sub, False)
            else:
                emit(li, False)
    return rows

def fetch(url, tries=4):
    for a in range(tries):
        try:
            r = requests.get(url, headers=H, timeout=30)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(2 * (a + 1))
    return None

def main(years):
    all_rows, done = [], []
    for y in years:
        html = fetch(f"https://en.wikipedia.org/wiki/Logie_Awards_of_{y}")
        if html is None:
            print(y, "SKIP (no page/404)", flush=True)
            continue
        rows = parse_page(html)
        for r in rows:
            r["year"] = y
        all_rows.extend(rows)
        done.append(y)
        print(y, len(rows), flush=True)
        time.sleep(0.6)
    if all_rows:
        mode = "a" if done and len(done) < len(years) and __import__("os").path.exists(OUT) else "w"
        with open(OUT, mode, newline="") as f:
            w = csv.DictWriter(f, fieldnames=["year", "category", "person", "program", "network", "is_winner"])
            if mode == "w":
                w.writeheader()
            w.writerows(all_rows)
    print("TOTAL", len(all_rows), "years done:", done)

if __name__ == "__main__":
    years = list(range(1959, 2027))
    main(years)
