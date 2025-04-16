
"""
Module/Script Name: post_pusher.py

Description:
Push It Real Good blog publisher — now upgraded to support client-specific folders,
scheduled posts, and automatic post-to-posted transfer on success.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date: 2025-04-15
Last Modified Date: 2025-04-15

Comments:
- v1.05 Reads config path, processes HTML in pre-post/, moves to posted/ on success
"""

import os
import json
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

def get_schedule_timestamp(day_name, time_str):
    day_map = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    now = datetime.utcnow()
    today_index = now.weekday()
    target_index = day_map.index(day_name)
    days_ahead = (target_index - today_index + 7) % 7
    schedule_date = now + timedelta(days=days_ahead)
    hour, minute = map(int, time_str.split(':'))
    return datetime(schedule_date.year, schedule_date.month, schedule_date.day, hour, minute)

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, help='Path to the config JSON file')
args = parser.parse_args()

# Load config
with open(args.config) as f:
    config = json.load(f)

content_dir = config['content_dir']
pre_post_dir = Path(content_dir) / 'pre-post'
posted_dir = Path(content_dir) / 'posted'
posts_json = Path(content_dir) / 'posts.json'

if not posts_json.exists():
    print(f"❌ Missing posts.json in {content_dir}")
    exit(1)

with open(posts_json, 'r') as f:
    posts = {p['slug']: p for p in json.load(f)}

success, skipped, errors = 0, 0, 0

for html_file in pre_post_dir.glob("*.html"):
    slug = html_file.stem
    if slug not in posts:
        print(f"⚠️ Skipping {slug} — no entry in posts.json")
        skipped += 1
        continue

    post_meta = posts[slug]
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    data = {
        "title": post_meta['title'],
        "slug": slug,
        "content": content,
        "status": config.get("post_status", "draft"),
        "categories": config.get("category_ids", []),
        "meta": {
            "rank_math_description": post_meta.get("rank_math_description", ""),
            "rank_math_focus_keyword": post_meta.get("focus_keyword", "")
        }
    }

    if config["post_status"] == "schedule":
        schedule_time = get_schedule_timestamp(config["schedule_day"], config["schedule_time"])
        data["date_gmt"] = schedule_time.isoformat()
        data["status"] = "future"

    try:
        media_url = post_meta.get("featured_image_url") or config.get("featured_image_url")
        if media_url:
            media_resp = requests.post(
                f"{config['wp_url'].rstrip('/')}/wp-json/wp/v2/media",
                headers={"Content-Disposition": f"attachment; filename={slug}.jpg"},
                data=requests.get(media_url).content,
                auth=(config["username"], config["app_password"])
            )
            if media_resp.ok:
                data["featured_media"] = media_resp.json().get("id")

        resp = requests.post(
            f"{config['wp_url'].rstrip('/')}/wp-json/wp/v2/posts",
            auth=(config["username"], config["app_password"]),
            json=data
        )

        if resp.status_code == 201:
            print(f"✅ Posted: {slug}")
            html_file.rename(posted_dir / html_file.name)
            success += 1
        else:
            print(f"❌ Error posting {slug}: {resp.status_code} {resp.text}")
            errors += 1

    except Exception as e:
        print(f"❌ Exception for {slug}: {str(e)}")
        errors += 1

print(f"✅ Success: {success} | ⚠️ Skipped: {skipped} | ❌ Errors: {errors}")
