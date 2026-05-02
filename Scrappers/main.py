import asyncio
import json
from engine import scrape



def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":

    config = load_config('/Users/abdelrahmansayed/Real estate Project/Scrappers/Configs/bayut.json')


    asyncio.run(scrape(config, max_pages=2))

