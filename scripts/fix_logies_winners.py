"""Audit fixes for logies_winners.csv (mechanical, verified against live pages):

1. Flip is_winner=True for rows whose text matches the bold winner <li> on the
   live page but which were mislabelled because the winner <li> had no nested
   nominee <ul> (scraper only detected winners via nested <ul>).
2. 2026 Hall of Fame: inductees are winners (no bold in infobox) -> flip 3 rows.
3. 1993 Most Outstanding Single Documentary or Series: joint winners; fix the
   'Faces in the Mob' mid-title ' in ' split, flag both as winners.
4. Append winner rows the scraper silently dropped because the entry text
   starts with a year digit ('2006 FIFA World Cup', '2011 AFL Grand Final', ...):
   2007/2012/2014/2015/2018/2019 Sports Coverage + 2012 Most Popular Sports Program.
5. Append the two whole categories missing from the CSV (2007 & 2012
   'Most Outstanding Sports Coverage') with correct winner flags.
6. Fix 6 remaining mid-title ' in ' split rows (Rats in the Ranks, etc.).
"""
import re, csv, pandas as pd

DATA = "/root/work/data/"
ENTRY = re.compile(r"^(.*?)\s+in\s+(.*?)\s*\(([^()]*)\)\s*$")

def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("&amp;", "&").replace("&apos;", "'").replace("&#160;", " ").replace("&nbsp;", " ").strip()

def split_top(html, tag):
    return re.findall(rf"<{tag}\b[^>]*>(.*?)</{tag}>", html, flags=re.S)

def cells(html):
    html = re.sub(r'<table[^>]*navbox[^>]*>.*?</table>', '', html, flags=re.S)
    marks = [(m.start(), m.end(), m.group(1), strip_tags(m.group(2)))
             for m in re.finditer(r"<(th|td)\b[^>]*>(.*?)</\1>", html, flags=re.S)]
    pending, out = [], []
    for s, e, kind, text in marks:
        if kind == 'th':
            if ((text.startswith('Most ') or 'Gold Logie' in text or 'Award' in text
                 or 'Hall of Fame' in text) and len(text) <= 80
                    and text not in ('Most awards', 'Most nominations')):
                pending.append(text)
            continue
        if not pending:
            continue
        out.append((pending.pop(0), html[s:e]))
    return out

def parse_page(year):
    html = open(f"{DATA}_log{year}_live.html").read()
    out = []  # (category, text, bold)
    for cat, cell in cells(html):
        for li in split_top(cell, 'li'):
            bold = '<b' in li
            t = re.sub(r'\[.*?\]', '', strip_tags(re.split(r'<ul', li)[0])).strip()
            t = re.sub(r'\s+', ' ', t)
            if t:
                out.append((cat, t, bold))
    return out

def norm(s):
    s = re.sub(r'\[.*?\]', '', s).replace(' for ', ' in ')
    return re.sub(r'[^a-z0-9]', '', s.lower())

def split_row(text):
    """Return (person, program, network) using the scraper's ENTRY convention."""
    m = ENTRY.match(text)
    if m:
        return [x.strip() for x in m.groups()] + [True]   # person-form
    net = re.match(r'^(.*)\s*\(([^()]*)\)\s*$', text)
    if net and any(k in net.group(2) for k in ('Network', 'TV', 'Ten', 'ABC', 'Nine',
                                               'Seven', 'SBS', 'Foxtel', 'Stan', 'Prime',
                                               'WIN', 'NBN', 'QTV', 'BTV', 'GMV', 'SoHo',
                                               'Showcase', 'UKTV', 'Netflix', 'Binge',
                                               'NITV', 'Channel')):
        return net.group(1).strip(), '', net.group(2).strip(), False
    return text, '', '', False

w = pd.read_csv(DATA + 'logies_winners.csv')
orig_len = len(w)

