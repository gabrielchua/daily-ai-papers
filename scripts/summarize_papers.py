"""
summarize_papers.py

This script summarizes the daily papers pulled from Hugging Face's papers page,
updates the README with the summaries, and cleans up temporary files.
"""

# Standard library imports
import json
import os
import time
from datetime import datetime
from typing import List, Dict

# Third party imports
import google.generativeai as genai
from logger import logger

# Configure the Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def summarize_paper(title: str, authors: str, pdf_path: str, model_name: str) -> tuple[str, str]:
    """
    Summarizes a research paper and determines its category using the Gemini API.

    Args:
    - title (str): The title of the paper.
    - authors (str): The authors of the paper.
    - pdf_path (str): The path to the PDF of the paper.

    Returns:
    - tuple[str, str]: The summary and category of the paper.
    """

    model = genai.GenerativeModel(model_name=model_name)

    # Upload the PDF to Gemini
    pdf_file = genai.upload_file(path=pdf_path, display_name=f"paper_{title}")

    # Load the prompt template
    with open("templates/prompt_template.md", "r") as f:
        prompt_template = f.read()

    prompt = prompt_template.replace("{title}", title).replace("{authors}", authors)

    response = model.generate_content([pdf_file, prompt])
    response_text = response.text
    
    logger.info(f"Response received: {response_text}")

    # Remove markdown json formatting if response is in markdown code block format
    if response_text.startswith("```json"):
        logger.warning("Response contains markdown json code format - removing formatting")
        response_text = response_text.replace("```json", "").replace("```", "")
    
    response_data = json.loads(response_text)

    return response_data["summary"], response_data["category"]


def update_readme(summaries: List[Dict[str, str]]) -> None:
    """
    Updates the README file with the summaries and categories of the papers.

    Args:
    - summaries (List[Dict[str, str]]): A list of dictionaries containing paper information and summaries.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_content = f"\n\n## Papers for {date_str}\n\n"
    new_content += "| Category | Title | Authors | Summary |\n"
    new_content += "|----------|-------|---------|---------|\n"
    for summary in summaries:
        # Replace line breaks with spaces
        summary["summary"] = summary["summary"].replace("\n", " ")
        hf_link = summary['link'].replace("https://arxiv.org/abs/", "https://huggingface.co/papers/")
        new_content += f"| {summary['category']} | {summary['title']} (Read more on [arXiv]({summary['link']}) or [HuggingFace]({hf_link}))| {summary['authors']} | {summary['summary']} |\n"

    day = date_str.split("-")[2]

    # Write the new content to the archive
    # Create the archive directory if it doesn't exist
    year = date_str.split("-")[0]
    month = date_str.split("-")[1]
    os.makedirs(f"archive/{year}/{month}", exist_ok=True)
    with open(f"archive/{year}/{month}/{day}.md", "w") as f:
        f.write(new_content)

    # Update the README with the new content
    # Load the existing README
    with open("README.md", "r") as f:
        existing_content = f.read()

    # Load the intro template
    with open("templates/README_intro.md", "r") as f:
        intro_content = f.read()

    # Add the date to the intro
    date_str_readme = date_str.replace("-", "--")
    intro_content = intro_content.replace("{DATE}", f"{date_str_readme} \n \n")

    # Remove the existing header
    front_content = existing_content.split("## Papers for")[0]
    existing_content = existing_content.replace(front_content, "")

    # Combine the intro, new content, and existing content
    updated_content = intro_content + new_content + "\n\n" +  existing_content

    # Write the updated content to the README
    with open("README.md", "w") as f:
        f.write(updated_content)


def main() -> None:
    """
    Main function to summarize papers, update the README, and clean up temporary files.
    """
    date = datetime.now().strftime("%Y-%m-%d")
    with open(f"data/{date}_papers.json", "r") as f:
        papers = json.load(f)

    summaries = []
    for i, paper in enumerate(papers):
        try:
            if i != 0:
                time.sleep(60) # Sleep for 1 minute to avoid rate limiting

            summary, category = summarize_paper(
                title=paper["title"],
                authors=paper["authors"],
                pdf_path=paper["pdf_path"],
                model_name="gemini-2.0-pro-exp-02-05"
            )
            summaries.append({**paper, "summary": summary, "category": category})
        except Exception:
            try:
                logger.warning(f"Failed to summarize paper {paper['title']}. Trying with a different model.")
                summary, category = summarize_paper(
                    title=paper["title"],
                    authors=paper["authors"],
                    pdf_path=paper["pdf_path"],
                    model_name="gemini-2.0-flash-001"
                )
                summaries.append({**paper, "summary": summary, "category": category})
            except Exception as e:
                logger.error(f"Failed to summarize paper {paper['title']} with both models. Due to {e}")
                continue

    update_readme(summaries)

    # Clean up temporary PDF files
    for paper in papers:
        if os.path.exists(paper["pdf_path"]):
            os.remove(paper["pdf_path"])


if __name__ == "__main__":
    main()
