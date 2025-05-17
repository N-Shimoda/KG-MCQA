import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

# Set up logging to file (at the top of the file)
logging.basicConfig(filename="wikipedia_api.log", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


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

    all_titles = []
    chunk_size = 50

    def fetch_titles(chunk: list[str]) -> list[str]:
        """
        Fetches the canonical Wikipedia page titles for a given list of titles.

        This function queries the Wikipedia API with a chunk of page titles, handling normalization and redirects.
        It returns the final resolved titles as they exist on Wikipedia.

        Parameters
        ----------
        chunk : list of str
            A list of Wikipedia page titles to query.

        Returns
        -------
        list of str
            A list of resolved Wikipedia page titles after normalization and redirect resolution.

        Examples
        --------
        >>> fetch_titles(["Albert Einstein", "Python (programming language)"])
        ['Albert Einstein', 'Python (programming language)']
        """
        url = "https://en.wikipedia.org/w/api.php"
        target_str = "|".join(chunk)
        params = {"action": "query", "prop": "info", "titles": target_str, "redirects": 1, "format": "json"}
        response = requests.get(url, params=params)
        data = response.json()

        # Log API call to file
        logging.info("Wikipedia API call executed for titles: %s", target_str)

        normalize_map = (
            {item["from"]: item["to"] for item in data["query"]["normalized"]} if "normalized" in data["query"] else {}
        )
        redirect_map = (
            {item["from"]: item["to"] for item in data["query"]["redirects"]} if "redirects" in data["query"] else {}
        )

        normalized = [normalize_map[target] if target in normalize_map else target for target in chunk]
        titles = [redirect_map[target] if target in redirect_map else target for target in normalized]
        return titles

    chunks = [targets[i : i + chunk_size] for i in range(0, len(targets), chunk_size)]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_titles, chunk) for chunk in chunks]
        for future in as_completed(futures):
            all_titles.extend(future.result())

    return all_titles


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

    all_titles = []
    all_urls = []
    chunk_size = 50

    def fetch_and_save(chunk: list[str]) -> tuple[list[str], list[str]]:
        """
        Fetch Wikipedia page data for a chunk of titles, save each page as a JSON file,
        and return the list of normalized/redirected titles and their URLs.

        Parameters
        ----------
        chunk : list[str]
            List of Wikipedia page titles (up to 50).

        Returns
        -------
        titles : list[str]
            List of normalized and redirected Wikipedia page titles.
        urls : list[str]
            List of URLs corresponding to the Wikipedia pages.
        """
        url = "https://en.wikipedia.org/w/api.php"
        target_str = "|".join(chunk)
        params = {
            "action": "query",
            "prop": "info|extracts",
            "inprop": "url",
            "exintro": 1,
            "explaintext": 1,
            "titles": target_str,
            "redirects": 1,
            "format": "json",
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Log API call to file
        logging.info("Wikipedia API call executed for titles: %s", target_str)

        normalize_map = (
            {item["from"]: item["to"] for item in data["query"]["normalized"]} if "normalized" in data["query"] else {}
        )
        redirect_map = (
            {item["from"]: item["to"] for item in data["query"]["redirects"]} if "redirects" in data["query"] else {}
        )
        normalized = [normalize_map[target] if target in normalize_map else target for target in chunk]
        titles = [redirect_map[target] if target in redirect_map else target for target in normalized]

        # Get URLs for each title
        pages = data["query"]["pages"]
        url_map = {page["title"]: page["fullurl"] if int(page_id) > 0 else None for page_id, page in pages.items()}
        urls = [url_map[title] for title in titles]

        # Save articles to JSON files
        today_date = datetime.now()
        for page_id, page in pages.items():
            if int(page_id) < 0:
                continue

            data_to_save = {
                "title": page["title"],
                "fullurl": page["fullurl"],
                "retrieved-date": today_date.strftime("%Y/%m/%d %H:%M:%S"),
                "converted": False,
                "summary": page["extract"],
            }

            subdir, basename = assign_file_path(page["title"])
            os.makedirs(f"{out_dir}/{subdir}", exist_ok=True)
            output_path = f"{out_dir}/{subdir}/{basename}"

            save_file = True
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as output_file:
                    date_str = json.load(output_file).get("retrieved-date")
                    retriedved_date = datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
                    if (today_date - retriedved_date).days < cache_ttl_days:
                        save_file = False

            if save_file:
                with open(output_path, "w", encoding="utf-8") as output_file:
                    json.dump(data_to_save, output_file, indent=4)

        return titles, urls

    chunks = [targets[i : i + chunk_size] for i in range(0, len(targets), chunk_size)]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_and_save, chunk) for chunk in chunks]
        for future in as_completed(futures):
            titles, urls = future.result()
            all_titles.extend(titles)
            all_urls.extend(urls)

    return all_titles, all_urls


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
