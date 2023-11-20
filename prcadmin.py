# SPDX-License-Identifier: LGPL-3.0-or-later
"""Analyze and save the administrative division of the People's Republic of China."""
# require Python 3.9 or later
import sys

if sys.version_info < (3, 9):
    raise RuntimeError("Python 3.9+ required.")

import argparse
import asyncio
import csv
import urllib.parse
import logging

import aiohttp
from bs4 import BeautifulSoup
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

TOP_URL = "http://www.stats.gov.cn/sj/tjbz/tjyqhdmhcxhfdm/{year}/"

t_saved = tqdm(desc="Saved", position=0, unit=" divisions")
t_scanned = tqdm(desc="Scanned", position=1, unit=" pages")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def analyze_page(url: str) -> tuple[list[tuple[str, str, str]], list[str]]:
    """Analyze the page and return the administrative division and subpages.

    Parameters
    ----------
    url : str
        The url of the page to be analyzed.

    Returns
    -------
    list[tuple(str, str)]
        List of administrative division. Each element is a tuple of the code, name, and level.
    list[str]
        List of subpages. Each element is a url.
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                html = await response.text()
        except aiohttp.ClientError:
            with logging_redirect_tqdm():
                logger.exception("Failed to get %s, retry after 5 s...", url)
            await asyncio.sleep(5)
            return [], [url]
    if "jsjiami.com.v6" in html:
        # too fast, retry after 1 min
        with logging_redirect_tqdm():
            logger.warning("Too fast to get %s, retry after 1 min...", url)
        await asyncio.sleep(60)
        return [], [url]
    bs4_obj = BeautifulSoup(html, "html.parser")
    for admin_type in ("province", "city", "county", "town", "village"):
        trs = bs4_obj.find_all("tr", class_=admin_type + "tr")
        if trs:
            break
    else:
        # No administrative division found.
        return [], []
    divisions = []
    subpages = []
    for tr in trs:
        tds = tr.find_all("td")
        if admin_type == "province":
            for td in tds:
                name = td.text
                code = td.find("a").get("href").split("/")[-1].split(".")[0] + (
                    "0" * 10
                )
                divisions.append((code, name, admin_type))
                subpages.append(td.find("a").get("href"))
        else:
            code = tds[0].text
            name = tds[-1].text
            divisions.append((code, name, admin_type))
            if tds[0].find("a") and tds[0].find("a").get("href"):
                # some a tags do not have href
                subpages.append(tds[0].find("a").get("href"))
    # make subpages absolute url based on the current url
    subpages = [urllib.parse.urljoin(url, subpage) for subpage in subpages]
    return divisions, subpages


async def worker(queue, queue_writer):
    """A worker to process the queue.

    Parameters
    ----------
    queue : asyncio.Queue
        The queue to be processed.
    """
    while True:
        url = await queue.get()
        divisions, subpages = await analyze_page(url)
        # save divisions
        for division in divisions:
            await queue_writer.put(division)
        for subpage in subpages:
            await queue.put(subpage)
        t_scanned.update(1)
        queue.task_done()


async def writer(queue, fn):
    """A worker to write the results to a csv file.

    Parameters
    ----------
    queue : asyncio.Queue
        The queue to be processed.
    fn : str
        The name of the file to save the results.
    """
    # create csv file to save results
    with open(fn, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["code", "name", "level"])
        writer.writeheader()
        while True:
            division = await queue.get()
            writer.writerow(
                {"code": division[0].strip(), "name": division[1].strip(), "level": division[2]}
            )
            queue.task_done()
            t_saved.update(1)


async def run_queue(url: str, fn: str, ntasks: int = 5):
    """Create a queue and run it.

    Parameters
    ----------
    url : str
        The url of the page to be analyzed.
    fn : str
        The name of the file to save the results.
    ntasks : int, optional
        The number of worker tasks to process the queue concurrently, by default 10
    """
    queue = asyncio.Queue()
    queue.put_nowait(url)
    queue_writer = asyncio.Queue()

    # Create five worker tasks to process the queue concurrently.
    for _ in range(ntasks):
        asyncio.create_task(worker(queue, queue_writer))
    # Create a writer task to write the results to a csv file.
    asyncio.create_task(writer(queue_writer, fn))
    await queue.join()
    await queue_writer.join()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Analyze and save the administrative division of the People's Republic of China."
    )
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        required=True,
        help="The year of the administrative division.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="The name of the file to save the results.",
    )
    parser.add_argument(
        "--ntasks",
        type=int,
        default=5,
        help="The number of worker tasks to process the queue concurrently.",
    )
    args = parser.parse_args()
    url = TOP_URL.format(year=args.year)
    asyncio.run(run_queue(url, args.file, ntasks=args.ntasks))


if __name__ == "__main__":
    main()
