"""Rebuild every Gold Logie person-level dataset from the CLEANED win list.

Rules (verified against Wikipedia's Gold Logie article, 2026-11-11):
- One Gold Logie win per person per year; Wikipedia lists a nominee once per
  associated program, so a winner-year collapses to the first-listed program.
- Special Gold Logies (Neil Armstrong & Buzz Aldrin 1970; Bob and Dolly Dyer 1971)
  are excluded: the story is the public vote.
- The Gold Logie was first awarded in 1960; the 1959 "Star of the Year" row in
  gold_logie_winners.csv is a predecessor award and is not a Gold Logie win.
- Winner's network = network of the first-listed program (Wikipedia order).
"""
import json, math
import pandas as pd

DATA = "/root/work/data"
SITE = "/root/work/site/data"

LABEL = {"variety": "Variety & talk show hosts", "comedy": "Comedy performers",
         "drama": "Drama & soap actors", "news": "News & current affairs",
         "lightent": "Light entertainment & reality hosts", "special": "Special broadcast"}
SPECIALS = {"Neil Armstrong and Buzz Aldrin", "Bob and Dolly Dyer"}

def clean_wins():
    n = pd.read_csv(f"{DATA}/gold_logie_nominees.csv")
    wins = n[(n["is_winner"]) & n["person"].notna()].copy()
    wins = wins.drop_duplicates(subset=["year", "person"], keep="first")
    wins = wins[~wins["person"].isin(SPECIALS)]
    return wins.reset_index(drop=True)

