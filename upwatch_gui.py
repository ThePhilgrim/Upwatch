from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import threading
import upwatch


class UpwatchGui:
    def __init__(self, json_content):
        # JSON Dict with URL, Don't Bother Me Rate, Job Posts
        self.json_content = json_content

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

        # self.start_logic_thread()

    # Accepts user input URL
    def set_url(self, window, close_window=False):
        # TODO: VALIDITY CHECK - CHECK QT DESIGNER WIDGET
        self.json_content["Requests URL"] = window.text()
        if close_window:
            self.set_url_window.close()

    # Shows previously input URL in text input fields
    def print_url_qline(self, qline):
        qline.setToolTip(self.json_content["Requests URL"])
        qline.setText(self.json_content["Requests URL"])
        qline.setCursorPosition(0)

    def start_logic_thread(self):
        threading.Thread(target=upwatch.scrape_loop, args=[json_content], daemon=True).start()

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

    # TODO: Add to settings window:
    # 1) How ofter to run Scraper
    # 2) Igore posts that don't have specified budget/rate
    # 3) Run program on start up
    # Settings Window  # TODO: Add "open upwatch on system startup option (default True)"
    def settings_window(self):
        self.settings_window = QtWidgets.QWidget()
        self.settings_window.setWindowTitle("Settings")
        self.settings_window.resize(340, 380)

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

        # Separator lines
        self.separator = QtWidgets.QFrame(self.settings_window)
        self.separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.separator.setGeometry(QtCore.QRect(25, 100, 290, 10))

        self.separator_2 = QtWidgets.QFrame(self.settings_window)
        self.separator_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.separator_2.setGeometry(QtCore.QRect(25, 210, 290, 10))

        # Run program on startup
        self.run_on_startup = QtWidgets.QCheckBox(self.settings_window)
        self.run_on_startup.setGeometry(QtCore.QRect(25, 120, 300, 20))
        self.run_on_startup.setText("Run Upwatch on system startup")
        self.run_on_startup.adjustSize()
        self.run_on_startup.setChecked(True)  # TODO: Add "Are you sure"-dialog if unchecked

        # Set scraping interval
        self.scrape_interval_label = QtWidgets.QLabel(self.settings_window)
        self.scrape_interval_label.setGeometry(QtCore.QRect(25, 165, 80, 20))
        self.scrape_interval_label.setText("How often should Upwatch check \nfor new job posts? (minutes)")
        self.scrape_interval_label.adjustSize()
        self.scrape_interval = QtWidgets.QComboBox(self.settings_window)
        self.scrape_interval.setGeometry(QtCore.QRect(230, 175, 80, 20))
        self.scrape_interval.addItems(["10", "15", "20", "30", "45", "60"])

        # Don't Bother Me Rate groupBox
        self.low_rate_groupbox = QtWidgets.QGroupBox(self.settings_window)
        self.low_rate_groupbox.setGeometry(QtCore.QRect(25, 230, 290, 150))
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
        self.fixed_low_rate_label.setGeometry(QtCore.QRect(0, 40, 91, 16))
        self.fixed_low_rate_label.setText("Fixed-price")
        self.fixed_low_rate = QtWidgets.QLineEdit(self.low_rate_groupbox)
        self.fixed_low_rate.setGeometry(QtCore.QRect(0, 60, 113, 21))
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

        # Ignore Posts without budget/rate Checkbox
        self.ignore_no_budgets = QtWidgets.QCheckBox(self.low_rate_groupbox)
        self.ignore_no_budgets.setGeometry(QtCore.QRect(0, 100, 300, 20))
        self.ignore_no_budgets.setText("Don't show me job posts without a specified \nbudget/hourly rate")
        self.ignore_no_budgets.adjustSize()

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
