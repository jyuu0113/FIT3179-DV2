"""Build every derived dataset for the DV2 page into site/data/.

Editorial derivations (star types, states, genders, genre buckets) are documented
in the page's chart-notes and metadata. All scraped inputs come from data/*.csv.
"""
import json, re, sys
import pandas as pd

sys.path.insert(0, "/root/work")
from star_type_lookup import LOOKUP

DATA = "/root/work/data"
SITE = "/root/work/site/data"

LABEL = {"variety": "Variety & talk show hosts", "comedy": "Comedy performers",
         "drama": "Drama & soap actors", "news": "News & current affairs",
         "lightent": "Light entertainment & reality hosts", "special": "Special broadcast"}

def main():
    # ---------- 1. gold_logie wins typed ----------
    n = pd.read_csv(f"{DATA}/gold_logie_nominees.csv")
    wins = n[n["is_winner"]].copy()
    wins["star_type_label"] = wins["person"].map(LOOKUP).map(LABEL)
    wins["decade"] = ((wins["year"] // 10) * 10).astype(str) + "s"
    wins[["year", "decade", "person", "star_type_label", "program", "network"]] \
        .to_csv(f"{SITE}/gold_logie_wins_typed.csv", index=False)

    # ---------- 2. repeat winners (career span) ----------
    rep = (wins.groupby("person")
           .agg(first_win=("year", "min"), last_win=("year", "max"),
                total_wins=("year", "count"),
                networks=("network", lambda s: ", ".join(sorted(set(s.astype(str))))),
                programs=("program", lambda s: ", ".join(sorted(set(s.astype(str))))))
           .reset_index())
    rep = rep[rep["total_wins"] > 1].sort_values("total_wins", ascending=False)
    rep["star_type_label"] = rep["person"].map(LOOKUP).map(LABEL)
    rep.to_csv(f"{SITE}/gold_logie_repeat_winners.csv", index=False)

    # ---------- 3. gender per winner ----------
    bio = json.load(open(f"{DATA}/people_bio_cache.json"))
    ALT = {"Ally Langdon": "Allison Langdon", "Bec Cartwright": "Rebecca Cartwright",
           "Norman Gunston": "Garry McDonald", "Bob and Dolly Dyer": "Dolly Dyer"}
    g = {"male": "Male", "female": "Female"}
    wins["gender"] = wins["person"].map(
        lambda p: g.get(bio.get(ALT.get(p, p), {}).get("gender", ""), "Unknown"))
    wins.to_csv(f"{SITE}/gold_logie_wins_gender.csv", index=False)

    # ---------- 4. winner network per year (bump chart) ----------
    yearly = (wins.groupby(["year", "network"]).size().reset_index(name="wins"))
    yearly["rank"] = yearly.groupby("year")["wins"].rank("dense", ascending=False).astype(int)
    yearly.to_csv(f"{SITE}/gold_logie_network_year.csv", index=False)

    # ---------- 5. birthplaces with state ----------
    b = pd.read_csv(f"{DATA}/people_birthplaces.csv")
    CITY_STATE = {
        "Melbourne": "VIC", "Footscray": "VIC", "Geelong": "VIC", "Bendigo": "VIC",
        "Geelong West": "VIC", "City of Stonnington": "VIC", "Bairnsdale": "VIC",
        "Sydney": "NSW", "Newcastle": "NSW", "Wollongong": "NSW", "Long Jetty": "NSW",
        "Manly": "NSW", "Surry Hills": "NSW", "Earlwood": "NSW", "Darlinghurst": "NSW",
        "Grafton": "NSW", "Coffs Harbour": "NSW", "Mittagong": "NSW", "Dubbo": "NSW",
        "Albury": "NSW", "Richmond": "NSW", "Bondi": "NSW", "Wagga Wagga": "NSW",
        "Cronulla": "NSW", "Boorowa": "NSW", "Gosford": "NSW", "Parramatta": "NSW",
        "Paddington": "NSW", "Goulburn": "NSW", "Gunnedah": "NSW",
        "Brisbane": "QLD", "Gold Coast": "QLD", "Mount Isa": "QLD", "Townsville": "QLD",
        "Mackay": "QLD", "Redcliffe": "QLD", "Queensland": "QLD", "Roma": "QLD",
        "Cairns": "QLD", "Toowoomba": "QLD", "Buderim": "QLD",
        "Adelaide": "SA", "Parkside": "SA", "Perth": "WA", "Fremantle": "WA",
        "Bunbury": "WA", "Broome": "WA", "Albany": "WA",
        "Canberra": "ACT", "Darwin": "NT", "Hobart": "TAS", "Tasmania": "TAS",
        "Launceston": "TAS"}
    OVERSEAS = {"Johannesburg", "Ibadan", "Osijek", "Tennessee", "Connecticut",
                "New York City", "Akron", "Honolulu", "Oakville", "Wellington",
                "Auckland", "Levin", "London", "Oxford", "Liverpool", "Kilwinning",
                "Coventry", "Omagh", "Lichfield", "Northampton", "Oldham",
                "Blackpool", "Battersea", "Christchurch", "Bristol", "Cardiff",
                "Howick", "Edinburgh", "Ely", "England", "Sri Lanka", "Tartu",
                "Waldorf", "Las Vegas", "Long Beach", "Conakry", "Vienna",
                "San Francisco", "Canada", "Parkersburg", "New South Wales"}
    def state_of(bp):
        if pd.isna(bp):
            return "Unknown"
        if bp in OVERSEAS:
            return "Overseas"
        return CITY_STATE.get(bp, "Unknown")
    b["state"] = b["birthplace"].map(state_of)
    b["flag"] = b.apply(lambda r: r["flag"] or ("Unknown" if r["state"] == "Unknown" else ""), axis=1)
    b.to_csv(f"{DATA}/people_birthplaces.csv", index=False)
    b.to_csv(f"{SITE}/people_birthplaces.csv", index=False)

    # ---------- 6. AACTA TV winners: broadcaster extraction ----------
    a = pd.read_csv(f"{DATA}/aacta_tv.csv")
    def broadcaster(detail):
        if not isinstance(detail, str) or "/" not in detail:
            return ""
        tail = detail.split("/")[-1].strip()
        tail = re.split(r"\||,\s", tail)[0].strip()
        return tail if 0 < len(tail) <= 40 else ""
    a["broadcaster"] = a["detail"].map(broadcaster)
    NETMAP = {"ABC": "ABC", "ABC TV": "ABC", "ABC1": "ABC", "ABC2": "ABC", "ABC TV Plus": "ABC",
              "SBS": "SBS", "Network Ten": "Ten", "10": "Ten", "10 Bold": "Ten",
              "Nine Network": "Nine", "Nine": "Nine", "Seven Network": "Seven",
              "Seven": "Seven", "7mate": "Seven", "7two": "Seven",
              "Netflix": "Netflix", "Stan": "Stan", "Binge": "Binge", "BINGE": "Binge",
              "Foxtel": "Foxtel", "Amazon Prime Video": "Prime Video", "Prime Video": "Prime Video",
              "Paramount+": "Paramount+", "Disney+": "Disney+", "Apple TV+": "Apple TV+"}
    a["broadcaster_norm"] = a["broadcaster"].map(
        lambda s: next((v for k, v in NETMAP.items() if s and k.lower() == s.lower()), s or "Other"))
    a.to_csv(f"{SITE}/aacta_tv_enriched.csv", index=False)

    # ---------- 7. genre join for winners of both systems ----------
    genres = pd.read_csv(f"{DATA}/winning_programs_genres.csv")
    gmap = dict(zip(genres["program"].str.lower(), genres["genre"]))
    def norm_program(p):
        if not isinstance(p, str):
            return ""
        p = re.sub(r"\s*\(([^()]*(?:Network|TV|9|7|10|Nine|Seven|Ten|ABC|SBS)[^()]*)\)\s*$", "", p)
        p = re.sub(r"\s+[–-]\s*Episode\s*\d+.*$", "", p, flags=re.I)
        p = re.sub(r"\s+(Series|Season)\s+\d+.*$", "", p, flags=re.I).strip()
        return p.strip().strip('"').lower()
    def genre_of(p):
        return gmap.get(norm_program(p), "")
    # AACTA program winners by genre
    ap = a[(a["is_winner"]) & a["person"].isna() | (a["person"] == "")].copy()
    ap = a[(a["is_winner"]) & (a["person"].isna() | (a["person"].astype(str) == ""))].copy()
    ap["genre"] = ap["program"].map(genre_of)
    ap[ap["genre"] != ""].to_csv(f"{SITE}/aacta_winners_genres.csv", index=False)
    # Logie program-category winners by genre
    lw = pd.read_csv(f"{DATA}/logies_winners.csv")
    lprog = lw[(lw["is_winner"]) & (lw["item_type"] == "program")].copy()
    lprog["genre"] = lprog["winner_item"].map(genre_of)
    lprog[lprog["genre"] != ""].to_csv(f"{SITE}/logie_winners_genres.csv", index=False)

    # ---------- 8. both-systems canon ----------
    lg = lprog[lprog["genre"] != ""][["year", "category", "winner_item", "genre"]].copy()
    lg["program_norm"] = lg["winner_item"].map(norm_program)
    ag = ap[ap["genre"] != ""][["year", "category", "program", "genre"]].copy()
    ag["program_norm"] = ag["program"].map(norm_program)
    lg_keys = set(lg["program_norm"])
    canon = ag[ag["program_norm"].isin(lg_keys)].copy()
    # one row per program: earliest AACTA win + genre + whether also a Logie winner
    canon_grouped = (canon.groupby("program_norm")
                     .agg(aacta_first_win=("year", "min"), aacta_wins=("year", "count"),
                          genre=("genre", "first"))
                     .reset_index())
    lg_only = (lg[lg["year"] >= 2012].groupby("program_norm")
               .agg(logie_first_win=("year", "min"), logie_wins=("year", "count"))
               .reset_index())
    canon_grouped = canon_grouped.merge(lg_only, on="program_norm", how="left")
    canon_grouped.to_csv(f"{SITE}/both_systems_programs.csv", index=False)

    print("gold typed:", len(wins), "| repeat:", len(rep), "| aacta enriched:", len(a),
          "| aacta genres:", len(pd.read_csv(f'{SITE}/aacta_winners_genres.csv')),
          "| logie genres:", len(pd.read_csv(f'{SITE}/logie_winners_genres.csv')),
          "| canon:", len(canon))

if __name__ == "__main__":
    main()
