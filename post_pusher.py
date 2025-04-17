"""
Module/Script Name: post_pusher.py

Description:
Handles automated WordPress blog publishing: reads HTML files, uploads featured images,
creates or schedules posts via the WP REST API, and moves processed files.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date: 2025-04-14
Last Modified Date: 2025-04-16

Comments:
- v1.05 Ready to Zip and Ship: added logging and robust error handling
"""

import argparse
import json
import os
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from requests.exceptions import HTTPError, RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_schedule_timestamp(day_name: str, time_str: str) -> int:
    """Return a UNIX timestamp for the next occurrence of day_name at time_str (HH:MM)"""
    today = datetime.now()
    target_time = datetime.strptime(time_str, "%H:%M").time()
    days_ahead = (list(calendar.day_name).index(day_name) - today.weekday() + 7) % 7
    if days_ahead == 0 and today.time() >= target_time:
        days_ahead = 7
    target = datetime.combine(today.date(), target_time) + timedelta(days=days_ahead)
    return int(target.timestamp())


def publish_file(file_path: Path, config: dict):
    """Process a single HTML file: upload image, post or schedule on WP, and move file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("I/O error reading '%s': %s", file_path, e)
        return

    # Featured image upload
    img_url = config.get("featured_image_url")
    if img_url and img_url.startswith("file://"):
        local_path = img_url.replace("file://", "")
        try:
            with open(local_path, "rb") as img_file:
                files = {"file": img_file}
                resp = requests.post(
                    f"{config['wp_url'].rstrip('/')}/wp-json/wp/v2/media",
                    auth=(config["username"], config["app_password"]),
                    files=files,
                )
                resp.raise_for_status()
                img_id = resp.json().get("id")
                logger.info("Uploaded featured image '%s' → ID %s", local_path, img_id)
        except (OSError, HTTPError) as e:
            logger.error("Failed to upload image '%s': %s", local_path, e)
            img_id = None
    else:
        img_id = None

    # Build post payload
    payload = {
        "title": file_path.stem.replace("-", " ").title(),
        "content": content,
        "status": config.get("post_status", "draft"),
    }
    if img_id:
        payload["featured_media"] = img_id

    # Schedule if needed
    if config.get("post_status") == "schedule":
        ts = get_schedule_timestamp(
            config.get("schedule_day", "Monday"), config.get("schedule_time", "00:00")
        )
        payload["date"] = datetime.fromtimestamp(ts).isoformat()
        logger.info("Scheduling post '%s' for %s", payload["title"], payload["date"])

    # Create or update post
    try:
        resp = requests.post(
            f"{config['wp_url'].rstrip('/')}/wp-json/wp/v2/posts",
            auth=(config["username"], config["app_password"]),
            json=payload,
        )
        resp.raise_for_status()
        post_id = resp.json().get("id")
        logger.info("Posted '%s' → Post ID %s", payload["title"], post_id)
    except HTTPError as e:
        logger.error("HTTP error posting '%s': %s", payload["title"], e)
    except RequestException as e:
        logger.error("Request exception for '%s': %s", payload["title"], e)

    # Move file to posted folder
    try:
        dest = file_path.parent.parent / "posted" / file_path.name
        file_path.replace(dest)
        logger.info("Moved '%s' → '%s'", file_path.name, dest)
    except OSError as e:
        logger.error("Error moving '%s' to posted: %s", file_path.name, e)


def load_config(config_path: str) -> dict:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Configuration file not found: %s", config_path)
        raise
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in config file: %s", e)
        raise


def main():
    parser = argparse.ArgumentParser(description="Publish posts to WordPress")
    parser.add_argument("--config", required=True, help="Path to JSON config file")
    args = parser.parse_args()

    config = load_config(args.config)
    source = Path(config["content_dir"]) / "pre-post"
    for html_file in source.glob("*.html"):
        publish_file(html_file, config)


if __name__ == "__main__":
    main()
