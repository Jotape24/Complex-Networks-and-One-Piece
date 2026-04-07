import re
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
    "rank",
    "n de paginas"
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
    url = f"https://onepiece.fandom.com/wiki/Episode_{n}"

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
                        if value: 
                            # Extract raw HTML inside the div
                            raw_html = str(value)
                            # Split by <br> tags
                            parts = raw_html.split("<br/>")

                            results = []
                            for part in parts:
                                text = BeautifulSoup(part, "html.parser").get_text(strip=True)
                                if "-" in text:
                                    _, en = text.split("-", 1)
                                    results.append(en.strip())

                                else:
                                    results.append(text.strip())
                            return results
                    return None

                def get_td_data(source):
                    tag = soup.find("td", {"data-source": source})
                    if tag:
                        text = tag.get_text(strip=False)
                        return text.split("-")[0]
                    return None
                
                def get_manga_pages():
                    count = 0
                    tag = soup.find("div", {"data-source": "chapter"})
                    if tag:
                        value = tag.find("div", class_="pi-data-value")
                        if value: 
                            # Extract raw HTML inside the div
                            raw_html = str(value)
                            # Split by <br> tags
                            parts = raw_html.split("<br/>")
                            for part in parts:
                                if "p." in part:
                                    part = part.split("p.")[1]
                                    text = BeautifulSoup(part, "html.parser").get_text(strip=True)
                                    pages = re.findall(r'-?\d*\.?\d+', text)
                                    pages = [float(x) for x in pages]
                                    if len(pages) > 1:
                                        count += abs(pages[1])-pages[0]
                                    else:
                                        count += 1
                    return count
                

                data = {
                    "episodio": n,
                    "fecha_emision": get_data("Airdate"),
                    "guion": get_data("Screen"),
                    "arte": get_data("Art"),
                    "animacion": get_data("Ad"),
                    "direccion": get_data("Ed"),
                    "tv_rating": get_td_data("rating"),
                    "rank": get_td_data("rank"),
                    "n de paginas": get_manga_pages()
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