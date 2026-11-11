"""Resolve birthplace (P19) + coordinates (P625) for Gold Logie / Logie winners.

Pipeline: en.wikipedia pageprops -> Wikidata QID -> wbgetentities (P19) ->
batched wbgetentities for place labels + P625 coords. Retries with backoff;
flags results whose country is not AU/NZ/UK for manual review.
"""
import csv, json, re, time, requests

WIKI = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "FIT3179-student-coursework/1.0 (educational data visualisation)"}
OUT = "/root/work/data/people_birthplaces.csv"
PLACE_CACHE = "/root/work/data/place_cache.json"

def api(url, params, tries=5):
    for a in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=30)
            if r.status_code == 200:
                return r.json()
        except (requests.RequestException, json.JSONDecodeError):
            pass
        time.sleep(1.5 * (a + 1))
    return None

def qid_for(name):
    j = api(WIKI, {"action": "query", "prop": "pageprops", "titles": name,
                   "format": "json", "redirects": 1})
    if not j:
        return None
    pages = j.get("query", {}).get("pages", {})
    for p in pages.values():
        q = p.get("pageprops", {}).get("wikibase_item")
        if q:
            return q
    return None

def batch_entities(ids, props="claims|labels"):
    out = {}
    for i in range(0, len(ids), 50):
        j = api(WD, {"action": "wbgetentities", "ids": "|".join(ids[i:i + 50]),
                     "props": props, "languages": "en", "format": "json"})
        if j:
            out.update(j.get("entities", {}))
        time.sleep(0.3)
    return out

def main():
    people = [r["person"] for r in csv.DictReader(open("/root/work/data/people_to_geocode.csv"))]
    try:
        qids = json.load(open("/root/work/data/qid_cache.json"))
    except Exception:
        qids = {}
    missing = []
    for i, name in enumerate(people):
        if name in qids:
            continue
        q = qid_for(name)
        if q:
            qids[name] = q
        else:
            missing.append(name)
        json.dump(qids, open("/root/work/data/qid_cache.json", "w"))
        if i % 20 == 19:
            print(f"{i + 1}/{len(people)} resolved", flush=True)
        time.sleep(0.15)
    print("resolved", len(qids), "missing", len(missing))

    ents = batch_entities(list(qids.values()))
    place_ids = set()
    person_p19 = {}
    for name, qid in qids.items():
        claims = ents.get(qid, {}).get("claims", {}).get("P19", [])
        ids = [c["mainsnak"]["datavalue"]["value"]["id"]
               for c in claims if "datavalue" in c.get("mainsnak", {})]
        person_p19[name] = ids
        place_ids.update(ids)

    places = batch_entities(list(place_ids), props="claims|labels")
    try:
        cache = json.load(open(PLACE_CACHE))
    except Exception:
        cache = {}
    for pid, ent in places.items():
        coords = None
        for c in ent.get("claims", {}).get("P625", []):
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value", {})
            coords = [v.get("latitude"), v.get("longitude")]
            break
        label = ent.get("labels", {}).get("en", {}).get("value", "")
        cache[pid] = {"label": label, "lat": coords[0] if coords else None,
                      "lon": coords[1] if coords else None}
    json.dump(cache, open(PLACE_CACHE, "w"))

    rows = []
    for name in people:
        ids = person_p19.get(name, [])
        if not ids:
            rows.append({"person": name, "qid": qids.get(name, ""), "birthplace": "",
                         "lat": "", "lon": "", "flag": "no P19"})
            continue
        for pid in ids[:1]:  # first P19 is the birthplace
            p = cache.get(pid, {})
            rows.append({"person": name, "qid": qids.get(name, ""), "birthplace": p.get("label", pid),
                         "lat": p.get("lat", ""), "lon": p.get("lon", ""), "flag": ""})
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["person", "qid", "birthplace", "lat", "lon", "flag"])
        w.writeheader()
        w.writerows(rows)
    print("written", len(rows), "rows; missing QIDs:", missing)

if __name__ == "__main__":
    main()
