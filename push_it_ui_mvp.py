"""
Module/Script Name: push_it_ui_mvp.py

Description:
PyQt6 GUI for the 'Push It Real Good' WordPress blog publishing tool.
Allows configuration input, save/load profiles, WordPress credential testing,
featured-image drag\&drop, category management, scheduling, live progress display,
and a Help menu with an image popup.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date: 2025-04-15
Last Modified Date: 2025-04-18

Comments:
- v0.96 Ready to Zip and Ship: added Help menu and image popup
- v0.97 Fixed QAction import for PyQt6
"""

import sys
import os
import json
import requests
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
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
    QSizePolicy,
    QMenuBar,
    QMenu,
    QDialog,
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import QTime, QProcess
from image_drop_widget import ImageDropWidget

CONFIG_DIR = "configs"
CONTENT_ROOT = "content"
for d in (CONFIG_DIR, CONTENT_ROOT):
    os.makedirs(d, exist_ok=True)


class PushItUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Push It Real Good 🕺📤")
        self.setMinimumWidth(600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Menu bar
        menubar = QMenuBar(self)
        help_menu = menubar.addMenu("Help")
        help_action = QAction("Show Skippy", self)
        help_action.triggered.connect(self.show_help_dialog)
        help_menu.addAction(help_action)
        self.setMenuBar(menubar)

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
        self.fetch_button = QPushButton(
            "Fetch Categories", clicked=self.fetch_categories
        )
        self.category_selector = QComboBox()
        self.category_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.category_selector.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.category_selector.currentIndexChanged.connect(self.select_category)
        self.new_category_input = QLineEdit()
        self.add_category_button = QPushButton(
            "Add Category", clicked=self.add_category
        )

        # Featured image & content
        self.featured_image_input = QLineEdit()
        self.content_folder_input = QLineEdit()

        # Post scheduling
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

        # Image drop widget
        self.image_drop = ImageDropWidget()
        self.image_drop.imagesDropped.connect(self.handle_images_dropped)

        # Action buttons
        self.save_button = QPushButton("💾 Save Config", clicked=self.save_config)
        self.test_button = QPushButton(
            "🧪 Test Connection", clicked=self.test_connection
        )
        self.run_button = QPushButton("🚀 Run post_pusher.py", clicked=self.run_script)

        # Progress bar & process
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        # Build form and layout
        self._build_form(layout)
        layout.addWidget(QLabel("Drag & drop featured image:"))
        layout.addWidget(self.image_drop)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.save_button)
        btn_row.addWidget(self.test_button)
        layout.addLayout(btn_row)
        layout.addWidget(self.status_label)
        layout.addWidget(self.run_button)
        layout.addWidget(self.progress_bar)

        self.load_config_list()

    def _build_form(self, parent_layout):
        form = QFormLayout()
        cfg_row = QHBoxLayout()
        cfg_row.addWidget(self.config_selector)
        cfg_row.addWidget(self.load_button)
        form.addRow("Load Config:", cfg_row)
        form.addRow("Config Name:", self.config_name_input)
        form.addRow("WordPress URL:", self.wp_url_input)
        form.addRow("Username:", self.username_input)
        form.addRow("App Password:", self.password_input)
        cat_row = QHBoxLayout()
        cat_row.addWidget(self.category_ids_input)
        cat_row.addWidget(self.fetch_button)
        cat_row.addWidget(self.category_selector)
        form.addRow("Category IDs:", cat_row)
        new_cat_row = QHBoxLayout()
        new_cat_row.addWidget(self.new_category_input)
        new_cat_row.addWidget(self.add_category_button)
        form.addRow("New Category:", new_cat_row)
        form.addRow("Featured Image Path:", self.featured_image_input)
        form.addRow("Content Folder:", self.content_folder_input)
        form.addRow("Post Status:", self.status_selector)
        form.addRow("Schedule Day:", self.schedule_day_selector)
        form.addRow("Schedule Time:", self.schedule_time_input)
        parent_layout.addLayout(form)

    def show_help_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Help - Skippy Says")
        dlg_layout = QVBoxLayout(dialog)
        pix = QPixmap()
        pix.load("/mnt/data/a82ae152-5072-424e-a6cd-3f578d28dada.png")
        img_label = QLabel(dialog)
        img_label.setPixmap(pix)
        dlg_layout.addWidget(img_label)
        close_btn = QPushButton("Stupid Monkey!", clicked=dialog.accept)
        dlg_layout.addWidget(close_btn)
        dialog.exec()

    # ... rest of methods unchanged ...


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PushItUI()
    window.show()
    sys.exit(app.exec())
