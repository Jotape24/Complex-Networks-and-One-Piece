import requests
from bs4 import BeautifulSoup
import cloudscraper
import csv
import time
import random

# Csv output file
output_file = "one_piece_episodes_my_anime_list.csv"

# Fields to extract
fields = [
    "episodio",
    "puntuacion",
    "votos"
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
def scrape_links(n, retries=3):
    url = f"https://myanimelist.net/anime/21/One_Piece/episode?offset={n*100}"

    for attempt in range(retries):
        try:
            response = session.get(url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                tags = soup.find_all("div", class_= "voted fs12 mb2")
                urls_episodes = {}
                for tag in tags:
                    value = tag.find("a", class_="js-episode-vote-button ga-click")
                    if value:
                        urls_episodes[value.get("data-episode-num", 0)] = value.get("data-topic-id", None)

                return urls_episodes
            else:
                print(f"[Attempt {attempt+1}] HTTP {response.status_code} in episode range {n*100 + 1}, {(n+1)*100}")

        except requests.exceptions.RequestException as e:
            print(f"[Attempt {attempt+1}] Error in episode range {n*100 + 1}, {(n+1)*100}: {e}")

        time.sleep(2)

def scrape_episodes(topic_id, episode, retries=3):
    url = f'https://myanimelist.net/forum/?topicid={topic_id}&pollresults=1'

    for attempt in range(retries):
        try:
            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                tag = soup.find("div", class_= "topic-poll-option total")

                data = {"episodio": 0, "puntuacion": 0, "votos": 0}
                if tag:
                    value = tag.find("div", class_="ratio").get_text(strip=True)
                    votes = tag.find("div", class_="number").get_text(strip=True)
                    if value and votes:
                        data["episodio"] = episode
                        data["puntuacion"] = float(value.removeprefix("Average ")) * 2
                        data["votos"] = int(votes.removesuffix(" votes").replace(",", ""))
                return data
                
            else:
                print(f"[Attempt {attempt+1}] HTTP {response.status_code} in episode {episode}")

        except requests.exceptions.RequestException as e:
            print(f"[Attempt {attempt+1}] Error in episode {episode}: {e}")

        time.sleep(5)

# CSV writing
with open(output_file, "a", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    # It considers up to the last episode aired on 2025
    episode_range = range(12)
    urls = {}
    for n in episode_range:
        print(f"Scrapeando links de episodios del {100*n + 1} al {100*(n+1)}...")

        urls.update(scrape_links(n))

        time.sleep(random.uniform(0.5, 2.0))
    
    for k in urls:
        data = scrape_episodes(urls[k], k)
        if data:
            writer.writerow(data)

print(f"Datos guardados en {output_file}")