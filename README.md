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

# Push It Real Good UI

A PyQt-powered graphical interface for managing WordPress blog publishing tasks with speed, accuracy, and style.

---

## 💾 Requirements

- Python 3.9+
- PyQt6
- requests
- beautifulsoup4

---

## 📦 Setup Instructions

### 1. Clone the Repo
```bash
git clone https://yourrepo.url/push_it_real_good.git
cd push_it_real_good
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install pyqt6 requests beautifulsoup4
```

---

## 🚀 How to Run the UI
```bash
python push_it_ui_mvp.py
```

---

## 📂 Project Structure
```
configs/                     # Saved UI configurations (.json)
content/
├── ClientName/
│   ├── pre-post/            # Drop ready-to-publish HTML blogs here
│   ├── posted/              # Published posts auto-moved here
│   └── posts.json           # Metadata for each blog
post_pusher.py               # Core publishing script
push_it_ui_mvp.py            # This UI
```

---

## ✅ Features Implemented
- Save/recall named configuration profiles
- Auto-generate directory structure for each client
- Supports publish, draft, and scheduled post modes
- WordPress credential test
- Supports featured images from posts.json or config fallback

---

## 🔮 Next Session Tasks
1. Drag & drop blog upload to `pre-post/`
2. Drag & drop image upload preview + URL insertion
3. Launch publishing from UI
4. Visual progress log / progress bar (text + pizzazz)
5. Optional: Integration with Skippy Hemingway AI post generator

---

## 🧠 Powered By
- Skippy the Magnificent
- That filthy monkey Big G


