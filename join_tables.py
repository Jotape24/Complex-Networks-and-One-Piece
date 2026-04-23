import pandas as pd

# File paths
file_episodes = "datasets/one_piece_episodes.csv"
file_imdb = "datasets/one_piece_imdb.csv"
file_mal = "datasets/one_piece_episodes_my_anime_list.csv"

# Load CSVs
df_episodes = pd.read_csv(file_episodes)
df_imdb = pd.read_csv(file_imdb)
df_mal = pd.read_csv(file_mal)

# Rename IMDb columns 
df_imdb = df_imdb.rename(
    columns={col: f"{col}_imdb" for col in df_imdb.columns if col != "episode"}
)

# Rename MAL columns 
df_mal = df_mal.rename(
    columns={col: f"{col}_MAL" for col in df_mal.columns if col != "episodio"}
)

# episodes + IMDb
df_merged = pd.merge(
    df_episodes,
    df_imdb,
    left_on="episodio",
    right_on="episode",
    how="inner"
)

# Drop duplicate join column from IMDb
df_merged = df_merged.drop(columns=["episode"])

# add MAL data
df_merged = pd.merge(
    df_merged,
    df_mal,
    on="episodio",
    how="inner"
)

df_merged["votos"] = df_merged["votes_imdb"] + df_merged["votos_MAL"]
df_merged["rating"] = (df_merged["rating_imdb"]*df_merged["votes_imdb"] + df_merged["puntuacion_MAL"]*df_merged["votos_MAL"])/df_merged["votos"]
df_merged["rating"] = df_merged["rating"].round(2)
df_merged = df_merged.drop(columns=["rating_imdb", "votes_imdb", "puntuacion_MAL", "votos_MAL"])

# Save result
df_merged.to_csv("datasets/one_piece_merged.csv", index=False)

print("Merge completed! Saved as one_piece_merged.csv")