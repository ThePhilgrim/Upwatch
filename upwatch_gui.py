from PyQt5 import QtGui
from PyQt5 import QtWidgets
import upwatch


class UpwatchGui:
    def __init__(self):
        self.user_input = upwatch.UserInput()

        if self.user_input.url:
            upwatch.job_post_scraper(self.user_input)

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
        self.user_input.url = self.set_url_window.text()
        upwatch.job_post_scraper(self.user_input)
        self.set_url_window.close()

    def set_url_window(self):
        self.set_url_window = QtWidgets.QLineEdit("Set URL")
        self.set_url_window.setGeometry(750, 50, 150, 50)
        self.set_url_window.returnPressed.connect(lambda: self.set_url())
        self.set_url_window.show()

    def settings_window(self):
        self.settings_window = QtWidgets.QWidget()
        self.settings_window.setWindowTitle("Settings")
        # self.settings_window.setGeometry(X, Y, X2, Y2)
        self.settings_window.show()

    def about_window(self):
        self.about_window = QtWidgets.QWidget()
        self.about_window.setWindowTitle("About")
        # self.about_window.setGeometry(X, Y, X2, Y2)
        self.about_window.show()


gui = UpwatchGui()
gui.app.exec_()
