"""
Module/Script Name: post_pusher.py

Description:
Pushes multiple HTML blog content files to a WordPress site using the REST API.
Each post is scheduled for consecutive Mondays at 8:00 AM and includes RankMath SEO metadata.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-04-13

Last Modified Date:
2025-04-13

Comments:
- Version 1.01 β — Added batch scheduling of SEO blog posts with featured image and RankMath integration.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import mimetypes

# Instead of hardcoded `posts = [...]`, use:
with open("posts.json", "r", encoding="utf-8") as f:
    posts = json.load(f)


def load_config(config_path="config.json"):
    with open(config_path, "r") as file:
        return json.load(file)


def load_post_content(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def upload_featured_image(image_url, config, logger):
    try:
        image_name = image_url.split("/")[-1]
        image_data = requests.get(image_url).content
        mime_type, _ = mimetypes.guess_type(image_url)
        if not mime_type:
            mime_type = "image/jpeg"

        media_url = f"{config['wp_url']}/wp-json/wp/v2/media"
        headers = {
            "Content-Disposition": f"attachment; filename={image_name}",
            "Content-Type": mime_type,
        }

        response = requests.post(
            media_url,
            headers=headers,
            data=image_data,
            auth=HTTPBasicAuth(config["username"], config["app_password"]),
        )
        if response.status_code in [200, 201]:
            media_id = response.json().get("id")
            logger.write(f"✅ Uploaded {image_name} → Media ID: {media_id}\n")
            print(f"✅ Image uploaded: {image_name} → Media ID: {media_id}")
            return media_id
        else:
            logger.write(
                f"❌ Failed to upload image: {image_name}\n{response.json()}\n"
            )
            print(f"❌ Failed to upload image: {image_name}")
            return None
    except Exception as e:
        logger.write(f"🔥 Exception uploading image: {image_url}\n{e}\n")
        print(f"🔥 Exception uploading image: {image_url}")
        return None


def post_exists(slug, config):
    url = f"{config['wp_url']}/wp-json/wp/v2/posts?slug={slug}"
    response = requests.get(
        url, auth=HTTPBasicAuth(config["username"], config["app_password"])
    )
    return response.status_code == 200 and bool(response.json())


def get_publish_date(weeks_ahead=0):
    today = datetime.now()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0 and today.hour >= 8:
        days_until_monday = 7
    publish_date = today + timedelta(days=days_until_monday + (weeks_ahead * 7))
    return publish_date.replace(hour=8, minute=0, second=0, microsecond=0).isoformat()


def push_post(post, content, publish_date, config, logger, results):
    global success_count, skip_count, error_count, dupe_count

    slug = post.get("slug")
    title = post.get("title")
    focus_keyword = post.get("focus_keyword")
    meta_description = post.get("rank_math_description")
    image_url = post.get("featured_image_url", config.get("featured_image_url"))

    missing_fields = [
        key
        for key in ["slug", "title", "focus_keyword", "rank_math_description"]
        if key not in post
    ]
    if missing_fields:
        logger.write(
            f"⚠️ Skipping post due to missing fields: {slug or '[UNKNOWN SLUG]'} → {missing_fields}\n"
        )
        print(f"⚠️ Skipping {slug} → Missing fields: {missing_fields}")
        results["skipped"] += 1
        return

    if post_exists(slug, config):
        logger.write(f"⚠️ Skipping duplicate: {slug}\n")
        print(f"⚠️ Duplicate skipped: {slug}")
        results["duplicates"] += 1
        return

    media_id = upload_featured_image(image_url, config, logger)

    payload = {
        "title": title,
        "slug": slug,
        "content": content,
        "status": "future",
        "date": publish_date,
        "categories": config.get("category_ids", []),
        "featured_media": media_id,
        "meta": {
            "rank_math_focus_keyword": focus_keyword,
            "rank_math_description": meta_description,
        },
    }

    url = f"{config['wp_url']}/wp-json/wp/v2/posts"
    auth = HTTPBasicAuth(config["username"], config["app_password"])
    response = requests.post(url, auth=auth, json=payload)

    if response.status_code == 201:
        logger.write(f"✅ Scheduled: {title} → {publish_date}\n")
        print(f"✅ Scheduled: {title} → {publish_date}")
        results["success"] += 1
    else:
        logger.write(f"❌ Failed to schedule: {title}\n{response.json()}\n")
        print(f"❌ Failed to schedule: {title}")
        results["errors"] += 1


def batch_schedule_posts():
    results = {"success": 0, "skipped": 0, "errors": 0, "duplicates": 0}
    config = load_config()
    with open("post_pusher.log", "a", encoding="utf-8") as logger:
        start_time = datetime.now().isoformat()
        logger.write(f"🚀 Run started: {start_time}\n")
        print(f"🚀 Run started: {start_time}")

        for i, post in enumerate(posts):
            try:
                html_path = os.path.join(
                    "content", f"{post.get('slug', f'post_{i}')}.html"
                )
                if not os.path.exists(html_path):
                    logger.write(f"❌ Missing HTML: {html_path} → Skipping\n")
                    print(f"❌ Missing file: {html_path}")
                    continue

                content = load_post_content(html_path)
                publish_date = get_publish_date(i)
                push_post(post, content, publish_date, config, logger, results)
            except Exception as e:
                logger.write(
                    f"🔥 Fatal error posting: {post.get('slug', '[UNKNOWN]')}\n{e}\n"
                )
                print(f"🔥 Fatal error posting: {post.get('slug', '[UNKNOWN]')}")

        finish_time = datetime.now().isoformat()
        logger.write(f"✅ Run completed: {finish_time}\n")
        print(f"✅ Run completed: {finish_time}")
        print(
            f"✔️ Summary: Success={results['success']}, Skipped={results['skipped']}, Duplicates={results['duplicates']}, Errors={results['errors']}"
        )


if __name__ == "__main__":
    batch_schedule_posts()
