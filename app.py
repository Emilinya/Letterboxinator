import os
import sys
import time
from dataclasses import dataclass

import PySide6.QtGui as qgui
import PySide6.QtCore as qcore
import PySide6.QtWidgets as qwidgets

from letterbox import add_letterbox


@dataclass
class ComboBoxData:
    items: list[tuple[str, str]]

    def apply_to(self, combobox: qwidgets.QComboBox):
        for i, (item, tooltip) in enumerate(self.items):
            combobox.addItem(item)
            combobox.setItemData(i, tooltip, qgui.Qt.ItemDataRole.ToolTipRole)


class MainWidget(qwidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Letterboxinator")
        self.setWindowIcon(qgui.QIcon("media/icon.png"))
        self.resize(680, 480)
        self.setAcceptDrops(True)
        self.setStyleSheet("font-size: 24px;")

        title = qwidgets.QLabel("Drag and drop an image to add letterbox")
        title.setStyleSheet("font-size: 34px; font-weight: bold;")

        mode_data = ComboBoxData(
            [
                ("Blur", "Fill background with a blured copy of the image"),
                ("Color", "Fill background with a color"),
                ("Extend", "Fill background by extending the edge pixels"),
            ]
        )
        mode_label = qwidgets.QLabel("Letterbox mode:")
        self.mode_select = qwidgets.QComboBox()
        mode_data.apply_to(self.mode_select)
        self.mode_select.currentTextChanged.connect(self.mode_changed)
        mode_layout = qwidgets.QHBoxLayout()
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_select)
        mode_layout.addStretch(0)

        self.ratio = (16.0, 9.0)
        ratio_label = qwidgets.QLabel("Goal ratio:")
        self.ratio_input = qwidgets.QLineEdit(
            f"{self.ratio[0]:.3g}x{self.ratio[1]:.3g}"
        )
        self.ratio_input.textChanged.connect(self.validate_ratio)
        ratio_layout = qwidgets.QHBoxLayout()
        ratio_layout.addWidget(ratio_label)
        ratio_layout.addWidget(self.ratio_input)
        ratio_layout.addStretch(0)
        ratio_frame = qwidgets.QFrame()
        ratio_layout.setContentsMargins(0, 0, 0, 0)
        ratio_frame.setLayout(ratio_layout)
        ratio_frame.setToolTip(
            "The ratio you want the letterboxed image to have.\n"
            + "Must be axb or a:b, where a and b are floats"
        )

        self.radius = 70
        radius_label = qwidgets.QLabel("Blur radius:")
        self.radius_input = qwidgets.QLineEdit(f"{self.radius}")
        self.radius_input.textChanged.connect(self.validate_radius)
        radius_layout = qwidgets.QHBoxLayout()
        radius_layout.addWidget(radius_label)
        radius_layout.addWidget(self.radius_input)
        radius_layout.addStretch(0)
        self.radius_frame = qwidgets.QFrame()
        radius_layout.setContentsMargins(0, 0, 0, 0)
        self.radius_frame.setLayout(radius_layout)
        self.radius_frame.setToolTip(
            "The radius of the gaussian blur.\n"
            + "A larger radius results in a more blured image"
        )

        self.color = qgui.QColor.fromString("white")
        color_label = qwidgets.QLabel("Background color:")
        # Using a button for this is so hacky, sorry :(
        self.color_display = qwidgets.QPushButton("")
        self.color_display.setDisabled(True)
        self.color_display.setStyleSheet(
            f"background-color: {self.color.name()}; border: 2px solid black"
        )
        color_button = qwidgets.QPushButton("Select new color")
        color_button.clicked.connect(self.open_color_dialog)
        self.color_input = qwidgets.QColorDialog(self.color)
        self.color_input.colorSelected.connect(self.accept_color)
        color_layout = qwidgets.QHBoxLayout()
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_display)
        color_layout.addWidget(color_button)
        color_layout.addStretch(0)
        color_layout.setContentsMargins(0, 0, 0, 0)
        self.color_frame = qwidgets.QFrame()
        self.color_frame.setLayout(color_layout)

        self.output_text = qwidgets.QLabel("")
        self.output_text.setWordWrap(True)

        main_layout = qwidgets.QVBoxLayout(self)
        main_layout.addWidget(title)
        main_layout.addLayout(mode_layout)
        main_layout.addWidget(ratio_frame)
        main_layout.addWidget(self.radius_frame)
        main_layout.addWidget(self.color_frame)
        main_layout.addWidget(self.output_text)
        main_layout.addStretch(0)

        self.mode_changed(self.mode_select.currentText())

    def mode_changed(self, mode: str):
        if mode == "Blur":
            self.color_frame.hide()
            self.radius_frame.show()
        elif mode == "Color":
            self.color_frame.show()
            self.radius_frame.hide()
        elif mode == "Extend":
            self.color_frame.hide()
            self.radius_frame.hide()
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def validate_ratio(self, new_ratio: str):
        if "x" in new_ratio:
            values = new_ratio.split("x")
        elif ":" in new_ratio:
            values = new_ratio.split(":")
        else:
            values = []

        if len(values) == 2:
            try:
                self.ratio = (float(values[0]), float(values[1]))
                self.ratio_input.setStyleSheet("color: black;")
                return
            except ValueError:
                pass

        self.ratio_input.setStyleSheet("color: red;")

    def validate_radius(self, new_radius: str):
        try:
            self.radius = int(new_radius)
            self.radius_input.setStyleSheet("color: black;")
        except ValueError:
            self.radius_input.setStyleSheet("color: red;")

    def open_color_dialog(self):
        self.color_input.show()

    def accept_color(self, color: qgui.QColor):
        self.color = color
        self.color_display.setStyleSheet(
            f"background-color: {self.color.name()}; border: 2px solid black"
        )

    def dragEnterEvent(self, event: qgui.QDragEnterEvent):
        for url in [url.fileName() for url in event.mimeData().urls()]:
            # TODO: Support folders
            if os.path.isdir(url):
                event.ignore()
                return

            # Is this all the extentions I should support? Probably
            extention = os.path.splitext(url)[1]
            if extention.lower() not in (
                ".jpg",
                ".jpeg",
                ".png",
                ".j2k",
                ".jp2",
                ".jpx",
                ".webp",
            ):
                event.ignore()
                return

        event.accept()

    def dropEvent(self, event: qgui.QDropEvent):
        showed_error = False
        mode = self.mode_select.currentText()
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for i, filename in enumerate(files):
            showed_error = False
            basename = os.path.basename(filename)

            self.output_text.setText(f"Adding letterbox to {basename} ...")
            qcore.QCoreApplication.processEvents()

            try:
                color = (
                    self.color.red(),
                    self.color.green(),
                    self.color.blue(),
                    self.color.alpha(),
                )
                add_letterbox(filename, self.ratio, mode, self.radius, color)
            # pylint: disable=broad-exception-caught
            except Exception as err:
                error_type = str(type(err))[8:-2]
                self.output_text.setText(
                    f"Processing {basename} gave {error_type}: {err}"
                )
                qcore.QCoreApplication.processEvents()
                showed_error = True
                if i != len(files) - 1:
                    time.sleep(3)

        if not showed_error:
            self.output_text.setText("Done!")


if __name__ == "__main__":
    app = qwidgets.QApplication(sys.argv)

    ui = MainWidget()
    ui.show()

    sys.exit(app.exec())
