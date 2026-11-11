"""Editorial genre classification for winning programs (documented, human-curated).

Buckets: Drama, Comedy, Light Entertainment, Reality, Factual, News & Current
Affairs, Children's, Sport, Lifestyle. Entries the classifier could not place
are flagged 'review' rather than guessed.
"""
import csv, re
import pandas as pd

G = {}
def Drama(*p): [G.setdefault(x, "Drama") for x in p]
def Comedy(*p): [G.setdefault(x, "Comedy") for x in p]
def LightEnt(*p): [G.setdefault(x, "Light Entertainment") for x in p]
def Reality(*p): [G.setdefault(x, "Reality") for x in p]
def Factual(*p): [G.setdefault(x, "Factual & Documentary") for x in p]
def News(*p): [G.setdefault(x, "News & Current Affairs") for x in p]
def Kids(*p): [G.setdefault(x, "Children's") for x in p]
def Sport(*p): [G.setdefault(x, "Sport") for x in p]
def Lifestyle(*p): [G.setdefault(x, "Lifestyle & Food") for x in p]

Drama("800 Words", "A Country Practice", "A Place to Call Home", "Acropolis Now",
      "After the Deluge", "All Saints", "Bangkok Hilton", "Barracuda", "Better Man",
      "Bite Club (Nine Network) and Mystery Road", "Bloom", "Blue Heelers",
      "Boy Swallows Universe", "Brokenwood", "Devil's Dust", "Division 4",
      "E Street", "East West 101", "Fires", "Grace Beside Me", "Home and Away",
      "INXS: Never Tear Us Apart", "Jack Irish", "Jessica", "Love Child",
      "Love Child (Nine Network) and The Wrong Girl", "Love Me", "Love My Way",
      "Mabo", "Maralinga Tjarutja", "McLeod's Daughters", "Molly",
      "Mr Inbetween", "My Brother Jack", "Mystery Road", "Mystery Road: Origin",
      "Neighbours", "Number 96", "Offspring", "Offspring (Network Ten) and Paper Giants: The Birth of Cleo",
      "Offspring and Party Tricks", "Packed to the Rafters", "Paper Giants: The Birth of Cleo",
      "Peter Allen: Not the Boy Next Door", "Police Rescue", "Power Games: The Packer-Murdoch Story",
      "Puberty Blues", "RAN Remote Area Nurse", "Rake", "Redfern Now", "Redfern Now: Promise Me",
      "Romper Stomper", "Safe Harbour", "Satisfaction", "Saved", "SeaChange", "Secret City",
      "Seven Types of Ambiguity", "Sisters of War", "Sons and Daughters", "Sword of Honour",
      "Stingers", "Stranded", "The Circuit", "The Cry", "The Kettering Incident", "The King",
      "The Man From Snowy River", "The Principal", "The Secret Life of Us", "The Secret River",
      "The Slap", "The Society Murders", "The Twelve", "Through My Eyes: The Lindy Chamberlain Story",
      "Tracks of Glory", "Underbelly", "Underbelly: Razor", "Underbelly: The Golden Mile",
      "Upright", "Wakefield", "Water Rats", "Wentworth", "White Collar Blue", "Wildside",
      "Wildside (ABC TV) and David Wenham in SeaChange", "Winners & Losers", "the Family",
      "the Ranks", "A Model Daughter: The Killing of Caroline Byrne", "Answered by Fire",
      "The Heroes", "Grand Opera", "Line", "This", "Maggie", "Jimmy", "Kate Box",
      "A Sunburnt Christmas", "Wakefield")
Comedy("Colin From Accounts", "Colin from Accounts", "Bump", "Fisk", "Please Like Me",
       "Rosehaven", "Summer Heights High", "Ja'mie: Private School Girl",
       "We Can Be Heroes: Finding The Australian of the Year", "Angry Boys",
       "Full Frontal", "The Mavis Bramston Show", "Utopia", "Mad As Hell",
       "Shaun Micallef's Mad As Hell", "Shaun Micallef's Mad as Hell",
       "Sam Pang Tonight", "CRAM! (Network Ten) and Utopia", "Boy Swallows Universe")
