import os

import wikipediaapi
from tqdm import tqdm


def load_wiki_agent() -> tuple[str, str]:
    """
    Load Wikipedia agent information from environment variables.

    Returns
    -------
    list[str]
        List of Wikipedia agent information.
    """
    # Load environment variables from .env file
    project_name = os.getenv("WIKI_PRJ_NAME")
    if not project_name:
        project_name = input("Enter the project name (WIKI_PRJ_NAME): ")

    mail_address = os.getenv("WIKI_MAIL")
    if not mail_address:
        mail_address = input("Enter the mail address (WIKI_MAIL): ")

    return project_name, mail_address


def download_wiki_page(targets: list[str], dir: str):
    """
    Download Wikipedia articles for the specified targets and save them in the specified directory.

    Parameters
    ----------
    targets : list[str]
        List of target Wikipedia pages to download.
    dir : str
        Directory to save the downloaded pages.
    """
    # Wikipedia API
    project_name, mail_address = load_wiki_agent()
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent=f"{project_name} ({mail_address})",
        language="en",
    )

    # Create the directory if it doesn't exist
    os.makedirs(dir, exist_ok=True)

    for target in tqdm(targets, desc="Downloading Wikipedia pages"):
        page = wiki_wiki.page(target)
        if page.exists():
            print("Title: {} ({})".format(page.title, page.fullurl))
            print("Summary: {}".format(page.summary))
        else:
            print("Page not found for {}".format(target))


if __name__ == "__main__":
    # Example usage
    targets = ["Kyoto University"]
    download_wiki_page(targets, dir="wikipedia")
