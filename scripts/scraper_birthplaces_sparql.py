"""Birthplaces via Wikidata SPARQL: batch people into VALUES clauses, fetch
label(P19) + P625 coordinates in one query per batch of 40 names.
Names that SPARQL cannot match fall back to enwiki pageprops (few cases).
"""
import csv, json, re, time, requests

SPARQL = "https://query.wikidata.org/sparql"
UA = {"User-Agent": "FIT3179-student-coursework/1.0 (educational data visualisation)"}
OUT = "/root/work/data/people_birthplaces.csv"

def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')

def q(batch):
    values = " ".join(f'"{esc(n)}"@en' for n in batch)
    query = f"""
SELECT ?personLabel ?birthLabel ?coord WHERE {{
  VALUES ?personLabel {{{values}}}
  ?person rdfs:label ?personLabel. FILTER(LANG(?personLabel)="en")
  ?person wdt:P19 ?birth.
  OPTIONAL {{ ?birth wdt:P625 ?coord. }}
  ?birth rdfs:label ?birthLabel. FILTER(LANG(?birthLabel)="en")
}}
"""
    for a in range(5):
        try:
            r = requests.get(SPARQL, params={"query": query, "format": "json"},
                             headers=UA, timeout=60)
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
        except requests.RequestException:
            pass
        time.sleep(3 * (a + 1))
    return None

def main():
    people = [r["person"] for r in csv.DictReader(open("/root/work/data/people_to_geocode.csv"))]
    found = {}
    for i in range(0, len(people), 40):
        batch = people[i:i + 40]
        rows = q(batch)
        if rows is None:
            print("batch", i, "FAILED"); continue
        for b in rows:
            name = b["personLabel"]["value"]
            if name not in found:   # first match wins
                coord = b.get("coord", {}).get("value", "")
                lon, lat = "", ""
                m = re.match(r"Point\((-?[\d.]+) (-?[\d.]+)\)", coord)
                if m:
                    lon, lat = float(m.group(1)), float(m.group(2))
                found[name] = {"person": name, "birthplace": b["birthLabel"]["value"],
                               "lat": lat, "lon": lon, "flag": ""}
        print(f"batch {i}-{i + len(batch)}: {len(found)} total matched", flush=True)
        time.sleep(2)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["person", "birthplace", "lat", "lon", "flag"])
        w.writeheader()
        for name in people:
            r = found.get(name, {"person": name, "birthplace": "", "lat": "", "lon": "", "flag": "not found"})
            w.writerow(r)
    print("matched", len(found), "of", len(people),
          "; unmatched:", [n for n in people if n not in found])

if __name__ == "__main__":
    main()
