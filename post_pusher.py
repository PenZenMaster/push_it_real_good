"""
Module/Script Name: post_pusher.py

Description:
Handles automated WordPress blog publishing: reads HTML files, uploads featured images,
creates or schedules posts via the WP REST API, and moves processed files.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date: 2025-04-14
Last Modified Date: 2025-04-17

Comments:
- v1.06 Ready to Zip and Ship: refactored media upload helper, added type hints and docstrings
"""

import argparse
import json
import logging
import calendar
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from requests.exceptions import HTTPError, RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_schedule_timestamp(day_name: str, time_str: str) -> int:
    """Return a UNIX timestamp for the next occurrence of day_name at time_str (HH:MM)."""
    today = datetime.now()
    target_time = datetime.strptime(time_str, "%H:%M").time()
    days_ahead = (list(calendar.day_name).index(day_name) - today.weekday() + 7) % 7
    if days_ahead == 0 and today.time() >= target_time:
        days_ahead = 7
    target = datetime.combine(today.date(), target_time) + timedelta(days=days_ahead)
    return int(target.timestamp())


def upload_featured_image(local_path: str, config: Dict[str, Any]) -> Optional[int]:
    """Upload a local image file to WordPress and return the media ID, or None on failure."""
    url = f"{config['wp_url'].rstrip('/')}/wp-json/wp/v2/media"
    try:
        with open(local_path, "rb") as img_file:
            files = {"file": img_file}
            response = requests.post(
                url, auth=(config["username"], config["app_password"]), files=files
            )
            response.raise_for_status()
            media_id = response.json().get("id")
            logger.info("Uploaded featured image '%s' → ID %s", local_path, media_id)
            return media_id
    except OSError as e:
        logger.error("I/O error uploading image '%s': %s", local_path, e)
    except HTTPError as e:
        logger.error("HTTP error uploading image '%s': %s", local_path, e)
    except RequestException as e:
        logger.error("Request exception uploading image '%s': %s", local_path, e)
    return None


def publish_file(file_path: Path, config: Dict[str, Any]) -> None:
    """Process a single HTML file: upload image, post or schedule to WordPress, and move the file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("I/O error reading '%s': %s", file_path, e)
        return

    # Handle featured image
    img_id: Optional[int] = None
    img_url = config.get("featured_image_url", "")
    if img_url.startswith("file://"):
        local_path = img_url.replace("file://", "")
        img_id = upload_featured_image(local_path, config)

    # Build post payload
    payload: Dict[str, Any] = {
        "title": file_path.stem.replace("-", " ").title(),
        "content": content,
        "status": config.get("post_status", "draft"),
    }
    if img_id:
        payload["featured_media"] = img_id

    # Schedule post if needed
    if config.get("post_status") == "schedule":
        ts = get_schedule_timestamp(
            config.get("schedule_day", "Monday"), config.get("schedule_time", "00:00")
        )
        payload["date"] = datetime.fromtimestamp(ts).isoformat()
        logger.info("Scheduling post '%s' for %s", payload["title"], payload["date"])

    # Create post on WordPress
    try:
        response = requests.post(
            f"{config['wp_url'].rstrip('/')}/wp-json/wp/v2/posts",
            auth=(config["username"], config["app_password"]),
            json=payload,
        )
        response.raise_for_status()
        post_id = response.json().get("id")
        logger.info("Posted '%s' → Post ID %s", payload["title"], post_id)
    except HTTPError as e:
        logger.error("HTTP error posting '%s': %s", payload["title"], e)
    except RequestException as e:
        logger.error("Request exception for '%s': %s", payload["title"], e)

    # Move file to 'posted' folder
    try:
        dest = file_path.parent.parent / "posted" / file_path.name
        file_path.replace(dest)
        logger.info("Moved '%s' → '%s'", file_path.name, dest)
    except OSError as e:
        logger.error("Error moving '%s' to posted: %s", file_path.name, e)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load and return the JSON configuration from the given path."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Configuration file not found: %s", config_path)
        raise
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in config file: %s", e)
        raise


def main() -> None:
    """Entry point: parse args, load config, and process all HTML files in pre-post directory."""
    parser = argparse.ArgumentParser(description="Publish posts to WordPress")
    parser.add_argument("--config", required=True, help="Path to JSON config file")
    args = parser.parse_args()

    config = load_config(args.config)
    source_dir = Path(config["content_dir"]) / "pre-post"
    for html_file in source_dir.glob("*.html"):
        publish_file(html_file, config)


if __name__ == "__main__":
    main()
