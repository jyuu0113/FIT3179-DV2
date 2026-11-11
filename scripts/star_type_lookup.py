# Editorial star-type classification of every Gold Logie winner, 1959-2026.
# Source of truth: gold_logie_nominees.csv winner rows (Wikipedia, TV Week Logie Awards).
# Types are the author's editorial labels based on the winner's own biography and
# winning program (see chart-note on the page). Types: variety, comedy, drama,
# news, lightent (light entertainment & reality hosts), special (one-off broadcast).
LOOKUP = {
    "Graham Kennedy": "variety", "Bob Dyer": "variety", "Lorrae Desmond": "variety",
    "Tommy Hanlon Jr.": "variety", "Bobby Limb": "variety", "Jimmy Hannan": "variety",
    "Gordon Chater": "comedy", "Hazel Phillips": "variety", "Brian Henderson": "variety",
    "Barry Crocker": "variety", "Maggie Tabberer": "variety", "Gerard Kennedy": "drama",
    "Bob and Dolly Dyer": "variety", "Tony Barber": "variety", "Pat McDonald": "drama",
    "Ernie Sigley": "variety", "Denise Drysdale": "variety", "Norman Gunston": "comedy",
    "Don Lane": "variety", "Jeanne Little": "variety", "Bert Newton": "variety",
    "Mike Walsh": "variety", "Daryl Somers": "variety", "Rowena Wallace": "drama",
    "Ray Martin": "news", "Kylie Minogue": "drama", "Craig McLachlan": "drama",
    "Steve Vizard": "comedy", "Jana Wendt": "news", "Lisa McCune": "drama",
    "Georgie Parker": "drama", "Rove McManus": "comedy", "John Wood": "drama",
    "Kate Ritchie": "drama", "Rebecca Gibney": "drama", "Ray Meagher": "drama",
    "Karl Stefanovic": "news", "Hamish Blake": "comedy", "Asher Keddie": "drama",
    "Scott Cam": "lightent", "Carrie Bickmore": "news", "Waleed Aly": "news",
    "Samuel Johnson": "drama", "Grant Denyer": "lightent", "Tom Gleeson": "comedy",
    "Sonia Kruger": "lightent", "Larry Emdur": "lightent", "Lynne McGranger": "drama",
    "Sam Pang": "comedy", "Michael Charlton": "news",
    "Neil Armstrong and Buzz Aldrin": "special",
}
