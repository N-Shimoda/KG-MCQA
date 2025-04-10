import json
import os
from datetime import datetime

import wikipediaapi
from dotenv import load_dotenv
from tqdm import tqdm


def load_wiki_agent_params() -> tuple[str, str]:
    """
    Load Wikipedia agent information from environment variables.

    Returns
    -------
    tuple[str, str]
        Tuple containing the project name and mail address.
    """
    # Load environment variables from .env file
    load_dotenv()

    project_name = os.getenv("WIKI_PRJ_NAME")
    if not project_name:
        project_name = input("Enter the project name (WIKI_PRJ_NAME): ")

    mail_address = os.getenv("WIKI_MAIL")
    if not mail_address:
        mail_address = input("Enter the mail address (WIKI_MAIL): ")

    return project_name, mail_address


def get_wiki_titles(targets: list[str]) -> list[str]:
    """
    Find Wikipedia page titles for the specified targets.

    Parameters
    ----------
    targets : list[str]
        List of target Wikipedia pages.

    Returns
    -------
    list[str]
        List of Wikipedia page titles.
    """
    project_name, mail_address = load_wiki_agent_params()
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent=f"{project_name} ({mail_address})",
        language="en",
    )
    titles = []
    for target in targets:
        page = wiki_wiki.page(target)
        titles.append(page.title if page.exists() else None)
    return titles


def assign_sub_dir(title: str) -> str:
    """
    Assign sub-directory based on the first character of the title.

    Parameters
    ----------
    title : str
        Title of the Wikipedia page.

    Returns
    -------
    str
        Sub-directory name.
    """
    first_char = title[0].lower()
    return first_char if first_char.isalpha() else "_others"


def download_wiki_pages(targets: list[str], out_dir: str, tqdm_disable: bool = False) -> None:
    """
    Download Wikipedia articles for target titles and save them in the specified directory.

    Parameters
    ----------
    targets : list[str]
        List of target Wikipedia pages to download.
    out_dir : str
        Directory to save the downloaded pages.
    tqdm_disable : bool
        Disable tqdm progress bar if set to True.
    """
    # Wikipedia API
    project_name, mail_address = load_wiki_agent_params()
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent=f"{project_name} ({mail_address})",
        language="en",
    )

    # date
    today_date = datetime.now()

    for target in tqdm(targets, desc="Downloading Wikipedia pages", disable=tqdm_disable):
        page = wiki_wiki.page(target)
        if page.exists():
            # article data
            data = {
                "title": page.title,
                "fullurl": page.fullurl,
                "retrieved-date": today_date.strftime("%Y/%m/%d %H:%M:%S"),
                "converted": False,
                "summary": page.summary,
            }

            # Create the directory if not exists
            sub_dir = assign_sub_dir(page.title)
            os.makedirs(f"{out_dir}/{sub_dir}", exist_ok=True)

            # Save article to JSON file
            output_path = f"{out_dir}/{sub_dir}/{page.title}.json"
            with open(output_path, "w", encoding="utf-8") as output_file:
                json.dump(data, output_file, indent=4)
        else:
            continue


if __name__ == "__main__":
    # Example usage
    targets = [
        "Kyoto University",
        "Machine Learning",
        "AI",
        "éclair",
        "クラシック音楽",
        "123 Start",
    ]
    download_wiki_pages(targets, out_dir="wikipedia")
