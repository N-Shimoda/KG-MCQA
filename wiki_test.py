import json

import requests


def get_wikipedia_page_url(title: str, lang: str = "en") -> str:
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {"action": "query", "format": "json", "titles": title, "prop": "info", "inprop": "url", "redirects": 1}

    response = requests.get(url, params=params)
    data = response.json()

    with open("response.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    pages = data["query"]["pages"]
    page = next(iter(pages.values()))

    if "fullurl" in page:
        return page["fullurl"]
    else:
        return f"記事『{title}』は見つかりませんでした。"


# 例
print(get_wikipedia_page_url("Kyoto University|Parasite|woodwind|Cubist Movement"))
