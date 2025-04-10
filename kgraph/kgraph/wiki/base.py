import asyncio
import json
import os
from datetime import datetime

import wikipediaapi
from aiohttp import ClientSession
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
    Wrapper for the asynchronous get_wiki_titles_async function.

    Parameters
    ----------
    targets : list[str]
        List of target Wikipedia pages.

    Returns
    -------
    list[str]
        List of Wikipedia page titles.
    """

    async def fetch_page_title(session: ClientSession, wiki_wiki: wikipediaapi.Wikipedia, target: str) -> str:
        """
        Fetch the title of a Wikipedia page asynchronously.

        Parameters
        ----------
        session : ClientSession
            The aiohttp session for making requests.
        wiki_wiki : wikipediaapi.Wikipedia
            Wikipedia API instance.
        target : str
            Target Wikipedia page.

        Returns
        -------
        str
            Title of the Wikipedia page if it exists, otherwise None.
        """
        page = wiki_wiki.page(target)
        return page.title if page.exists() else None

    async def get_wiki_titles_async(targets: list[str]) -> list[str]:
        """
        Find Wikipedia page titles for the specified targets asynchronously.

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

        async with ClientSession() as session:
            tasks = [fetch_page_title(session, wiki_wiki, target) for target in targets]
            return await asyncio.gather(*tasks)

    return asyncio.run(get_wiki_titles_async(targets))


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


async def download_wiki_pages_async(
    targets: list[str] | set[str], out_dir: str, tqdm_disable: bool = False
) -> list[tuple[str, str]]:
    """
    Download Wikipedia articles for the specified target titles asynchronously and save them as JSON files
    in the specified output directory.

    Parameters
    ----------
    targets: list[str] | set[str]
        A list of Wikipedia page titles to download.
    out_dir: str
        The directory where the downloaded pages will be saved. Subdirectories may be created based on the titles.
    tqdm_disable : bool, optional
        If True, disables the tqdm progress bar. Defaults to False.

    Returns
    -------
    list[tuple[str, str]]
        A list of tuples, where each tuple contains the title and full URL of a successfully downloaded Wikipedia page.

    Notes
    -----
    - The function uses the Wikipedia API to fetch page data.
    - Each downloaded page is saved as a JSON file containing metadata such as title, URL, retrieval date,
        and a summary of the page.
    - The output directory structure may include subdirectories based on the page titles.
    - This function is asynchronous and uses asyncio for concurrent downloads.
    """
    # Wikipedia API
    project_name, mail_address = load_wiki_agent_params()
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent=f"{project_name} ({mail_address})",
        language="en",
    )

    # date
    today_date = datetime.now()

    async def fetch_and_save(target: str) -> tuple[str, str]:
        """
        Fetch and save a Wikipedia page asynchronously.

        Parameters
        ----------
        target : str
            Target Wikipedia page.

        Returns
        -------
        page.title : str
            Title of the Wikipedia page if it exists, otherwise original query text.
        page.fullurl : str | None
            Full URL of the Wikipedia page if it exists, otherwise None.
        """
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
        return page.title, page.fullurl

    tasks = [
        fetch_and_save(target) for target in tqdm(targets, desc="Downloading Wikipedia pages", disable=tqdm_disable)
    ]
    res = await asyncio.gather(*tasks)
    return res


def download_wiki_pages(
    targets: list[str] | set[str], out_dir: str, tqdm_disable: bool = False
) -> list[tuple[str, str]]:
    """
    Wrapper for the asynchronous download_wiki_pages_async function.

    Parameters
    ----------
    targets : list[str] | set[str]
        List or set of target Wikipedia pages to download.
    out_dir : str
        Directory to save the downloaded pages.
    tqdm_disable : bool, optional
        If True, disables the tqdm progress bar. Defaults to False.

    Returns
    -------
    list[tuple[str, str]]
        A list of tuples, where each tuple contains the title and full URL of a successfully downloaded Wikipedia page.
    """
    return asyncio.run(download_wiki_pages_async(targets, out_dir, tqdm_disable))


if __name__ == "__main__":
    # Example usage
    targets = ["Kyoto University", "Machine Learning", "AI", "éclair", "classical music", "123 Start", "Naoki Shimoda"]
    res = download_wiki_pages(targets, out_dir="wikipedia")
    print(res)
