import json

import requests


def get_wikipedia_page_summary(title: str, lang: str = "en") -> dict:
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "info|extracts",
        "inprop": "url",
        "exintro": 1,  # 冒頭部分のみ
        "explaintext": 1,  # プレーンテキストで取得
        "titles": title,
        "redirects": 1,
        "format": "json",
    }

    response = requests.get(url, params=params)
    data = response.json()

    with open("response.json", "w") as f:
        json.dump(data, f, indent=4)

    pages = data["query"]["pages"]
    summaries = {}
    for key, page in pages.items():
        if int(key) > 0:
            summaries[page["title"]] = page.get("extract", "")
        else:
            summaries[page["title"]] = None
    return summaries


# 例
targets = ["Inception", "Kyoto University", "Parasite", "woodwind", "Cubist Movement", "harmony"]
print(get_wikipedia_page_summary("|".join(targets)))
