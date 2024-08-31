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

    # Upload the PDF to Gemini
    pdf_file = genai.upload_file(path=pdf_path, display_name=f"paper_{title}")

    prompt = f"""
    Read the AI research paper carefully and summarise it in 4-5 sentences. Be terse and include the key details.

    Be formal and academic in your tone.

    Highlight the key results, and how it may be relevant to practitioners (e.g., AI Engineers, Data Scientists, etc).
    
    Here is additional information about the paper:
    Title: {title}
    Authors: {authors}
    """
    response = model.generate_content([pdf_file, prompt])
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
        # Replace line breaks with spaces
        summary['summary'] = summary['summary'].replace('\n', ' ')
        new_content += f"| {summary['title']} | {summary['authors']} | {summary['summary']} | [Read more]({summary['link']}) |\n"

    with open('README.md', 'r') as f:
        existing_content = f.read()

    # Remove the existing header
    front_content = existing_content.split("## Papers for")[0]
    existing_content = existing_content.replace(front_content, "")

    updated_content = f"# Daily AI Papers \n\nThis summary is automated the summary of [HuggingFace's Daily Papers](https://huggingface.co/papers), using Gemini and GitHub actions.\n\nLast updated: {date_str}\n\n" + new_content + existing_content
     
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