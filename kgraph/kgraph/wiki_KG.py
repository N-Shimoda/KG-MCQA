import json
import os
from datetime import datetime
from typing import Literal

import wikipediaapi

from kgraph import KB, from_text_to_kb
from kgraph.utils import colorize


def wiki_summary_to_kb(
    page_title: str,
    use_cache=True,
    save_cache=True,
    cache_directory="/github/mcq-generator/KG_cache",
    verbose=False,
) -> tuple[KB, str, str]:
    """
    Construct a KG from Wikipedia page of given title.

    Parameters
    ----------
    page_title: str
        Title of Wikipedia page.
    save_cache: bool
        If `True`, this function generates KG cache in specified directory.
    cache_directory: str
        Path of KG cache directory.
    verbose: bool

    Returns
    -------
    kb: KB
        Knowledge graph constructed from given Wikipedia page.
    page_text: str
        English text of summary part in Wikipedia.
    page_url: str
        URL of Wikipedia page.
    """
    # Check if cache page exist
    cache_directory = os.environ["HOME"] + cache_directory
    if use_cache:
        KG, page_url = check_KG_cache(page_title, cache_directory)
    else:
        KG = None

    # Case where KG cache was available
    if KG:
        if verbose:
            print(colorize("Loaded KG cache for '{}' ({})".format(page_title, page_url), 36))
        page_text = None

    # Case where KG cache was not found
    else:
        # Get page text from Wikipedia
        page_text, page_url = get_wikipedia_page_text(page_title)

        if page_text is not None:
            # Print page title and summary
            if verbose:
                print(colorize("Keyword:\n", 36) + page_title + " ({})".format(page_url))
                print(colorize("Page summary:\n", 36) + page_text)

            # Create KG from text
            KG = from_text_to_kb(page_text, verbose=verbose)

            # Save KG cache if specified
            if save_cache:
                save_KG_cache(
                    page_title, page_url, page_text, KG.relations, cache_directory=cache_directory
                )
        else:
            print(colorize("Page does not exist for '{}'".format(page_title), 31))
            KG = KB()

    return KG, page_text, page_url


def save_KG_cache(
    title: str,
    url: str,
    page_text: str,
    relations: list[dict[Literal["head", "type", "tail", "meta"], str]],
    cache_directory: str,
):
    """
    Create KG cache as json files in specified directory.

    Parameters
    ----------
    title: str
        Title of Wikipedia page
    url: str
        URL of Wikipedia page
    relations: list[dict[Literal["head", "type", "tail"], str]]
        KG relations to save.
    cache_directory: str
        Specify cache directory.
    """
    today_date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    # remove metadata from relations
    relations = [{k: v for k, v in r.items() if k != "meta"} for r in relations]

    data = {
        "title": title,
        "url": url,
        "date": today_date,
        "input_text": page_text,
        "relations": relations,
    }
    output_path = f"{cache_directory}/{title}.json"
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(data, output_file, indent=4)


def check_KG_cache(title: str, cache_directory: str) -> tuple[KB, str] | tuple[None, None]:
    """
    Check cache directory for KG with given title.

    Returns
    -------
    kb: KB
        KB constructed from KG cache.
    url: str
        URL of Wikipedia page which was used to create KG cache.
    """
    file_path = os.path.join(cache_directory, f"{title}.json")

    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                relations = data["relations"]
                url = data["url"]
                return KB(relations), url
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {title}.json: {e}")
                return (None, None)
    else:
        return None, None


def get_wikipedia_page_text(title, language="en") -> tuple[str, str]:
    """
    Retrieves the summary of a Wikipedia page with the specified title and returns the text and page URL.
    If the page does not exist, returns a tuple of `None`.

    Parameters
    ----------
    title: str
        Title of the Wikipedia page.
    language: str
        Language code for Wikipedia (default is English: 'en').

    Returns
    -------
    summary: str
        The text of the Wikipedia page summary.
    fullurl: str
        The URL of the Wikipedia page.
    """
    wiki_wiki = wikipediaapi.Wikipedia(
        language=language,
        user_agent="PrivateResearch (https://github.com/N-Shimoda; shimoda.naoki.77s@st.kyoto-u.ac.jp)",
    )
    page = wiki_wiki.page(title)

    if page.exists():
        return page.summary, page.fullurl
    else:
        # raise ValueError("Page does not exist for {}".format(title))
        return None, None


if __name__ == "__main__":

    # kg, _, _ = wiki_summary_to_kb('"I Have a Dream" speech', use_cache=False, verbose=True)
    kg, _, _ = wiki_summary_to_kb("Ichiro Suzuki", use_cache=False, verbose=True)
    print(kg)
