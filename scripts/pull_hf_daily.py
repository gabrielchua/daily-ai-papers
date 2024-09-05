"""
pull_hf_daily.py

This script pulls the daily papers from Hugging Face's papers page, downloads their PDFs,
and saves their information in a JSON file.
"""

# Standard library imports
import json
import os
import re
from datetime import datetime
from typing import List, Dict

# Third party imports
import requests
from bs4 import BeautifulSoup

HF_URL = "https://huggingface.co/papers"


def download_pdf(arxiv_id: str, save_path: str) -> bool:
    """
    Downloads the PDF of a paper from arXiv given its ID.

    Args:
        arxiv_id (str): The arXiv ID of the paper.
        save_path (str): The path where the PDF will be saved.

    Returns:
        bool: True if the download was successful, False otherwise.
    """
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        return True
    return False


def pull_hf_daily() -> None:
    """
    Pulls the daily papers from Hugging Face's papers page, downloads their PDFs,
    and saves their information in a JSON file.
    """
    response = requests.get(HF_URL)
    soup = BeautifulSoup(response.content, "html.parser")

    papers: List[Dict[str, str]] = []
    seen_ids = set()  # Set to track seen arXiv IDs
    temp_pdf_dir = "temp_pdfs"
    os.makedirs(
        temp_pdf_dir, exist_ok=True
    )  # Create temp_pdfs directory if it doesn't exist

    # Locate the relevant div elements
    for paper_div in soup.find_all("div", class_="w-full"):
        # Extract the title
        title_tag = paper_div.find("a", class_="line-clamp-3")
        if title_tag:
            title = title_tag.text.strip()
        else:
            print("Title not found for a paper")
            continue

        # Extract the paper ID from the link
        link = title_tag["href"]
        arxiv_id_match = re.search(r"/papers/(\d+\.\d+)", link)
        if arxiv_id_match:
            arxiv_id = arxiv_id_match.group(1)
        else:
            print(f"Could not extract arXiv ID from link: {link}")
            continue

        # Check for duplicates using arXiv ID
        if arxiv_id in seen_ids:
            print(f"Duplicate paper detected with ID {arxiv_id}, skipping.")
            continue
        seen_ids.add(arxiv_id)  # Add ID to set of seen IDs

        # Extract the authors
        authors = []
        for li in paper_div.find_all("li"):
            author = li.get("title")
            if author:
                authors.append(author)

        # Create the full link to the paper
        full_link = f"https://arxiv.org/abs/{arxiv_id}"

        # Attempt to download the PDF
        pdf_path = os.path.join(temp_pdf_dir, f"{arxiv_id}.pdf")
        if download_pdf(arxiv_id, pdf_path):
            papers.append(
                {
                    "title": title,
                    "authors": ", ".join(authors),
                    "link": full_link,
                    "pdf_path": pdf_path,
                }
            )
        else:
            print(f"Failed to download PDF for {arxiv_id}")

    date = datetime.now().strftime("%Y-%m-%d")
    data_dir = "data"
    print(f"Ensuring data directory exists: {data_dir}")
    os.makedirs(data_dir, exist_ok=True)  # Create 'data' directory if it doesn't exist
    data_file_path = os.path.join(data_dir, f"{date}_papers.json")

    print(f"Writing data to {data_file_path}")
    with open(data_file_path, "w") as f:
        json.dump(papers, f, indent=2)
    print(f"Saved {len(papers)} papers' information and PDFs")


if __name__ == "__main__":
    pull_hf_daily()
