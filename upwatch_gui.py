from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from threading import Thread
import upwatch
# import time


class UpwatchGui:
    def __init__(self, json_content):
        # JSON Dict with URL, Don't Bother Me Rate, Job Posts
        self.json_content = json_content

        # Calling the logic
        if self.json_content["Requests URL"] is not None:
            Thread(target=upwatch.job_post_scraper(self.json_content)).start()
            # TODO: If json_content["URL"] is None -> Run settings window

        # Main Application
        self.app = QtWidgets.QApplication([])
        self.app.setQuitOnLastWindowClosed(False)

        # Create the icon
        icon = QtGui.QIcon("uwlogo.png")  # TODO: Fix own logo

        # Create the tray
        self.tray = QtWidgets.QSystemTrayIcon()
        self.tray.setIcon(icon)
        self.tray.setVisible(True)

        self.actions = []

        # Create the menu
        self.menu = QtWidgets.QMenu()
        url_action = QtWidgets.QAction("Set URL")
        url_action.triggered.connect(self.set_url_window)
        self.actions.append(url_action)

        settings_action = QtWidgets.QAction("Settings")
        settings_action.triggered.connect(self.settings_window)
        self.actions.append(settings_action)

        about_action = QtWidgets.QAction("About")
        about_action.triggered.connect(self.about_window)
        self.actions.append(about_action)

        # Add a Quit option to the menu.
        # TODO: Call write_to_json before closing the program – Remove writing from job_post_scraper
        quit_action = QtWidgets.QAction("Quit")
        quit_action.triggered.connect(self.close_program)
        self.actions.append(quit_action)

        # Add buttons to menubar menu
        for action in self.actions:
            self.menu.addAction(action)

        # Add the menu to the tray
        self.tray.setContextMenu(self.menu)

        # Launches settings window on program start if no Requests URL is defined.
        if self.json_content["Requests URL"] is None:
            self.settings_window()

    # Accepts user input URL and calls logic  # TODO: Add settings window url box to this method
    def set_url(self, window, close_window=False):
        # TODO: VALIDITY CHECK - CHECK QT DESIGNER WIDGET
        self.json_content["Requests URL"] = window.text()
        Thread(target=upwatch.job_post_scraper(self.json_content)).start()
        if close_window:
            self.set_url_window.close()

    # Shows previously input URL in text input fields
    def print_url_qline(self, qline):
        qline.setToolTip(self.json_content["Requests URL"])
        qline.setText(self.json_content["Requests URL"])
        qline.setCursorPosition(0)

    def set_dbmr_state(self):
        if self.json_content["DBMR"] is False:
            self.json_content["DBMR"] = True
        else:
            self.json_content["DBMR"] = False
            self.json_content["Fixed Lowest Rate"] = 0
            self.json_content["Hourly Lowest Rate"] = 0

    def set_dbmr_fixed(self):
        if len(self.fixed_low_rate.text()) > 0:
            self.json_content["Fixed Lowest Rate"] = self.fixed_low_rate.text()
        else:
            self.json_content["Fixed Lowest Rate"] = 0

    def set_dbmr_hourly(self):
        if len(self.hourly_low_rate.text()) > 0:
            self.json_content["Hourly Lowest Rate"] = self.hourly_low_rate.text()
        else:
            self.json_content["Hourly Lowest Rate"] = 0

    def close_program(self):
        upwatch.write_to_json(self.json_content)
        self.app.quit()

    # TODO: Make sure set_url_window shows up under the Upwatch Icon!

    # "Set URL" Window
    def set_url_window(self):
        self.set_url_window = QtWidgets.QDialog()
        self.paste_url = QtWidgets.QLineEdit(self.set_url_window)
        self.paste_url.setPlaceholderText("Paste Valid Upwork URL here")
        # self.set_url_window = QtWidgets.QLineEdit("Paste your URL here")
        self.set_url_window.setGeometry(750, 0, 200, 30)
        self.paste_url.resize(200, 30)
        # self.set_url_window.QtWidgets.setCentralWidget(self.paste_url)  # TODO: FIX THIS INSTEAD OF RESIZE ON PREVIOUS LINE
        self.paste_url.returnPressed.connect(lambda: self.set_url(self.paste_url, True))
        self.set_url_window.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        )
        if self.json_content["Requests URL"] is not None:
            self.print_url_qline(self.paste_url)
        self.set_url_window.show()
        # TODO: Add "QRegexpValidator − Checks input against a Regex expression"

    # Settings Window  # TODO: Add "open upwatch on system startup option (default True)"
    def settings_window(self):
        self.settings_window = QtWidgets.QWidget()
        self.settings_window.setWindowTitle("Settings")
        self.settings_window.resize(340, 240)

        # URL Text Input label
        self.settings_label_url = QtWidgets.QLabel(self.settings_window)
        self.settings_label_url.setText("Paste Upwork URL Here")
        self.settings_label_url.setGeometry(QtCore.QRect(25, 20, 161, 16))
        self.settings_label_url.setToolTip(
            """Apply appropriate filters for your job on Upwork
and paste the URL from the browser (Must be a valid Upwork link)"""
        )

        # URL Text Input Box
        self.settings_line_edit = QtWidgets.QLineEdit(self.settings_window)
        self.settings_line_edit.setGeometry(QtCore.QRect(25, 45, 290, 21))
        self.settings_line_edit.setPlaceholderText("https://www.upwork.com/...")
        if self.json_content["Requests URL"] is not None:
            self.print_url_qline(self.settings_line_edit)
        self.settings_line_edit.returnPressed.connect(lambda: self.set_url(self.settings_line_edit))

        # Separator line
        self.separator = QtWidgets.QFrame(self.settings_window)
        self.separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.separator.setGeometry(QtCore.QRect(25, 100, 290, 10))

        # Don't Bother Me Rate groupBox
        self.low_rate_groupbox = QtWidgets.QGroupBox(self.settings_window)
        self.low_rate_groupbox.setGeometry(QtCore.QRect(10, 130, 320, 91))
        self.low_rate_groupbox.setFlat(True)
        self.low_rate_groupbox.setCheckable(True)
        self.low_rate_groupbox.setChecked(json_content["DBMR"])
        self.low_rate_groupbox.toggled.connect(self.set_dbmr_state)
        self.low_rate_groupbox.setTitle("Don't-Bother-Me Rate")
        self.low_rate_groupbox.setToolTip(
            "Job posts with a budget lower than your set\nvalue will not trigger a notification."
        )

        # Don't Bother Me Rate Input Boxes
        # Fixed
        self.fixed_low_rate_label = QtWidgets.QLabel(self.low_rate_groupbox)
        self.fixed_low_rate_label.setGeometry(QtCore.QRect(20, 40, 91, 16))
        self.fixed_low_rate_label.setText("Fixed-price")
        self.fixed_low_rate = QtWidgets.QLineEdit(self.low_rate_groupbox)
        self.fixed_low_rate.setGeometry(QtCore.QRect(20, 60, 113, 21))
        self.fixed_low_rate.setPlaceholderText("e.g.  120")
        if self.json_content["Fixed Lowest Rate"] != 0:
            self.fixed_low_rate.setText(self.json_content["Fixed Lowest Rate"])
        self.fixed_low_rate.setClearButtonEnabled(True)
        self.fixed_low_rate.setToolTip(
            "Any fixed-price job post paying less than your set value will be ignored."
        )
        self.fixed_low_rate.textChanged.connect(self.set_dbmr_fixed)

        # Hourly
        self.hourly_low_rate_label = QtWidgets.QLabel(self.low_rate_groupbox)
        self.hourly_low_rate_label.setGeometry(QtCore.QRect(180, 40, 60, 16))
        self.hourly_low_rate_label.setText("Hourly")
        self.hourly_low_rate = QtWidgets.QLineEdit(self.low_rate_groupbox)
        self.hourly_low_rate.setGeometry(QtCore.QRect(180, 60, 113, 21))
        self.hourly_low_rate.setPlaceholderText("e.g.  35")
        if self.json_content["Hourly Lowest Rate"] != 0:
            self.hourly_low_rate.setText(self.json_content["Hourly Lowest Rate"])
        self.hourly_low_rate.setClearButtonEnabled(True)
        self.hourly_low_rate.setToolTip(
            "Any hourly contract paying less than your set value will be ignored."
        )
        self.hourly_low_rate.textChanged.connect(self.set_dbmr_hourly)

        self.settings_window.show()

    # About Window
    def about_window(self):
        self.about_window = QtWidgets.QWidget()
        self.about_window.setWindowTitle("About")
        self.about_window.setGeometry(300, 300, 300, 300)

        about_label = QtWidgets.QLabel(self.about_window)
        about_label.setText("Created by The Philgrim")
        about_label.move(75, 80)

        about_button = QtWidgets.QPushButton(self.about_window)
        about_button.setText("Click Here Right Now!")
        about_button.move(65, 105)
        self.about_window.show()


json_content = upwatch.read_from_json()
gui = UpwatchGui(json_content)
gui.app.exec_()
