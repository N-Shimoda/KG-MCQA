import json
import os
from datetime import datetime

import requests


def assign_file_path(title: str) -> tuple[str, str]:
    """
    Assign a sub-directory path based on the first character of the title.
    Non-alphabetic characters are grouped under '_others'.

    Parameters
    ----------
    title : str
        The title of the Wikipedia page.

    Returns
    -------
    subdir : str
        Sub-directory name based on the first character of the title.
    basename : str
        File name for the JSON file, replacing spaces with underscores.

    Example
    -------
    >>> assign_file_path("Machine Learning")
    ('m', 'Machine_Learning.json')
    """
    first_char = title[0].lower()
    subdir = first_char if first_char.isalpha() else "_others"
    basename = title.replace(" ", "_") + ".json"
    return subdir, basename


def get_wiki_titles(targets: list[str]) -> list[str]:
    """
    Get Wikipedia page titles for the given targets.
    The output titles are normalized and redirected if happens.

    Parameters
    ----------
    targets : list[str]
        List of Wikipedia page titles.

    Returns
    -------
    titles : list[str]
        List of Wikipedia page titles.
    """
    if len(targets) == 0:
        return []

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

    # print("targets:", targets)
    # print("normalized:", normalized)
    # print("redirected:", redirected)

    return redirected


def download_wiki_pages(targets: list[str], out_dir: str, cache_ttl_days: int = 1) -> tuple[list[str], list[str]]:
    """
    Download Wikipedia pages and save them as JSON files.

    Parameters
    ----------
    targets : list[str]
        List of Wikipedia page titles to download.
    out_dir : str
        Output directory to save the JSON files.
    cache_ttl_days : int
        Number of days to keep the cache. Default is 1 day.

    Returns
    -------
    titles : list[str]
        List of Wikipedia page titles.
    urls : list[str]
        List of URLs for the downloaded pages.
    """
    if len(targets) == 0:
        return [], []

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
    response.raise_for_status()
    data = response.json()

    # for dev
    # with open("response.json", "w") as f:
    #     json.dump(data, f, indent=4, ensure_ascii=False)

    # get titles
    normalize_map = (
        {item["from"]: item["to"] for item in data["query"]["normalized"]} if "normalized" in data["query"] else {}
    )
    redirect_map = (
        {item["from"]: item["to"] for item in data["query"]["redirects"]} if "redirects" in data["query"] else {}
    )
    normalized = [normalize_map[target] if target in normalize_map else target for target in targets]
    titles = [redirect_map[target] if target in redirect_map else target for target in normalized]

    # get URLs
    pages = data["query"]["pages"]
    url_map = {page["title"]: page["fullurl"] if int(page_id) > 0 else None for page_id, page in pages.items()}
    urls = [url_map[title] for title in titles]

    # Save articles to JSON files
    today_date = datetime.now()
    for page_id, page in pages.items():
        # skip if page not found
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

    return titles, urls


if __name__ == "__main__":
    # Example usage
    targets = [
        "Kyoto University",
        "Machine Learning",
        "AI",
        "éclair",
        "classical music",
        "123 Start",
        "Naoki Shimoda",
    ]
    # targets = []
    titles, urls = download_wiki_pages(targets, out_dir="wikipedia/test")
    print("Wiki titles: ", titles)
    print("URLs: ", urls)
