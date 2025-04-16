"""
Module/Script Name: push_it_ui_mvp.py

Description:
Graphical user interface (GUI) for the 'Push It Real Good' WordPress blog publishing tool.
Allows configuration input, save/load profiles, WordPress credential testing, and scheduling posts.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date: 2025-04-15
Last Modified Date: 2025-04-15

Comments:
- v0.91 Added automatic client folder + pre-post/posted subdir creation on config save
"""

import sys
import json
import os
import requests
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QComboBox,
    QMessageBox,
    QLabel,
    QHBoxLayout,
    QGroupBox,
    QTimeEdit,
    QSpinBox,
)
from PyQt6.QtCore import QTime

CONFIG_DIR = "configs"
CONTENT_ROOT = "content"
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(CONTENT_ROOT, exist_ok=True)


class PushItUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Push It Real Good 🕺📤")
        self.setMinimumWidth(500)

        self.config_name_input = QLineEdit()
        self.config_selector = QComboBox()
        self.config_selector.currentTextChanged.connect(self.load_config)

        self.wp_url_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.category_ids_input = QLineEdit()
        self.featured_image_input = QLineEdit()
        self.content_folder_input = QLineEdit()

        self.status_selector = QComboBox()
        self.status_selector.addItems(["draft", "publish", "schedule"])
        self.status_selector.currentTextChanged.connect(self.toggle_schedule_fields)

        self.schedule_day_selector = QComboBox()
        self.schedule_day_selector.addItems(
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )
        self.schedule_time_input = QTimeEdit(QTime(14, 0))

        self.schedule_day_selector.setEnabled(False)
        self.schedule_time_input.setEnabled(False)

        self.status_label = QLabel("Status: Not Connected")

        self.init_ui()
        self.load_config_list()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        config_layout = QHBoxLayout()
        config_layout.addWidget(self.config_selector)
        config_layout.addWidget(QPushButton("🔄", clicked=self.load_config_list))
        form.addRow("Load Config:", config_layout)

        form.addRow("Config Name:", self.config_name_input)
        form.addRow("WordPress URL:", self.wp_url_input)
        form.addRow("Username:", self.username_input)
        form.addRow("App Password:", self.password_input)
        form.addRow("Category IDs (comma):", self.category_ids_input)
        form.addRow("Featured Image URL:", self.featured_image_input)
        form.addRow("Content Folder:", self.content_folder_input)

        form.addRow("Post Status:", self.status_selector)
        form.addRow("Schedule Day:", self.schedule_day_selector)
        form.addRow("Schedule Time:", self.schedule_time_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("💾 Save Config", clicked=self.save_config))
        btn_layout.addWidget(
            QPushButton("🧪 Test Connection", clicked=self.test_connection)
        )
        layout.addLayout(btn_layout)

        layout.addWidget(self.status_label)
        layout.addWidget(QPushButton("🚀 Run post_pusher.py", clicked=self.run_script))

        self.setLayout(layout)

    def load_config_list(self):
        self.config_selector.clear()
        configs = [
            f.removesuffix(".json")
            for f in os.listdir(CONFIG_DIR)
            if f.endswith(".json")
        ]
        self.config_selector.addItems(["-- Select --"] + configs)

    def load_config(self, name):
        if name == "-- Select --":
            return
        path = os.path.join(CONFIG_DIR, name + ".json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            self.config_name_input.setText(name)
            self.wp_url_input.setText(data.get("wp_url", ""))
            self.username_input.setText(data.get("username", ""))
            self.password_input.setText(data.get("app_password", ""))
            self.category_ids_input.setText(
                ",".join(map(str, data.get("category_ids", [])))
            )
            self.featured_image_input.setText(data.get("featured_image_url", ""))
            self.content_folder_input.setText(data.get("content_dir", ""))
            self.status_selector.setCurrentText(data.get("post_status", "draft"))
            self.schedule_day_selector.setCurrentText(
                data.get("schedule_day", "Monday")
            )
            t = data.get("schedule_time", "14:00")
            self.schedule_time_input.setTime(QTime.fromString(t, "HH:mm"))

    def save_config(self):
        name = self.config_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a config name.")
            return

        client_folder = os.path.join(CONTENT_ROOT, name)
        pre_post = os.path.join(client_folder, "pre-post")
        posted = os.path.join(client_folder, "posted")

        os.makedirs(pre_post, exist_ok=True)
        os.makedirs(posted, exist_ok=True)

        data = {
            "wp_url": self.wp_url_input.text(),
            "username": self.username_input.text(),
            "app_password": self.password_input.text(),
            "category_ids": [
                int(cid.strip())
                for cid in self.category_ids_input.text().split(",")
                if cid.strip().isdigit()
            ],
            "featured_image_url": self.featured_image_input.text(),
            "content_dir": client_folder,
            "post_status": self.status_selector.currentText(),
            "schedule_day": self.schedule_day_selector.currentText(),
            "schedule_time": self.schedule_time_input.time().toString("HH:mm"),
        }

        with open(os.path.join(CONFIG_DIR, name + ".json"), "w") as f:
            json.dump(data, f, indent=2)
        self.load_config_list()
        QMessageBox.information(self, "Saved", f"Configuration '{name}' saved.")

    def test_connection(self):
        try:
            url = f"{self.wp_url_input.text().rstrip('/')}/wp-json/wp/v2/users/me"
            response = requests.get(
                url, auth=(self.username_input.text(), self.password_input.text())
            )
            if response.status_code == 200:
                self.status_label.setText(
                    "✅ Connected: " + response.json().get("name", "OK")
                )
            else:
                self.status_label.setText(
                    f"❌ Failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")

    def toggle_schedule_fields(self, value):
        enable = value == "schedule"
        self.schedule_day_selector.setEnabled(enable)
        self.schedule_time_input.setEnabled(enable)

    def run_script(self):
        QMessageBox.information(
            self,
            "Run Script",
            "This would launch post_pusher.py with the selected config.",
        )
        # Integration hook here: call your post_pusher.py and pass in config path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PushItUI()
    window.show()
    sys.exit(app.exec())
