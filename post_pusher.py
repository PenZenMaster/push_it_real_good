"""
Module/Script Name: post_pusher.py

Description:
Pushes formatted HTML blog content to a WordPress site using the REST API. Reads config from JSON and posts from local content directory.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-04-13

Last Modified Date:
2025-04-13

Comments:
- Version 1.00 β — Initial setup for automated blog post publishing to WordPress via REST API
"""

import os
import json
import requests
from requests.auth import HTTPBasicAuth


# Load configuration
def load_config(config_path="config.json"):
    with open(config_path, "r") as file:
        return json.load(file)


# Load post content
def load_post_content(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


# Push post to WordPress

import mimetypes


def upload_featured_image(image_url, config):
    image_name = image_url.split("/")[-1]
    image_data = requests.get(image_url).content
    mime_type, _ = mimetypes.guess_type(image_url)

    if not mime_type:
        mime_type = "image/jpeg"  # Fallback just in case

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
        print(f"✅ Image uploaded successfully. Media ID: {media_id}")
        return media_id
    else:
        print(f"❌ Failed to upload image. Status Code: {response.status_code}")
        print(response.json())
        return None


def push_post(title, content, slug, status="draft"):
    config = load_config()
    url = f"{config['wp_url']}/wp-json/wp/v2/posts"
    auth = HTTPBasicAuth(config["username"], config["app_password"])

    featured_image_id = upload_featured_image(config["featured_image_url"], config)
    payload = {
        "featured_media": featured_image_id,
        "title": title,
        "content": content,
        "status": status,
        "slug": slug,
        "categories": config.get("category_ids", []),
    }

    response = requests.post(url, auth=auth, json=payload)
    if response.status_code == 201:
        print(f"✅ Success! Post '{title}' created as {status}.")
    else:
        print(f"❌ Failed to create post. Status Code: {response.status_code}")
        print(response.json())


if __name__ == "__main__":
    # Example usage
    title = "Best Online Tools for Comparing Mortgage Rates in 2025"
    slug = "best-online-mortgage-rate-tools-2025"
    html_file = os.path.join("content", "rate-comparison.html")
    content = load_post_content(html_file)
    push_post(title, content, slug)
