"""
Module/Script Name: push_it_ui_mvp.py

Description:
PyQt6 GUI for the 'Push It Real Good' WordPress blog publishing tool.
Allows configuration input, save/load profiles, WordPress credential testing,
featured-image drag&amp;drop, scheduling, and live progress display.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date: 2025-04-15
Last Modified Date: 2025-04-17

Comments:
- v0.92 Ready to Zip and Ship: embedded ImageDropWidget, QProcess-run, and progress bar
"""

import sys
import os
import json
import requests
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QLabel,
    QHBoxLayout,
    QTimeEdit,
    QProgressBar,
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

        # --- Config selectors & inputs ---
        self.config_selector = QComboBox()
        self.config_selector.currentTextChanged.connect(self.load_config)
        self.load_button = QPushButton("🔄", clicked=self.load_config_list)

        self.config_name_input = QLineEdit()
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

        # --- Image drop widget ---
        self.image_drop = ImageDropWidget()
        self.image_drop.imagesDropped.connect(self.handle_images_dropped)

        # --- Buttons ---
        self.save_button = QPushButton("💾 Save Config", clicked=self.save_config)
        self.test_button = QPushButton(
            "🧪 Test Connection", clicked=self.test_connection
        )
        self.run_button = QPushButton("🚀 Run post_pusher.py", clicked=self.run_script)

        # --- Progress bar & process ---
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
        form.addRow("Category IDs (comma):", self.category_ids_input)
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

        # Status and Run
        layout.addWidget(self.status_label)
        layout.addWidget(self.run_button)

        # Progress bar
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def load_config_list(self):
        self.config_selector.clear()
        profiles = [
            f.removesuffix(".json")
            for f in os.listdir(CONFIG_DIR)
            if f.endswith(".json")
        ]
        self.config_selector.addItems(["-- Select --"] + profiles)

    def load_config(self, name: str) -> None:
        if name == "-- Select --":
            return
        path = os.path.join(CONFIG_DIR, name + ".json")
        if os.path.isfile(path):
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
            self.schedule_time_input.setTime(
                QTime.fromString(data.get("schedule_time", "14:00"), "HH:mm")
            )

    def save_config(self) -> None:
        name = self.config_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a config name.")
            return
        client_dir = os.path.join(CONTENT_ROOT, name)
        pre = os.path.join(client_dir, "pre-post")
        posted = os.path.join(client_dir, "posted")
        os.makedirs(pre, exist_ok=True)
        os.makedirs(posted, exist_ok=True)

        cfg = {
            "wp_url": self.wp_url_input.text(),
            "username": self.username_input.text(),
            "app_password": self.password_input.text(),
            "category_ids": [
                int(cid)
                for cid in self.category_ids_input.text().split(",")
                if cid.isdigit()
            ],
            "featured_image_url": self.featured_image_input.text(),
            "content_dir": client_dir,
            "post_status": self.status_selector.currentText(),
            "schedule_day": self.schedule_day_selector.currentText(),
            "schedule_time": self.schedule_time_input.time().toString("HH:mm"),
        }
        with open(os.path.join(CONFIG_DIR, name + ".json"), "w") as f:
            json.dump(cfg, f, indent=2)
        self.load_config_list()
        QMessageBox.information(self, "Saved", f"Configuration '{name}' saved.")

    def test_connection(self) -> None:
        try:
            url = f"{self.wp_url_input.text().rstrip('/')}/wp-json/wp/v2/users/me"
            resp = requests.get(
                url, auth=(self.username_input.text(), self.password_input.text())
            )
            if resp.status_code == 200:
                self.status_label.setText(
                    "✅ Connected: " + resp.json().get("name", "OK")
                )
            else:
                self.status_label.setText(f"❌ Failed: {resp.status_code}")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")

    def toggle_schedule_fields(self, text: str) -> None:
        enable = text == "schedule"
        self.schedule_day_selector.setEnabled(enable)
        self.schedule_time_input.setEnabled(enable)

    def handle_images_dropped(self, paths: list[str]) -> None:
        if paths:
            self.featured_image_input.setText(paths[0])

    def run_script(self) -> None:
        profile = self.config_selector.currentText()
        if profile == "-- Select --":
            QMessageBox.warning(self, "No Profile", "Please select a profile first.")
            return
        cfg_path = os.path.join(CONFIG_DIR, profile + ".json")
        self.progress_bar.setRange(0, 0)  # busy indicator
        self.run_button.setEnabled(False)
        self.process.start(sys.executable, ["post_pusher.py", "--config", cfg_path])

    def handle_stdout(self) -> None:
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8")
        print(data, end="")  # TODO: hook into a UI log view

    def handle_stderr(self) -> None:
        data = bytes(self.process.readAllStandardError()).decode("utf-8")
        print(data, end="")

    def process_finished(
        self, exit_code: int, exit_status: QProcess.ExitStatus
    ) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.run_button.setEnabled(True)
        QMessageBox.information(
            self, "Done", f"Process finished with code {exit_code}."
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PushItUI()
    window.show()
    sys.exit(app.exec())
