from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import upwatch
import time


class UpwatchGui:
    def __init__(self, json_content):
        self.json_content = json_content
        # self.user_input = upwatch.UserInput(json_content["URL"], json_content["Fixed Lowest Rate"], json_content["Hourly Lowest Rate"])

        if self.json_content["Requests URL"] is not None:
            upwatch.job_post_scraper(self.json_content)  # self.user_input used as arg before
            # TODO: If json_content["URL"] is None -> Run settings window

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
        quit_action = QtWidgets.QAction("Quit")
        quit_action.triggered.connect(self.app.quit)
        self.actions.append(quit_action)

        # Add buttons to menubar menu
        for action in self.actions:
            self.menu.addAction(action)

        # Add the menu to the tray
        self.tray.setContextMenu(self.menu)

    def set_url(self):
        self.json_content["Requests URL"] = self.line_edit.text()
        upwatch.job_post_scraper(self.json_content)  # self.user_input used as arg before
        self.set_url_window.close()

    # TODO: Make sure set_url_window shows up under the Upwatch Icon!
    def set_url_window(self):
        self.set_url_window = QtWidgets.QDialog()
        self.line_edit = QtWidgets.QLineEdit("Paste Upwork URL Here", self.set_url_window)
        # self.set_url_window = QtWidgets.QLineEdit("Paste your URL here")
        self.set_url_window.setGeometry(750, 0, 200, 30)
        self.line_edit.resize(200, 30)
        self.line_edit.returnPressed.connect(lambda: self.set_url())
        self.set_url_window.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.set_url_window.show()
        # TODO: Add "QRegexpValidator − Checks input against a Regex expression"

    def settings_window(self):
        self.settings_window = QtWidgets.QWidget()
        self.settings_window.setWindowTitle("Settings")
        # self.settings_window.setGeometry(X, Y, X2, Y2)
        self.settings_window.show()

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
