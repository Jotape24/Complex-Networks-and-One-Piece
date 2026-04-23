from pathlib import Path
import pandas as pd

# To execute this code, make sure you have the IMDb TSV files in a "datasets" folder.
# Download link: https://datasets.imdbws.com/


# Path to IMDb datasets
BASE_DIR = Path(__file__).resolve().parent

path_title = BASE_DIR / ".." / "datasets" / "title.basics.tsv"
path_episode = BASE_DIR / ".." / "datasets" / "title.episode.tsv"
path_ratings = BASE_DIR / ".." / "datasets" / "title.ratings.tsv"

# Read datasets
title = pd.read_csv(path_title, sep="\t", dtype=str, na_values="\\N")
episode = pd.read_csv(path_episode, sep="\t", dtype=str, na_values="\\N")
ratings = pd.read_csv(path_ratings, sep="\t", dtype=str, na_values="\\N")

# Selection of One Piece TV series
one_piece = title[
    (title["primaryTitle"].str.lower() == "one piece") &
    (title["titleType"] == "tvSeries")
]

if one_piece.empty:
    raise ValueError("No se encontró One Piece")

parent_tconst = one_piece.iloc[0]["tconst"]

# Filter episodes of One Piece
episodes_op = episode[episode["parentTconst"] == parent_tconst].copy()

episodes_op["episodeNumber"] = pd.to_numeric(episodes_op["episodeNumber"], errors="coerce")

# Merge with ratings
episodes_op = episodes_op.merge(ratings, on="tconst", how="left")

episodes_op["averageRating"] = pd.to_numeric(episodes_op["averageRating"], errors="coerce")
episodes_op["numVotes"] = pd.to_numeric(episodes_op["numVotes"], errors="coerce")

# Sort and clean data
table = episodes_op.sort_values("episodeNumber")
table = table.dropna(subset=["episodeNumber"])
table = table[table["episodeNumber"] <= 1155]

table = table[["episodeNumber", "averageRating", "numVotes"]]

table = table.rename(columns={
    "episodeNumber": "episode",
    "averageRating": "rating",
    "numVotes": "votes"
})

output_path = BASE_DIR / ".." / "datasets" / "one_piece_imdb.csv"
table.to_csv(output_path, index=False, encoding="utf-8")

print(f"CSV guardado en: {output_path}")