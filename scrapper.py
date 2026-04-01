import requests
from bs4 import BeautifulSoup
import cloudscraper
import csv
import time
import random

# Csv output file
output_file = "one_piece_episodes.csv"

# Fields to extract
fields = [
    "episodio",
    "fecha_emision",
    "guion",
    "arte",
    "animacion",
    "direccion",
    "tv_rating",
    "rank"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

session = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)
session.headers.update(headers)

# scraping function to extract episode data
def scrape_episode(n, retries=3):
    url = f"https://onepiece.fandom.com/es/wiki/Episodio_{n}"

    for attempt in range(retries):
        try:
            response = session.get(url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Helper functions to extract data
                def get_data(source):
                    tag = soup.find("div", {"data-source": source})
                    if tag:
                        value = tag.find("div", class_="pi-data-value")
                        return value.get_text(strip=True) if value else None
                    return None

                def get_td_data(source):
                    tag = soup.find("td", {"data-source": source})
                    if tag:
                        return tag.get_text(strip=True)
                    return None

                data = {
                    "episodio": n,
                    "fecha_emision": get_data("Airdate"),
                    "guion": get_data("Guión"),
                    "arte": get_data("Art"),
                    "animacion": get_data("Animación"),
                    "direccion": get_data("Director"),
                    "tv_rating": get_td_data("Rating"),
                    "rank": get_td_data("Rango")
                }

                return data

            else:
                print(f"[Attempt {attempt+1}] HTTP {response.status_code} in episode {n}")

        except requests.exceptions.RequestException as e:
            print(f"[Attempt {attempt+1}] Error in episode {n}: {e}")

        time.sleep(2)

# CSV writing
with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    # It considers up to the last episode aired on 2025
    episode_range = range(1, 1155 + 1)

    for n in episode_range:
        print(f"Scrapeando episodio {n}...")

        info = scrape_episode(n)

        if info:
            writer.writerow(info)

        time.sleep(random.uniform(0.5, 2.0))

print(f"Datos guardados en {output_file}")