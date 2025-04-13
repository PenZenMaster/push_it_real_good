# Push It Real Good 🕺📤

Automate WordPress blog publishing with Python and REST API.

## 🚀 What It Does
- Reads blog HTML from `/content/`
- Uploads a featured image from a remote URL
- Publishes the post to WordPress via REST API
- Supports category assignment and draft/publish toggle

## 🧰 Requirements
- Python 3.8+
- WordPress site with Application Passwords enabled
- `requests` library (`pip install requests`)

## 🔧 Setup

1. Clone or copy this repo.
2. Add your WordPress credentials to `config.json`:
```json
{
  "wp_url": "https://your-wordpress-site.com",
  "username": "your-username",
  "app_password": "your-app-password",
  "category_ids": [3],
  "featured_image_url": "https://your-site.com/path-to-image.jpg"
}
```

3. Drop your HTML content into `/content/` and name the file something like `your-post.html`.

## 🚦 Usage
Run the script to post a blog:

```bash
python post_pusher.py
```

## 📁 Project Structure
```
push_it_real_good/
├── post_pusher.py         # Main Python script
├── config.json            # Credentials & settings (excluded by .gitignore)
├── content/               # HTML blog post files
│   └── rate-comparison.html
├── .gitignore             # Keeps sensitive and cluttery files out of Git
└── README.md              # This file right here
```

## 🛡️ Security
- Never commit `config.json` to a public repo.
- Use an application password (not your WP login password).
- Rotate app passwords if compromised.

---

Made with code, coffee, and just a lil' funk by Skippy the Magnificent & Big G.
