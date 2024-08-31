"""
summarize_papers.py

This script summarizes the daily papers pulled from Hugging Face's papers page,
updates the README with the summaries, and cleans up temporary files.
"""

import json
import os
from datetime import datetime
from typing import List, Dict
import google.generativeai as genai
import PIL.Image

# Configure the Gemini API
genai.configure(api_key=os.environ['GEMINI_API_KEY'])

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def summarize_paper(title: str, authors: str, pdf_path: str) -> str:
    """
    Summarizes a research paper using the Gemini API.

    Args:
        title (str): The title of the paper.
        authors (str): The authors of the paper.
        pdf_path (str): The path to the PDF of the paper.

    Returns:
        str: The summary of the paper.
    """
    pdf_image = PIL.Image.open(pdf_path)
    prompt = f"""
    Summarize the given AI research paper in 4-5 sentences.

    Highlight the key results, and how it may be relevant to practitioners (e.g., AI Engineers, Data Scientists, etc).
    
    Here is additional information about the paper:
    Title: {title}
    Authors: {authors}
    """
    response = model.generate_content([prompt, pdf_image])
    return response.text

def update_readme(summaries: List[Dict[str, str]]) -> None:
    """
    Updates the README file with the summaries of the papers.

    Args:
        summaries (List[Dict[str, str]]): A list of dictionaries containing paper information and summaries.
    """
    date_str = datetime.now().strftime('%Y-%m-%d')
    new_content = f"## Papers for {date_str}\n\n"
    new_content += "| Title | Authors | Summary | Link |\n"
    new_content += "|-------|---------|---------|------|\n"
    for summary in summaries:
        new_content += f"| {summary['title']} | {summary['authors']} | {summary['summary']} | [Read more]({summary['link']}) |\n"

    with open('README.md', 'r') as f:
        existing_content = f.read()

    updated_content = f"# Daily Arxiv Paper Summaries\n\nThis summary is automated by GitHub actions, Gemini, and acknowledges the contributions by HuggingFace in curating this list.\n\nLast updated: {date_str}\n\n" + new_content + existing_content

    with open('README.md', 'w') as f:
        f.write(updated_content)

def main() -> None:
    """
    Main function to summarize papers, update the README, and clean up temporary files.
    """
    date = datetime.now().strftime("%Y-%m-%d")
    with open(f'data/{date}_papers.json', 'r') as f:
        papers = json.load(f)

    summaries = []
    for paper in papers:
        summary = summarize_paper(paper['title'], paper['authors'], paper['pdf_path'])
        summaries.append({**paper, 'summary': summary})

    update_readme(summaries)

    # Clean up temporary PDF files
    for paper in papers:
        if os.path.exists(paper['pdf_path']):
            os.remove(paper['pdf_path'])

if __name__ == "__main__":
    main()