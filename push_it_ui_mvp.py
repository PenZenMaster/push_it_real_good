"""
Module/Script Name: push_it_ui_mvp.py

Description:
PyQt6 GUI for the 'Push It Real Good' WordPress blog publishing tool.
Allows configuration input, save/load profiles, WordPress credential testing,
featured-image drag&drop, category management, scheduling, and live progress display.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date: 2025-04-15
Last Modified Date: 2025-04-18

Comments:
- v0.94 Ready to Zip and Ship: improved category dropdown readability
"""
import sys
import os
import json
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QLabel, QHBoxLayout,
    QTimeEdit, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import QTime, QProcess
from image_drop_widget import ImageDropWidget

CONFIG_DIR = "configs"
CONTENT_ROOT = "content"
for d in (CONFIG_DIR, CONTENT_ROOT):
    os.makedirs(d, exist_ok=True)

class PushItUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Push It Real Good 🕺📤")
        self.setMinimumWidth(600)

        # Config selector
        self.config_selector = QComboBox()
        self.config_selector.currentTextChanged.connect(self.load_config)
        self.load_button = QPushButton("🔄", clicked=self.load_config_list)

        # Inputs
        self.config_name_input = QLineEdit()
        self.wp_url_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()

        # Category management
        self.category_ids_input = QLineEdit()
        self.fetch_button = QPushButton("Fetch Categories", clicked=self.fetch_categories)
        self.category_selector = QComboBox()
        # Make combo expand to fit full category names
        self.category_selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.category_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.category_selector.currentIndexChanged.connect(self.select_category)
        self.new_category_input = QLineEdit()
        self.add_category_button = QPushButton("Add Category", clicked=self.add_category)

        # Featured image & content
        self.featured_image_input = QLineEdit()
        self.content_folder_input = QLineEdit()

        # Post scheduling
        self.status_selector = QComboBox()
        self.status_selector.addItems(["draft", "publish", "schedule"])
        self.status_selector.currentTextChanged.connect(self.toggle_schedule_fields)
        self.schedule_day_selector = QComboBox()
        self.schedule_day_selector.addItems([
            "Monday","Tuesday","Wednesday","Thursday",
            "Friday","Saturday","Sunday",
        ])
        self.schedule_time_input = QTimeEdit(QTime(14, 0))
        self.schedule_day_selector.setEnabled(False)
        self.schedule_time_input.setEnabled(False)

        self.status_label = QLabel("Status: Not Connected")

        # Image drop widget
        self.image_drop = ImageDropWidget()
        self.image_drop.imagesDropped.connect(self.handle_images_dropped)

        # Action buttons
        self.save_button = QPushButton("💾 Save Config", clicked=self.save_config)
        self.test_button = QPushButton("🧪 Test Connection", clicked=self.test_connection)
        self.run_button = QPushButton("🚀 Run post_pusher.py", clicked=self.run_script)

        # Progress bar & process
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        self.init_ui()
        self.load_config_list()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Config row
        cfg_row = QHBoxLayout()
        cfg_row.addWidget(self.config_selector)
        cfg_row.addWidget(self.load_button)
        form.addRow("Load Config:", cfg_row)
        form.addRow("Config Name:", self.config_name_input)
        form.addRow("WordPress URL:", self.wp_url_input)
        form.addRow("Username:", self.username_input)
        form.addRow("App Password:", self.password_input)

        # Category row
        cat_row = QHBoxLayout()
        cat_row.addWidget(self.category_ids_input)
        cat_row.addWidget(self.fetch_button)
        cat_row.addWidget(self.category_selector)
        form.addRow("Category IDs:", cat_row)

        # New category row
        new_cat_row = QHBoxLayout()
        new_cat_row.addWidget(self.new_category_input)
        new_cat_row.addWidget(self.add_category_button)
        form.addRow("New Category:", new_cat_row)

        # Rest of form
        form.addRow("Featured Image Path:", self.featured_image_input)
        form.addRow("Content Folder:", self.content_folder_input)
        form.addRow("Post Status:", self.status_selector)
        form.addRow("Schedule Day:", self.schedule_day_selector)
        form.addRow("Schedule Time:", self.schedule_time_input)
        layout.addLayout(form)

        # Image drop area
        layout.addWidget(QLabel("Drag & drop featured image:"))
        layout.addWidget(self.image_drop)

        # Save/Test buttons
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.save_button)
        btn_row.addWidget(self.test_button)
        layout.addLayout(btn_row)

        # Status & Run
        layout.addWidget(self.status_label)
        layout.addWidget(self.run_button)

        # Progress bar
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def load_config_list(self) -> None:
        self.config_selector.clear()
        profiles = [f.removesuffix('.json') for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
        self.config_selector.addItems(["-- Select --"] + profiles)

    def load_config(self, name: str) -> None:
        if name == "-- Select --":
            return
        path = os.path.join(CONFIG_DIR, f"{name}.json")
        if os.path.isfile(path):
            with open(path, 'r') as f:
                data = json.load(f)
            self.config_name_input.setText(name)
            self.wp_url_input.setText(data.get('wp_url', ''))
            self.username_input.setText(data.get('username', ''))
            self.password_input.setText(data.get('app_password', ''))
            self.category_ids_input.setText(
                ",".join(map(str, data.get('category_ids', [])))
            )
            self.featured_image_input.setText(data.get('featured_image_url', ''))
            self.content_folder_input.setText(data.get('content_dir', ''))
            self.status_selector.setCurrentText(data.get('post_status', 'draft'))
            self.schedule_day_selector.setCurrentText(data.get('schedule_day', 'Monday'))
            self.schedule_time_input.setTime(
                QTime.fromString(data.get('schedule_time', '14:00'), 'HH:mm')
            )

    def fetch_categories(self) -> None:
        """Fetch existing WP categories and populate the selector."""
        try:
            url = f"{self.wp_url_input.text().rstrip('/')}/wp-json/wp/v2/categories"
            resp = requests.get(
                url,
                auth=(self.username_input.text(), self.password_input.text())
            )
            resp.raise_for_status()
            cats = resp.json()
            self.category_selector.clear()
            for cat in cats:
                self.category_selector.addItem(f"{cat['name']} ({cat['id']})", cat['id'])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch categories: {e}")

    def select_category(self, index: int) -> None:
        """Add selected category ID to the ID input field."""
        if index < 0:
            return
        cat_id = self.category_selector.itemData(index)
        existing = {cid.strip() for cid in self.category_ids_input.text().split(',') if cid.strip()}
        if str(cat_id) not in existing:
            existing.add(str(cat_id))
            self.category_ids_input.setText(\
