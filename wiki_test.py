import json
import os
from datetime import datetime

import requests

from kgraph.wiki import assign_file_path


def get_wiki_titles(targets: list[str]) -> list[str]:
    # send request to Wikipedia API
    url = "https://en.wikipedia.org/w/api.php"
    target_str = "|".join(targets)
    params = {"action": "query", "prop": "info", "titles": target_str, "redirects": 1, "format": "json"}

    response = requests.get(url, params=params)
    data = response.json()

    # trace normalization and redirects
    normalize_map = {item["from"]: item["to"] for item in data["query"]["normalized"]}
    redirect_map = {item["from"]: item["to"] for item in data["query"]["redirects"]}

    normalized = [normalize_map[target] if target in normalize_map else target for target in targets]
    redirected = [redirect_map[target] if target in redirect_map else target for target in normalized]

    print("targets:", targets)
    print("normalized:", normalized)
    print("redirected:", redirected)

    return redirected


def download_wiki_pages(targets: list[str], out_dir: str) -> tuple[list[str], list[str]]:
    # send request to Wikipedia API
    url = "https://en.wikipedia.org/w/api.php"
    target_str = "|".join(targets)
    params = {
        "action": "query",
        "prop": "info|extracts",
        "inprop": "url",
        "exintro": 1,  # 冒頭部分のみ
        "explaintext": 1,  # プレーンテキストで取得
        "titles": target_str,
        "redirects": 1,
        "format": "json",
    }
    response = requests.get(url, params=params)
    data = response.json()

    with open("response.json", "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # save data
    today_date = datetime.now()
    cache_ttl_days = 1
    for page_id, page in data["query"]["pages"].items():
        if int(page_id) < 0:
            continue

        data = {
            "title": page["title"],
            "fullurl": page["fullurl"],
            "retrieved-date": today_date.strftime("%Y/%m/%d %H:%M:%S"),
            "converted": False,
            "summary": page["extract"],
        }

        # Create output directory if it doesn't exist
        subdir, basename = assign_file_path(page["title"])
        os.makedirs(f"{out_dir}/{subdir}", exist_ok=True)
        output_path = f"{out_dir}/{subdir}/{basename}"

        # Save article to JSON file
        save_file = True
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as output_file:
                date_str = json.load(output_file).get("retrieved-date")
                retriedved_date = datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
                if (today_date - retriedved_date).days < cache_ttl_days:
                    save_file = False

        if save_file:
            with open(output_path, "w", encoding="utf-8") as output_file:
                json.dump(data, output_file, indent=4)


# 例
targets = ["Inception", "Kyoto University", "Parasite", "woodwind", "Cubist Movement", "harmony"]
# get_wiki_titles(targets)
download_wiki_pages(targets, "wiki_test")
