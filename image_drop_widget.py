"""
Module/Script Name: image_drop_widget.py

Description:
A PyQt6 widget that accepts drag-and-drop of image files and emits a list of file paths.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-04-16
Last Modified Date:
2025-04-17

Comments:
- v1.01 Ready to Zip and Ship: migrated to PyQt6 imports
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap


class ImageDropWidget(QWidget):
    """
    A widget that accepts drag-and-drop of image files and emits the file paths.
    """

    imagesDropped = pyqtSignal(list)  # Emits list of file paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        self.instruction = QLabel("Drag & drop images here", self)
        self.instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.instruction)
        self.listWidget = QListWidget(self)
        layout.addWidget(self.listWidget)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
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
            100,
            100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        item.setIcon(pixmap)
        item.setText(path.split("/")[-1])
        self.listWidget.addItem(item)
