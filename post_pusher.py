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

posts = [
    {
        "slug": "fha-loan-plymouth-mi",
        "title": "How to Qualify for an FHA Loan in Plymouth, MI",
        "description": "Explore FHA loan benefits and qualification steps for Plymouth, MI homebuyers. Low down payments and flexible credit make FHA loans a top choice."
    },
    {
        "slug": "va-mortgage-ann-arbor-mi",
        "title": "Why VA Home Loans Are a Smart Choice in Ann Arbor, MI",
        "description": "Veterans and active-duty service members in Ann Arbor: Learn how VA loans offer zero down, no PMI, and better rates for your home purchase."
    },
    {
        "slug": "usda-mortgage-plymouth-mi",
        "title": "USDA Mortgage Loans in Plymouth, MI: Zero Down, Big Opportunity",
        "description": "Live in a rural area near Plymouth, MI? Discover how USDA mortgage loans let you buy with zero down and low interest rates."
    },
    {
        "slug": "adjustable-rate-mortgage-michigan",
        "title": "What You Need to Know About Adjustable Rate Mortgages in Michigan",
        "description": "Explore how adjustable-rate mortgages (ARMs) work in Michigan, their pros and cons, and if they're right for your financial plan."
    },
    {
        "slug": "first-time-home-buyer-michigan",
        "title": "First-Time Homebuyer Programs in Michigan: What You Need to Know",
        "description": "New to home buying in Michigan? Discover the best first-time buyer programs, grants, and loan options available right now."
    },
    {
        "slug": "refinance-mortgage-plymouth-mi",
        "title": "Refinancing Your Home in Plymouth, MI: Smart Moves in a Shifting Market",
        "description": "Thinking of refinancing in Plymouth, MI? Compare rates, explore your options, and decide if now is the right time to refinance your mortgage."
    },
    {
        "slug": "conventional-vs-fha-loans-michigan",
        "title": "Conventional vs FHA Loans in Michigan: Which One Wins?",
        "description": "Weighing FHA vs conventional in Michigan? This guide compares credit, down payment, and qualification differences to help you choose."
    },
    {
        "slug": "mortgage-pre-approval-plymouth-mi",
        "title": "Getting Pre-Approved for a Mortgage in Plymouth, MI: What to Expect",
        "description": "Learn how to get pre-approved for a mortgage in Plymouth, MI. Understand the documents, process, and how to increase your chances."
    }
]

def load_config(config_path='config.json'):
    with open(config_path, 'r') as file:
        return json.load(file)

def load_post_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def upload_featured_image(image_url, config, logger):
    try:
        image_name = image_url.split('/')[-1]
        image_data = requests.get(image_url).content
        mime_type, _ = mimetypes.guess_type(image_url)
        if not mime_type:
            mime_type = 'image/jpeg'

        media_url = f"{config['wp_url']}/wp-json/wp/v2/media"
        headers = {
            'Content-Disposition': f'attachment; filename={image_name}',
            'Content-Type': mime_type
        }

        response = requests.post(media_url, headers=headers, data=image_data,
                                 auth=HTTPBasicAuth(config['username'], config['app_password']))
        if response.status_code in [200, 201]:
            media_id = response.json().get('id')
            logger.write(f"✅ Uploaded {image_name} → Media ID: {media_id}\n")
            return media_id
        else:
            logger.write(f"❌ Failed to upload image: {image_name}\n{response.json()}\n")
            return None
    except Exception as e:
        logger.write(f"🔥 Exception uploading image: {image_url}\n{e}\n")
        return None

def post_exists(slug, config):
    url = f"{config['wp_url']}/wp-json/wp/v2/posts?slug={slug}"
    response = requests.get(url, auth=HTTPBasicAuth(config['username'], config['app_password']))
    return response.status_code == 200 and bool(response.json())

def get_publish_date(weeks_ahead=0):
    today = datetime.now()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0 and today.hour >= 8:
        days_until_monday = 7
    publish_date = today + timedelta(days=days_until_monday + (weeks_ahead * 7))
    return publish_date.replace(hour=8, minute=0, second=0, microsecond=0).isoformat()

def push_post(post, content, publish_date, config, logger):
    slug = post.get('slug')
    title = post.get('title')
    focus_keyword = post.get('focus_keyword')
    meta_description = post.get('rank_math_description')
    image_url = post.get('featured_image_url', config.get('featured_image_url'))

    missing_fields = [key for key in ['slug', 'title', 'focus_keyword', 'rank_math_description'] if key not in post]
    if missing_fields:
        logger.write(f"⚠️ Skipping post due to missing fields: {slug or '[UNKNOWN SLUG]'} → {missing_fields}\n")
        return

    if post_exists(slug, config):
        logger.write(f"⚠️ Skipping duplicate: {slug}\n")
        return

    media_id = upload_featured_image(image_url, config, logger)

    payload = {
        'title': title,
        'slug': slug,
        'content': content,
        'status': 'future',
        'date': publish_date,
        'categories': config.get('category_ids', []),
        'featured_media': media_id,
        'meta': {
            'rank_math_focus_keyword': focus_keyword,
            'rank_math_description': meta_description
        }
    }

    url = f"{config['wp_url']}/wp-json/wp/v2/posts"
    auth = HTTPBasicAuth(config['username'], config['app_password'])
    response = requests.post(url, auth=auth, json=payload)

    if response.status_code == 201:
        logger.write(f"✅ Scheduled: {title} → {publish_date}\n")
    else:
        logger.write(f"❌ Failed to schedule: {title}\n{response.json()}\n")

def batch_schedule_posts():
    config = load_config()
    with open('post_pusher.log', 'a', encoding='utf-8') as logger:
        logger.write(f"🚀 Run started: {datetime.now().isoformat()}\n")

        for i, post in enumerate(posts):
            try:
                html_path = os.path.join('content', f"{post.get('slug', f'post_{i}')}.html")
                if not os.path.exists(html_path):
                    logger.write(f"❌ Missing HTML: {html_path} → Skipping\n")
                    continue

                content = load_post_content(html_path)
                publish_date = get_publish_date(i)
                push_post(post, content, publish_date, config, logger)
            except Exception as e:
                logger.write(f"🔥 Fatal error posting: {post.get('slug', '[UNKNOWN]')}\n{e}\n")

        logger.write(f"✅ Run completed: {datetime.now().isoformat()}\n\n")

if __name__ == '__main__':
    batch_schedule_posts()