def main():
    wins = clean_wins()
    wins["star_type_label"] = wins["person"].map(
        lambda p: {"Graham Kennedy": "Variety & talk show hosts"}.get(p))  # placeholder, fixed below
    import sys
    sys.path.insert(0, "/root/work")
    from star_type_lookup import LOOKUP
    wins["star_type_label"] = wins["person"].map(LOOKUP).map(LABEL)
    wins["decade"] = ((wins["year"] // 10) * 10).astype(str) + "s"
    wins[["year", "decade", "person", "star_type_label", "program", "network"]] \
        .to_csv(f"{SITE}/gold_logie_wins_typed.csv", index=False)

    # repeat winners
    rep = (wins.groupby("person")
           .agg(first_win=("year", "min"), last_win=("year", "max"), total_wins=("year", "count"),
                networks=("network", lambda s: ", ".join(sorted(set(s.astype(str))))),
                programs=("program", lambda s: ", ".join(sorted(set(s.astype(str))))))
           .reset_index())
    rep = rep[rep["total_wins"] > 1].sort_values("total_wins", ascending=False)
    rep["star_type_label"] = rep["person"].map(LOOKUP).map(LABEL)
    rep.to_csv(f"{SITE}/gold_logie_repeat_winners.csv", index=False)

    # gender
    bio = json.load(open(f"{DATA}/people_bio_cache.json"))
    ALT = {"Ally Langdon": "Allison Langdon", "Bec Cartwright": "Rebecca Cartwright",
           "Norman Gunston": "Garry McDonald"}
    g = {"male": "Male", "female": "Female"}
    wins["gender"] = wins["person"].map(
        lambda p: g.get(bio.get(ALT.get(p, p), {}).get("gender", ""), "Unknown"))
    wins[["year", "decade", "person", "gender"]].to_csv(f"{SITE}/gold_logie_wins_gender.csv", index=False)

    # per-year network table + reign years + decade totals
    yearly = (wins.groupby(["year", "network"]).size().reset_index(name="wins"))
    yearly["rank"] = yearly.groupby("year")["wins"].rank("dense", ascending=False).astype(int)
    yearly.to_csv(f"{SITE}/gold_logie_network_major.csv", index=False)
    years = yearly[["network", "year"]].sort_values(["year", "network"])
    years["next_year"] = years["year"] + 1
    years.to_csv(f"{SITE}/gold_logie_network_years.csv", index=False)
    dec = (wins.groupby(["decade", "network"]).size().reset_index(name="wins"))
    decs = [f"{d}s" for d in range(1960, 2030, 10)]
    nets = ["Nine", "Seven", "Ten", "ABC"]
    full = pd.MultiIndex.from_product([decs, nets], names=["decade", "network"]).to_frame(index=False)
    dec = full.merge(dec, how="left", on=["decade", "network"]).fillna({"wins": 0})
    dec["wins"] = dec["wins"].astype(int)
    dec.to_csv(f"{SITE}/network_decade_totals.csv", index=False)

    # ---------- birthplace-derived maps (winners only) ----------
    b = pd.read_csv(f"{DATA}/people_birthplaces.csv")
    tot = wins.groupby("person").size().rename("gold_wins")
    b["gold_wins"] = b["person"].map(tot).fillna(0).astype(int)
    b.to_csv(f"{DATA}/people_birthplaces.csv", index=False)
    win = b[(b["person"].isin(tot.index)) & b["state"].isin(
        ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT"])]
    ov = b[(b["person"].isin(tot.index)) & (b["state"] == "Overseas")].copy()

    # state counts
    st = win.groupby("state").size().reset_index(name="winners")
    STATE_NAME = {"NSW": "New South Wales", "VIC": "Victoria", "QLD": "Queensland",
                  "SA": "South Australia", "WA": "Western Australia", "TAS": "Tasmania",
                  "ACT": "Australian Capital Territory", "NT": "Northern Territory"}
    st["STATE_NAME"] = st["state"].map(STATE_NAME)
    st = st.rename(columns={"state": "code"})
    st[["STATE_NAME", "code", "winners"]].to_csv(f"{SITE}/map_state_counts.csv", index=False)

    # one row per winner for the AU dot map, golden-angle sunflower jitter per city
    win = win.sort_values(["birthplace", "person"]).reset_index(drop=True)
    GA = math.radians(137.507764)
    R = 0.55
    rows = []
    for city, grp in win.groupby("birthplace"):
        k = len(grp)
        for i, (_, r) in enumerate(grp.iterrows()):
            rr = R * math.sqrt((i + 0.5) / max(k, 1))
            ang = i * GA
            dlon = rr * math.cos(ang) / max(math.cos(math.radians(r["lat"])), 0.5)
            dlat = rr * math.sin(ang)
            rows.append({"person": r["person"], "birthplace": city, "state": r["state"],
                         "lon": round(r["lon"] + dlon, 4), "lat": round(r["lat"] + dlat, 4),
                         "city_size": k})
    pd.DataFrame(rows).to_csv(f"{SITE}/map_person_dots.csv", index=False)

    # city-level table
    city = (win.groupby("birthplace")
            .agg(lat=("lat", "first"), lon=("lon", "first"), state=("state", "first"),
                 wins=("gold_wins", "sum"), people=("person", "size"))
            .reset_index())
    city.to_csv(f"{SITE}/map_city_totals.csv", index=False)
    win[["person", "birthplace", "lat", "lon", "state", "gold_wins"]] \
        .to_csv(f"{SITE}/map_birthplaces.csv", index=False)

    # overseas winners by country
    COUNTRY = {"Tennessee": ("United States", 36.282, -99.731), "Connecticut": ("United States", 41.6, -72.7),
               "New York City": ("United States", 40.7, -74.0), "Akron": ("United States", 41.08, -81.52),
               "Honolulu": ("United States", 21.3, -157.86), "Waldorf": ("United States", 38.63, -76.9),
               "Las Vegas": ("United States", 36.17, -115.14), "Long Beach": ("United States", 33.77, -118.19),
               "San Francisco": ("United States", 37.77, -122.42), "Parkersburg": ("United States", 39.27, -81.56),
               "Oakville": ("Canada", 49.8, -93.02), "Canada": ("Canada", 49.8, -93.02),
               "Wellington": ("New Zealand", -41.29, 174.78), "Auckland": ("New Zealand", -36.85, 174.76),
               "Levin": ("New Zealand", -40.62, 175.29), "Howick": ("New Zealand", -36.89, 174.91),
               "Christchurch": ("New Zealand", -43.53, 172.64),
               "London": ("United Kingdom", 52.702, -1.634), "Oxford": ("United Kingdom", 51.75, -1.26),
               "Liverpool": ("United Kingdom", 53.41, -2.98), "Kilwinning": ("United Kingdom", 55.65, -4.71),
               "Coventry": ("United Kingdom", 52.41, -1.51), "Omagh": ("United Kingdom", 54.5, -7.3),
               "Lichfield": ("United Kingdom", 52.68, -1.82), "Northampton": ("United Kingdom", 52.24, -0.89),
               "Oldham": ("United Kingdom", 53.54, -2.11), "Blackpool": ("United Kingdom", 53.82, -3.05),
               "Battersea": ("United Kingdom", 51.47, -0.16), "Bristol": ("United Kingdom", 51.45, -2.59),
               "Cardiff": ("United Kingdom", 51.48, -3.18), "Edinburgh": ("United Kingdom", 55.95, -3.19),
               "Ely": ("United Kingdom", 52.4, 0.26), "England": ("United Kingdom", 52.7, -1.6),
               "Johannesburg": ("South Africa", -26.204, 28.047),
               "Ibadan": ("Nigeria", 7.38, 3.95), "Osijek": ("Croatia", 45.56, 18.67),
               "Sri Lanka": ("Sri Lanka", 7.873, 80.771), "Tartu": ("Estonia", 58.378, 26.729),
               "Conakry": ("Guinea", 9.509, -13.712), "Vienna": ("Austria", 48.208, 16.373)}
    ov["country"] = ov["birthplace"].map(lambda c: COUNTRY.get(c, (c,))[0])
    oc = (ov.groupby("country").agg(winners=("person", "size")).reset_index())
    coords = {}
    for c in ov["birthplace"].unique():
        if c in COUNTRY and c not in coords:
            coords[COUNTRY[c][0]] = (COUNTRY[c][1], COUNTRY[c][2])
    oc["lat"] = oc["country"].map(lambda c: coords[c][0])
    oc["lon"] = oc["country"].map(lambda c: coords[c][1])
    oc = oc.sort_values("winners", ascending=False)
    oc.to_csv(f"{SITE}/map_overseas_winners.csv", index=False)

    print("clean wins:", len(wins), "| winners:", wins["person"].nunique(),
          "| AU mapped:", len(win), "| overseas winners:", int(oc['winners'].sum()))
    print("all-time networks:\n", wins["network"].value_counts().to_string())
    print("decades:\n", dec.to_string())
    print("overseas:\n", oc.to_string())
    print("city top:\n", city.sort_values("wins", ascending=False).head(8).to_string())

if __name__ == "__main__":
    main()