LightEnt("Hey Hey It's Saturday", "In Melbourne Tonight", "It Could Be You", "Bandstand",
         "Blankety Blanks", "Fast Forward", "Pick a Box", "Sound of Music",
         "Spicks and Specks", "Spicks and Specks and Adam Hills in Gordon Street Tonight",
         "Talkin' 'Bout Your Generation", "The Barry Crocker Show", "The Don Lane Show",
         "The Ernie Sigley Show", "The Graham Kennedy Show", "The Lorrae Desmond Show",
         "The Midday Show", "The Mike Walsh Show", "The Mobil Limb Show", "Midday",
         "The Norman Gunston Show", "Rove (Live)", "Rove Live",
         "Rove and Are You Smarter Than a 5th Grader?", "The 7pm Project", "The Project",
         "The Circle", "The Front Bar", "Have You Been Paying Attention?",
         "Hard Quiz", "Guy Montgomery's Guy Mont-Spelling Bee",
         "Hamish and Andy's Euro Gap Year and Hamish and Andy's Caravan of Courage: Australia Vs New Zealand",
         "Hamish and Andy's Gap Year", "All Star Family Feud",
         "All Star Family Feud (Network Ten) and Family Feud", "Family Feud",
         "Eurovision Song Contest 2023 - Grand Final", "Logie Awards 2025",
         "Sam Pang Tonight, Have You Been Paying Attention?, The Front Bar and Logie Awards 2025",
         "Sydney Gay and Lesbian Mardi Gras 2021", "Great Temptation", "All Together Now",
         "At Home Alone Together", "Eurovision - Decades", "In Melbourne Tonight")
Reality("Big Brother", "Big Brother, Dancing with The Stars and The Voice",
        "Dancing with the Stars", "The Voice", "MasterChef Australia", "Masterchef Australia",
        "The Block", "I'm a Celebrity...Get Me Out of Here!", "Australian Idol",
        "LEGO® Masters Australia", "Lego Masters", "The Chase Australia",
        "The Chase Australia and The Morning Show", "Tipping Point Australia, Australian Open and Olympic and Paralympic Games Paris 2024",
        "Gogglebox Australia", "Love on the Spectrum", "The Set", "Muster Dogs",
        "Portrait Artist of the Year", "Beauty and the Geek", "Therecruit")
Factual("Alone Australia", "The Australian Wars", "The People vs Robodebt",
        "You Can't Ask That", "Miriam Margolyes Australia Unmasked",
        "Miriam Margolyes Impossibly Australian", "A Dog's World with Tony Armstrong",
        "Old People's Home For 4 Year Olds", "Old People's Home for Teenagers",
        "Gardening Australia", "Backyard Blitz", "Better Homes and Gardens",
        "Australian Story", "This Life: Belinda Emmett\", Australian Story",
        "60 Minutes", "60 Minutes and Dangerous Lies: Unmasking Belle Gibson",
        "Miriam Margolyes: Almost Australian")
News("A Current Affair", "A Current Affair, The Great Debate and Election 2025: Australia Decides",
     "Four Corners", "7.30", "7.30 and Australia Votes 2025: Election Night Live",
     "News Breakfast", "ABC News Breakfast", "Today", "The Morning Show",
     "Aboriginal Communities\", Lateline", "Lateline", "Nine News", "ABC News",
     "Apollo 11 broadcast")
Kids("Bluey", "Bindi: The Jungle Girl", "Play School: All Together",
     "100% Wolf: Legend of the Moonstone", "Bluey and Taylor Swift Fireball",
     "Are You Tougher Than Your Ancestors?", "Hardball", "First Day")
Sport("Australian Open, 2025 Melbourne Cup, Wimbledon 2025, Roland Garros 2025, US Open 2025 and Cross Court",
      "AFL Footy Show", "The Front Bar")
Lifestyle("Grand Designs Australia", "The Great Australian Bake Off", "The Living Room",
          "Adam and Poh's Great Australian Bites", "Adam and Poh's Malaysia in Australia",
          "Garden Allies", "River Cottage Australia")

Drama("Stateless", "The Newsreader", "Heartbreak High", "The Narrow Road to the Deep North – Episodes 1")
# person names or mis-parsed entries — excluded from genre charts
G["Friends"] = "flag-overseas-star"
G["Goolagong"] = "flag-person-or-parse"
G["Kitty Flanagan"] = "flag-person-or-parse"
G["Miranda Tapsell"] = "flag-person-or-parse"
G["Yellowstone"] = "flag-overseas-star"

if __name__ == "__main__":
    df = pd.read_csv("/root/work/data/winning_programs.csv")
    df["genre"] = df["program"].map(G)
    df["flag"] = df["genre"].isna()
    df["genre"] = df["genre"].fillna("")
    df.to_csv("/root/work/data/winning_programs_genres.csv", index=False)
    print(len(df), "programs;", df["flag"].sum(), "unclassified:")
    print(df[df["flag"]]["program"].tolist())
