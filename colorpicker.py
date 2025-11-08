import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QColorDialog
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QBrush, QFont
from fractions import Fraction
import webcolors
import os
import json


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal(QPoint)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(event.pos())


class EllipseLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self.color = None

    def setColor(self, color):
        self.color = color
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.color is None:
            brush_color = QColor(255, 255, 255)
        else:
            color_r, color_g, color_b = self.color
            brush_color = QColor(color_r, color_g, color_b)

        brush = QBrush(brush_color, Qt.SolidPattern)
        painter.setBrush(brush)

        pen_color = QColor(255, 255, 255)
        painter.setPen(pen_color)

        rect = self.contentsRect()
        diameter = 100
        x = rect.center().x() - diameter // 2
        y = rect.center().y() - diameter // 2

        painter.drawEllipse(x, y, diameter, diameter)


def get_color_name(rgb_tuple):
    try:
        color_name = webcolors.rgb_to_name(rgb_tuple)
        return color_name
    except ValueError:
        #If no exact match is found, find the closest color
        try:
            closest_name = webcolors.rgb_to_name(rgb_tuple, spec='html4')
            return closest_name
        except ValueError as e:
            print(f"Error: {e}")
            return None


class Ui_colorPicker(object):
    color_list = {}
    image = None
    chosen_color = None

    def save_colors(self, parent_widget):
        data = {}
        colors = np.array(
            [[self.color_list[x][0], self.color_list[x][1], self.color_list[x][2]] for x in self.color_list])
        target_color = np.array([self.chosen_color[0], self.chosen_color[1], self.chosen_color[2]])

        coefficients, residuals, _, _ = np.linalg.lstsq(colors.T, target_color, rcond=None)

        output_data = []
        col_id = 0
        for x in self.color_list:
            col = self.color_list[x]
            col_name = get_color_name(col)
            if col_name is None:
                continue
            col_ratio = round(coefficients[col_id], 1)
            col_id += 1
            if col_ratio == 0:
                continue
            col_ratio_fraction = Fraction(col_ratio).limit_denominator()
            output_data.append(f'{col_name}: {col_ratio_fraction} ({col_ratio})')

        self.txtStatus.setText('\n'.join(output_data))
        """Saves the current colors and their ratios to a JSON file."""

        script_dir = os.path.dirname(__file__)

        save_file_path, _ = QFileDialog.getSaveFileName(parent_widget,
                                                        "Save Color Data",
                                                        script_dir,
                                                        "JSON Files (*.json)")

        if save_file_path:
            for index, color in enumerate(self.color_list):
                rgb_color = self.color_list[color]
                color_name = get_color_name(rgb_color)
                try:
                    ratio = coefficients[index]
                    ratio_fraction = Fraction(ratio).limit_denominator()
                    data[color_name] = {
                        "rgb": rgb_color,
                        "ratio": str(ratio_fraction) 
                    }
                except NameError:
                    pass

            try:
                with open(save_file_path, 'w') as outfile:
                    json.dump(data, outfile, indent=4) 
                QMessageBox.information(parent_widget, "Save Successful", f"Color data saved to {save_file_path}")

            except (IOError, json.JSONDecodeError) as e:
                QMessageBox.warning(parent_widget, "Save Error", f"Failed to save color data: {e}")
        else:
            QMessageBox.information(None, "Save Canceled", "No file selected.")

    def setupUi(self, colorPicker):
        colorPicker.setObjectName("colorPicker")
        colorPicker.setFixedSize(1024, 768)
        colorPicker.setStyleSheet("background-color: #2D2D2D; color: #FFFFFF; font-size: 16px;")

        self.btnSave = QtWidgets.QPushButton(colorPicker)
        self.btnSave.setGeometry(QtCore.QRect(900, 20, 100, 25))
        self.btnSave.setStyleSheet("background-color: #4D4D4D; color: #FFFFFF; font-size: 16px;")
        self.btnSave.setObjectName("btnSave")
        self.btnSave.setText("Save Colors")
        self.btnSave.clicked.connect(lambda: self.save_colors(colorPicker))

        self.btnOpenImage = QtWidgets.QPushButton(colorPicker)
        self.btnOpenImage.setGeometry(QtCore.QRect(20, 20, 120, 25))
        self.btnOpenImage.setStyleSheet("background-color: #4D4D4D; color: #FFFFFF; font-size: 16px;")
        self.btnOpenImage.setObjectName("btnOpenImage")

        self.txtImageFilePath = QtWidgets.QLineEdit(colorPicker)
        self.txtImageFilePath.setGeometry(QtCore.QRect(150, 20, 600, 25))
        self.txtImageFilePath.setObjectName("txtImageFilePath")

        self.lblImage = ClickableLabel(colorPicker)
        self.lblImage.setScaledContents(True)
        self.lblImage.setGeometry(QtCore.QRect(30, 70, 640, 480))
        self.lblImage.setAlignment(Qt.AlignLeft)
        self.lblImage.setText("")
        self.lblImage.setObjectName("lblImage")

        self.labelColorPalette = QtWidgets.QLabel(colorPicker)
        self.labelColorPalette.setGeometry(QtCore.QRect(700, 50, 300, 25))
        self.labelColorPalette.setAlignment(Qt.AlignCenter)
        self.labelColorPalette.setObjectName("labelColorPalette")
        self.labelColorPalette.setText("Color Palette")

        font = self.labelColorPalette.font()
        font.setPointSize(18)
        self.labelColorPalette.setFont(font)

        self.grpColorBox = QtWidgets.QGroupBox(colorPicker)
        self.grpColorBox.setGeometry(QtCore.QRect(700, 70, 300, 460))
        self.grpColorBox.setAlignment(Qt.AlignCenter)
        self.grpColorBox.setFlat(False)
        self.grpColorBox.setObjectName("grpColorBox")

        self.btnColors = []
        for btn_row in range(5):
            for btn_col in range(3):
                btnColor = QtWidgets.QPushButton(self.grpColorBox)
                x_pos = 50 + 80 * btn_col
                y_pos = 50 + 80 * btn_row
                btnColor.setGeometry(QtCore.QRect(x_pos, y_pos, 50, 50))
                btnColor.setStyleSheet("background-color: none;")
                btnColor.released.connect(
                    lambda button_index=3 * btn_row + btn_col: self.change_color_in_btn_list(button_index))
                self.btnColors.append(btnColor)

        self.btnColors[0].setStyleSheet("background-color: #ff0000")
        self.btnColors[1].setStyleSheet("background-color: #00ff00")
        self.btnColors[2].setStyleSheet("background-color: #0000ff")

        self.color_list[0] = (255, 0, 0)
        self.color_list[1] = (0, 255, 0)
        self.color_list[2] = (0, 0, 255)

        self.grpGetColor = QtWidgets.QGroupBox(colorPicker)
        self.grpGetColor.setGeometry(QtCore.QRect(480, 579, 520, 160))
        self.grpGetColor.setAlignment(Qt.AlignCenter)
        self.grpGetColor.setObjectName("grpGetColor")

        self.color_label = EllipseLabel(self.grpGetColor)
        self.color_label.setGeometry(QtCore.QRect(60, 30, 120, 120))
        self.color_label.setText("")

        self.btn_get_color = QtWidgets.QPushButton(self.grpGetColor)
        self.btn_get_color.setGeometry(QtCore.QRect(250, 50, 150, 50))
        self.btn_get_color.setStyleSheet("background-color: #4D4D4D; color: #FFFFFF; font-size: 16px;")
        self.btn_get_color.setText("Get Color")
        self.btn_get_color.setObjectName("btn_get_color")

        self.labelColorRatios = QtWidgets.QLabel(colorPicker)
        self.labelColorRatios.setGeometry(QtCore.QRect(30, 570, 340, 40))
        self.labelColorRatios.setObjectName("labelColorRatios")
        self.labelColorRatios.setText("Ratios of colors to mix")
        self.labelColorRatios.setAlignment(Qt.AlignLeft)

        font = self.labelColorRatios.font()
        font.setPointSize(32) 
        self.labelColorRatios.setFont(font)

        self.txtStatus = QtWidgets.QTextEdit(colorPicker)
        self.txtStatus.setGeometry(QtCore.QRect(30, 590, 430, 170))
        self.txtStatus.setAutoFillBackground(False)
        self.txtStatus.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.txtStatus.setFrameShadow(QtWidgets.QFrame.Plain)
        self.txtStatus.setObjectName("txtStatus")

        self.retranslateUi(colorPicker)
        QtCore.QMetaObject.connectSlotsByName(colorPicker)

        self.btnOpenImage.released.connect(self.open_image)
        self.lblImage.clicked.connect(self.on_omage_clicked)
        self.btn_get_color.released.connect(self.get_color)

    def retranslateUi(self, colorPicker):
        _translate = QtCore.QCoreApplication.translate
        colorPicker.setWindowTitle(_translate("colorPicker", "color picker"))
        self.btnOpenImage.setText(_translate("colorPicker", "Open Image"))
        self.grpColorBox.setTitle(_translate("colorPicker", " click button to add/change color "))
        self.grpGetColor.setTitle(_translate("colorPicker", "  Get the color"))

    def show_chosen_color(self, color):
        self.color_label.setColor(color)

    def on_omage_clicked(self, pos):
        if self.image:
            image_width = self.image.width()
            image_height = self.image.height()

            label_width = self.lblImage.width()
            label_height = self.lblImage.height()

            mapped_pos = QPoint(
                int(pos.x() * image_width / label_width),
                int(pos.y() * image_height / label_height)
            )

            if 0 <= mapped_pos.x() < image_width and 0 <= mapped_pos.y() < image_height:
                pixel_color = QColor(self.image.pixel(mapped_pos))
                rgb_color = (pixel_color.red(), pixel_color.green(), pixel_color.blue())
                self.chosen_color = rgb_color
                self.show_chosen_color(rgb_color)
                self.txtStatus.setText(f"Position ({mapped_pos.x()}, {mapped_pos.y()})\nColor: RGB{rgb_color}")
            else:
                self.txtStatus.setText("Clicked outside of the image boundaries")

    def open_image(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(None, 'QFileDialog.getOpenFileName()', '',
                                                  'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if fileName:
            image = QImage(fileName)
            if image.isNull():
                QMessageBox.information(self, "Color Picker", "Cannot load %s." % fileName)
                return

            target_width = 640
            target_height = 480

            resized_image = image.scaled(target_width, target_height,
                                         aspectRatioMode=Qt.KeepAspectRatio)

            self.lblImage.setPixmap(QPixmap.fromImage(resized_image))
            self.image = resized_image
            self.txtImageFilePath.setText(fileName)

    def change_color_in_btn_list(self, btn_index):
        color_default = QColor(0, 0, 0) 
        color = QColorDialog.getColor(initial=color_default)
        if color.isValid():
            try:
                self.color_list[btn_index] = (color.red(), color.green(), color.blue())
                self.btnColors[btn_index].setStyleSheet("background-color: {}".format(color.name()))
            except Exception as err:
                print(err)

    def mousePressEvent(self, event):
        if self.image:
            pos = event.pos()
            if self.image.rect().contains(pos):
                pixel_color = QColor(self.image.pixel(pos))
                rgb_color = pixel_color.red(), pixel_color.green(), pixel_color.blue()
                print(f"RGB color at position ({pos.x()}, {pos.y()}): {rgb_color}")

    def get_color(self):
        colors = np.array(
            [[self.color_list[x][0], self.color_list[x][1], self.color_list[x][2]] for x in self.color_list])
        target_color = np.array([self.chosen_color[0], self.chosen_color[1], self.chosen_color[2]])

        coefficients, residuals, _, _ = np.linalg.lstsq(colors.T, target_color, rcond=None)

        output_data = []
        col_id = 0
        for x in self.color_list:
            col = self.color_list[x]
            col_name = get_color_name(col)
            if col_name is None:
                continue
            col_ratio = round(coefficients[col_id], 1)
            col_id += 1
            if col_ratio == 0:
                continue
            col_ratio_fraction = Fraction(col_ratio).limit_denominator()
            output_data.append(f'{col_name}: {col_ratio_fraction} ({col_ratio}) {col_ratio * 10} ml')

        self.txtStatus.setText('\n'.join(output_data))
