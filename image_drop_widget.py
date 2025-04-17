# image_drop_widget.py
"""
Module/Script Name: image_drop_widget.py

Description:
A PyQt5 widget that accepts drag‑and‑drop of image files and emits a list of file paths.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-04-16

Last Modified Date:
2025-04-16

Comments:
- v1.00 Ready to Zip and Ship
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap


class ImageDropWidget(QWidget):
    imagesDropped = pyqtSignal(list)  # emits list of file paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        self.instruction = QLabel("Drag & drop images here", self)
        self.instruction.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.instruction)
        self.listWidget = QListWidget(self)
        layout.addWidget(self.listWidget)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        image_paths = []
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                image_paths.append(path)
                self._addThumbnail(path)
        if image_paths:
            self.imagesDropped.emit(image_paths)

    def _addThumbnail(self, path):
        item = QListWidgetItem()
        pixmap = QPixmap(path).scaled(
            100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        item.setIcon(pixmap)
        item.setText(path.split("/")[-1])
        self.listWidget.addItem(item)
