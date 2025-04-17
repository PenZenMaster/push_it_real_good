# Push It Real Good 🕺📤

Automate WordPress blog publishing with Python and the WordPress REST API.

## 🚀 What It Does
- Reads blog HTML from `content/<ProfileName>/pre-post/`
- Uploads a featured image from a local path or remote URL
- Publishes the post to WordPress via REST API
- Supports category assignment and draft/publish/schedule modes
- Moves published files into `posted/` for archival

## 🧰 Requirements
- Python 3.8+
- WordPress site with Application Passwords enabled
- `requests` library (`pip install requests`)

## 🔧 Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/PenZenMaster/push_it_real_good.git
   cd push_it_real_good
   ```

2. **Create a Python virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add publishing profiles**
   - All configuration profiles live in `configs/`.
   - Create a JSON file for each profile, e.g. `configs/default.json`:
     ```json
     {
       "wp_url": "https://your-wordpress-site.com",
       "username": "your-username",
       "app_password": "your-app-password",
       "category_ids": [3],
       "featured_image_url": "https://your-site.com/path-to-image.jpg",
       "content_dir": "content/ClientName",
       "post_status": "draft",
       "schedule_day": "Monday",
       "schedule_time": "14:00"
     }
     ```

5. **Prepare your content**
   - For CLI mode, drop your HTML files into the profile folder’s `pre-post/` directory, e.g.:
     ```
     content/ClientName/pre-post/your-post.html
     ```
   - For UI mode, the GUI will handle the move between `pre-post/` and `posted/` automatically.

## 🚦 CLI Usage

By default, runs the `default.json` profile:
```bash
python post_pusher.py --config configs/default.json
```

You can specify any profile:
```bash
python post_pusher.py --config configs/ClientName.json
```

## 📂 Project Structure
```
push_it_real_good/
├── configs/                # JSON profile configs (one per client)
│   ├── default.json
│   └── ClientName.json
├── content/                # Blog HTML files by profile
│   └── ClientName/
│       ├── pre-post/       # Ready-to-publish HTML here
│       └── posted/         # Published posts moved here
├── post_pusher.py          # Core publishing script
├── push_it_ui_mvp.py       # PyQt GUI for managing profiles & publishing
├── requirements.txt        # Pinned Python dependencies
└── README.md               # This file
```

---

# Push It Real Good UI

A PyQt6-powered graphical interface for managing WordPress blog publishing tasks with speed, accuracy, and style.

## 💾 UI Requirements
- Python 3.9+
- PyQt6
- requests
- beautifulsoup4

## 🚀 How to Run the UI
```bash
python push_it_ui_mvp.py
```

## ✅ UI Features Implemented
- Save/recall named configuration profiles
- Auto-create `pre-post/` and `posted/` directories for each profile
- Publish, draft, or schedule posts
- WordPress credential testing
- Drag & drop featured image selection (via ImageDropWidget)

## 🔮 Next Session Tasks
1. Drag & drop blog upload to `pre-post/`
2. Visual progress log / progress bar (text + animation)
3. Launch publishing from GUI
4. Optional: AI-assisted blog generation

---

© 2025 Skippy the Magnificent & Big G