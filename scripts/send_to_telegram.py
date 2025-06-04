"""
send_to_telegram.py

This script sends paper summaries to a Telegram channel as audio messages,
followed by text messages. It runs hourly, selecting one summary from the
latest day's update in the README that hasn't been sent before.
"""

import asyncio
import json
import logging
import os
import random
import re
from pathlib import Path

from openai import OpenAI
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from logger import logger

# Configuration
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Initialize the Bot and OpenAI client
bot = Bot(token=BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# Supported voices for text-to-speech
VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# Path for the JSON file to track sent papers
SENT_PAPERS_FILE = Path(__file__).parent / "sent_papers.json"

def load_sent_papers():
    """
    Loads the list of papers that have already been sent.
    """
    if SENT_PAPERS_FILE.exists():
        with open(SENT_PAPERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_sent_papers(sent_papers):
    """
    Saves the list of papers that have been sent.
    """
    with open(SENT_PAPERS_FILE, 'w') as f:
        json.dump(sent_papers, f)

def get_latest_summary(sent_papers):
    """
    Extracts a summary from the README file that hasn't been sent before.
    """
    with open("README.md", "r") as f:
        content = f.read()

    # Find the latest date section
    sections = content.split("## Papers for ")
    if len(sections) < 2:
        return None

    latest_section = sections[1]
    summaries = latest_section.split("|\n")

    if len(summaries) < 4:
        return None

    # Select a random summary that hasn't been sent before
    new_summaries = [s for s in summaries[2:] if not any(paper_id in s for paper_id in sent_papers)]
    if not new_summaries:
        return None

    summary = random.choice(new_summaries)
    parts = summary.split(" | ")

    if len(parts) < 2:
        return None

    title_author = parts[0].split("| ")
    title_with_links = title_author[1].strip()
    authors = title_author[2].strip()
    summary_text = parts[1].strip()

    # Extract links
    arxiv_link_match = re.search(r'\[arXiv\]\((.*?)\)', title_with_links)
    hf_link_match = re.search(r'\[HuggingFace\]\((.*?)\)', title_with_links)
    
    arxiv_link = arxiv_link_match.group(1) if arxiv_link_match else None
    hf_link = hf_link_match.group(1) if hf_link_match else None

    # Remove links from title
    title = re.sub(r'\(Read more on \[arXiv\].*?\[HuggingFace\].*?\)', '', title_with_links).strip()

    # Extract paper ID from arXiv link
    paper_id = arxiv_link.split('/')[-1] if arxiv_link else None

    return title, authors, summary_text, arxiv_link, hf_link, paper_id

async def text_to_speech(text, title):
    """
    Converts text to speech using OpenAI's API.

    Args:
    - text (str): The text to convert to speech.
    - title (str): The title of the paper.

    Returns:
    - speech_file_path (Path): The path to the audio file.
    """
    # Create a valid filename from the title
    valid_filename = re.sub(r'[^\w\-_\. ]', '_', title)
    speech_file_path = Path(__file__).parent / f"{valid_filename}.mp3"
    voice = random.choice(VOICES)

    try:
        response = client.audio.speech.create(model="tts-1", voice=voice, input=text)
        response.stream_to_file(speech_file_path)
        return speech_file_path
    except Exception as e:
        logger.error(f"Failed to generate speech: {e}")
        return None

def escape_markdown(text):
    """
    Escape special characters for Markdown V2 formatting.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

async def send_audio(audio_file):
    """
    Sends an audio file to the specified Telegram channel.

    Args:
    - audio_file (Path): The path to the audio file.
    - title (str): The title of the paper.
    - authors (str): The authors of the paper.
    - summary (str): The summary of the paper.
    """
    try:
        with open(audio_file, "rb") as audio:
            await bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=audio,
                caption="Listen to the summary of the paper\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        logger.info("Audio sent successfully.")
    except FileNotFoundError:
        logger.error(f"Audio file not found: {audio_file}")
    except TelegramError as e:
        logger.error(f"Failed to send audio: {e}")

async def send_text_summary(title, authors, summary, arxiv_link, hf_link):
    """
    Sends a text summary to the specified Telegram channel.

    Args:
    - title (str): The title of the paper.
    - authors (str): The authors of the paper.
    - summary (str): The summary of the paper.
    - arxiv_link (str): The arXiv link of the paper.
    - hf_link (str): The Hugging Face link of the paper.
    """
    escaped_title = escape_markdown(title.rstrip(")"))
    escaped_authors = escape_markdown(authors)
    escaped_summary = escape_markdown(summary)
    escaped_arxiv_link = escape_markdown(arxiv_link)
    escaped_hf_link = escape_markdown(hf_link)

    message = f"*{escaped_title}*\n\nby {escaped_authors}\n\n{escaped_summary}\n\n"
    message += f"Read more on [arXiv]({escaped_arxiv_link}) or [HuggingFace]({escaped_hf_link})"

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        logger.info("Text summary sent successfully.")
    except TelegramError as e:
        logger.error(f"Failed to send text summary: {e}")

async def main():
    """
    Main function to send media and text summary.
    """
    sent_papers = load_sent_papers()
    result = get_latest_summary(sent_papers)
    if not result:
        logger.info("No new summaries found in README.")
        return

    title, authors, summary, arxiv_link, hf_link, paper_id = result
    audio_file_path = await text_to_speech(summary, title)
    if audio_file_path:
        await send_text_summary(title, authors, summary, arxiv_link, hf_link)
        await send_audio(audio_file_path)
        os.remove(audio_file_path)  # Clean up the audio file after sending

        # Add the paper ID to the list of sent papers and save
        sent_papers.append(paper_id)
        save_sent_papers(sent_papers)
        logger.info(f"Sent summary for paper ID: {paper_id}")

if __name__ == "__main__":
    asyncio.run(main())
