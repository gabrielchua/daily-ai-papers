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
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    return False


def pull_hf_daily() -> None:
    """
    Pulls the daily papers from Hugging Face's papers page, downloads their PDFs,
    and saves their information in a JSON file.
    """
    url = "https://huggingface.co/papers"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    papers: List[Dict[str, str]] = []
    temp_pdf_dir = "temp_pdfs"
    os.makedirs(temp_pdf_dir, exist_ok=True)

    for paper in soup.find_all('article', class_='paper-card'):
        title = paper.find('h3').text.strip()
        authors = paper.find('p', class_='authors').text.strip()
        link = paper.find('a', class_='paper-title')['href']

        # Extract arXiv ID from the link
        arxiv_id_match = re.search(r'/papers/(\d+\.\d+)', link)
        if arxiv_id_match:
            arxiv_id = arxiv_id_match.group(1)
            pdf_path = os.path.join(temp_pdf_dir, f"{arxiv_id}.pdf")

            if download_pdf(arxiv_id, pdf_path):
                papers.append({
                    'title': title,
                    'authors': authors,
                    'link': f"https://arxiv.org/abs/{arxiv_id}",
                    'pdf_path': pdf_path
                })
            else:
                print(f"Failed to download PDF for {arxiv_id}")
        else:
            print(f"Could not extract arXiv ID from link: {link}")

    date = datetime.now().strftime("%Y-%m-%d")
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)  # Create 'data' directory if it doesn't exist
    with open(os.path.join(data_dir, f'{date}_papers.json'), 'w') as f:
        json.dump(papers, f, indent=2)

    print(f"Saved {len(papers)} papers' information and PDFs")


if __name__ == "__main__":
    pull_hf_daily()