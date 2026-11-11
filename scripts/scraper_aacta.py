"""Scrape AACTA winners-and-nominees pages into aacta_tv.csv.

Page contract (verified on 2026 edition): each award is a
<div id="awards-N" class="awards-list__item"> block containing an
'awards-list__title' heading and 'nominees-list__item' entries; winners carry
the extra class 'nominees-list__item--winner'. Entry text: program title in
'nominees-list__title', producers/production-company/network in '__info'.
"""
import re, time, csv, requests

H = {"User-Agent": "FIT3179-student-coursework/1.0 (educational data visualisation)"}
BASE = "https://www.aacta.org"
OUT = "/root/work/data/aacta_all.csv"
SLUGS = ["2026-aacta-awards", "2025-aacta-awards", "2024-aacta-awards", "2023-aacta-awards",
         "2022-aacta-awards", "2021-aacta-awards", "2020-aacta-awards", "2019-aacta-awards",
         "2018-aacta-awards", "7th-aacta-awards", "6th-aacta-awards", "5th-aacta-awards",
         "4th-aacta-awards", "3rd-aacta-awards", "2nd-aacta-awards", "inaugural-aacta-awards"]
YEAR_OF = {"2026-aacta-awards": 2026, "2025-aacta-awards": 2025, "2024-aacta-awards": 2024,
           "2023-aacta-awards": 2023, "2022-aacta-awards": 2022, "2021-aacta-awards": 2021,
           "2020-aacta-awards": 2020, "2019-aacta-awards": 2019, "2018-aacta-awards": 2018,
           "7th-aacta-awards": 2017, "6th-aacta-awards": 2016, "5th-aacta-awards": 2015,
           "4th-aacta-awards": 2014, "3rd-aacta-awards": 2013, "2nd-aacta-awards": 2012,
           "inaugural-aacta-awards": 2011}
TV_WORDS = re.compile(r"drama|comedy|entertainment|factual|lifestyle|reality|children|"
                      r"actor|actress|television|scripted|presenter|documentary", re.I)

def clean(s):
    s = re.sub(r"<[^>]+>", "|", s)
    s = re.sub(r"\|{2,}", "|", s)
    parts = [p.strip() for p in s.split("|") if p.strip()]
    return parts

def parse(html, edition):
    rows = []
    for block in re.split(r'<div[^>]*class="awards-list__item"', html)[1:]:
        tm = re.search(r'awards-list__title[^>]*>(.*?)</', block, re.S)
        if not tm:
            continue
        parts = clean(tm.group(1))
        category = parts[0] if parts else ""
        if not TV_WORDS.search(category):
            continue
        for item in re.split(r'class="nominees-list__item', block)[1:]:
            winner = "nominees-list__item--winner" in item[:300]
            title = re.search(r'nominees-list__title[^>]*>(.*?)</span>', item, re.S)
            info = re.search(r'nominees-list__info[^>]*>(.*?)</div>', item, re.S)
            prog = clean(title.group(1)) if title else []
            inf = clean(info.group(1)) if info else []
            rows.append({"edition": edition, "year": YEAR_OF[edition],
                         "category": category, "program": "; ".join(prog),
                         "detail": " | ".join(inf), "is_winner": winner})
    return rows

def fetch(url, tries=4):
    for a in range(tries):
        try:
            r = requests.get(url, headers=H, timeout=30)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(2 * (a + 1))
    return None

def main():
    all_rows = []
    for slug in SLUGS:
        html = fetch(f"{BASE}/aacta-awards/winners-and-nominees/{slug}/")
        if html is None:
            print(slug, "FAILED"); continue
        rows = parse(html, slug)
        all_rows.extend(rows)
        wins = sum(r["is_winner"] for r in rows)
        print(slug, len(rows), "entries", wins, "winners", flush=True)
        time.sleep(0.8)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["edition", "year", "category", "program", "detail", "is_winner"])
        w.writeheader()
        w.writerows(all_rows)
    print("TOTAL", len(all_rows))

if __name__ == "__main__":
    main()