# ---- gather live bold winners per (year, category) ----
live = {}
for y in range(1985, 2027):
    for cat, t, bold in parse_page(y):
        if bold:
            live.setdefault((y, cat), []).append(t)

# ---- 1+2+3: flip mislabelled rows ----
flipped = []
for i, r in w.iterrows():
    if r.is_winner:
        continue
    key = (r.year, r.category)
    if key not in live:
        continue
    t = f"{r.person} in {r.program} ({r.network})" if pd.notna(r.program) and r.program else str(r.person)
    if any(norm(t) == norm(b) for b in live[key]):
        w.at[i, 'is_winner'] = True
        flipped.append(i)
print("flipped existing rows:", len(flipped))

# ---- 5: append whole missing categories (2007 & 2012 Sports Coverage) ----
added = 0
new_rows = []
for y, cat in [(2007, 'Most Outstanding Sports Coverage'), (2012, 'Most Outstanding Sports Coverage')]:
    for c, t, bold in parse_page(y):
        if c != cat:
            continue
        person, program, network, person_form = split_row(t)
        new_rows.append({
            'year': y, 'category': cat, 'person': person, 'program': program,
            'network': network, 'is_winner': bold,
            'item_type': 'person' if person_form else 'program',
            'winner_item': program if person_form else person,
            'winner_name': person if person_form else ''})
        added += 1
print("rows appended (missing categories):", added)

# ---- 4: append year-prefixed winners dropped by the startswith('20') filter ----
have = set()
for i, r in w.iterrows():
    if r.is_winner:
        t = f"{r.person} in {r.program} ({r.network})" if pd.notna(r.program) and r.program else str(r.person)
        have.add((r.year, r.category, norm(t)))
for (y, cat), ts in live.items():
    if cat not in ('Most Outstanding Sports Coverage', 'Most Popular Sports Program'):
        continue
    for t in ts:
        if t[0].isdigit() and (y, cat, norm(t)) not in have:
            person, program, network, person_form = split_row(t)
            new_rows.append({'year': y, 'category': cat, 'person': person,
                             'program': program, 'network': network, 'is_winner': True,
                             'item_type': 'person' if person_form else 'program',
                             'winner_item': program if person_form else person,
                             'winner_name': person if person_form else ''})
            added += 1
print("rows appended total:", added)

# ---- 6: fix mid-title ' in ' split rows ----
TITLE_FIXES = {
    ('Rats', 'the Ranks'): ('Rats in the Ranks', ''),
    ('A Death', 'the Family'): ('A Death in the Family', ''),
    ('Love is', 'the Air'): ('Love is in the Air', ''),
    ('Two', 'the Top End'): ('Two in the Top End', ''),
    ('Miracle', 'the Storm'): ('Miracle in the Storm', ''),
    ('"Salma', 'the Square"'): ('"Salma in the Square"', ''),
    ('Faces', 'the Mob'): ('Faces in the Mob', ''),
}
fixed_titles = 0
for i, r in w.iterrows():
    k = (r.person, r.program)
    if k in TITLE_FIXES:
        person, program = TITLE_FIXES[k]
        w.at[i, 'person'], w.at[i, 'program'] = person, program
        fixed_titles += 1
print("mid-title splits fixed:", fixed_titles)

# ---- 1993 joint winners: ensure both bold entries flagged ----
sub = (w.year == 1993) & (w.category == 'Most Outstanding Single Documentary or Series')
w.loc[sub & w.person.isin(['Cop it Sweet (ABC TV)', 'Faces in the Mob']), 'is_winner'] = True

# ---- 2: 2026 Hall of Fame inductees are winners ----
hof = (w.year == 2026) & (w.category == 'Hall of Fame')
w.loc[hof, 'is_winner'] = True

w = pd.concat([w, pd.DataFrame(new_rows)], ignore_index=True)
w.to_csv(DATA + 'logies_winners.csv', index=False)
print("saved:", orig_len, "->", len(w))
