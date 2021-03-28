from __future__ import annotations
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from functools import partial
from typing import List, Union
import upwatch
import time
import webbrowser
import sys
import pathlib


# TODO: Make "run on startup" system independent
def manage_startup_plist_file(json_content: upwatch.JsonContent) -> None:
    """ Creates a plist file and saves it as a Launch Agent to run Upwatch on system startup """
    plist_path = pathlib.Path("~/Library/LaunchAgents").expanduser()

    error_path = pathlib.Path(__file__).parent / "upwatch.error"

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>upwatch.gui.py</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{__file__}</string>
    </array>
    <key>StandardErrorPath</key>
    <string>{error_path}</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""

    if (
        not (plist_path / "upwatch_startup.plist").exists()
        and json_content["Run on startup"]
    ):
        with open(plist_path / "upwatch_startup.plist", "w") as startup_plist:
            startup_plist.write(plist_content)
    elif (plist_path / "upwatch_startup.plist").exists() and not json_content[
        "Run on startup"
    ]:
        (plist_path / "upwatch_startup.plist").unlink()


def set_url(
    json_content: upwatch.JsonContent,
    window: QtWidgets.QWidget,
    close_window: bool = False,
) -> None:
    """ Accepts user input URL and stores it in json_content """
    # TODO: VALIDITY CHECK - CHECK QT DESIGNER WIDGET
    if window.text():
        json_content["Requests URL"] = window.text()
    else:
        json_content["Requests URL"] = ""
    if close_window:
        appcore.url_dialog.window.close()


def print_url_qline(
    json_content: upwatch.JsonContent, qline: QtWidgets.QWidget
) -> None:  # TODO: Consider if this method can be merged with set_url()
    """ Shows previously input URL in text input fields """
    qline.setToolTip(json_content["Requests URL"])
    qline.setText(json_content["Requests URL"])
    qline.setCursorPosition(0)


class AppCore:
    def __init__(self, json_content: upwatch.JsonContent, json_found: bool) -> None:
        # JSON Dict with URL, Don't Bother Me Rate, Job Posts
        self.json_content = json_content
        self.json_found = json_found

        # Creates upwatch_startup.plist first time program is run
        if not json_found:
            manage_startup_plist_file(self.json_content)

        # Main Application
        self.app = QtWidgets.QApplication([])
        self.app.setQuitOnLastWindowClosed(False)

        self.url_dialog = UrlDialog(self.json_content)
        settings = SettingsWindow(self.json_content)
        about = AboutWindow()

        # Create the icon
        logo_path = pathlib.Path(__file__).parent
        self.icon = QtGui.QIcon(str(logo_path / "uwlogo.png"))  # TODO: Fix own logo

        # Create the tray
        self.tray = QtWidgets.QSystemTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setVisible(True)

        self.actions: List[QtWidgets.QAction] = []

        # Create the menu
        self.menu = QtWidgets.QMenu()
        url_action = QtWidgets.QAction("Set URL")
        url_action.triggered.connect(
            lambda: self.show_raise_window(
                self.url_dialog, self.url_dialog.window, True
            )
        )
        self.actions.append(url_action)

        settings_action = QtWidgets.QAction("Settings")
        settings_action.triggered.connect(
            lambda: self.show_raise_window(settings, settings.window, True)
        )
        self.actions.append(settings_action)

        about_action = QtWidgets.QAction("About")
        about_action.triggered.connect(
            lambda: self.show_raise_window(about, about.window)
        )
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
        if not self.json_content["Requests URL"]:
            self.show_raise_window(
                settings, settings.window
            )  # instantiate settings class Here

        self.worker_thread = WorkerThread(self.json_content)
        self.worker_thread.job_done.connect(self.on_job_done)
        self.worker_thread.json_content = self.json_content
        self.worker_thread.start()

        self.tray.messageClicked.connect(self.message_clicked)

    def show_raise_window(
        self, instance: Union[UrlDialog, SettingsWindow, AboutWindow], window: QtWidgets.QWidget, _print: bool = False
    ) -> None:
        # Shows the currently set URL if window is settins or url dialog
        if _print:
            print_url_qline(self.json_content, instance.url_input)
        window.show()
        window.raise_()

    def open_url(
        self, url: str, event: QtGui.QMouseEvent
    ) -> None:  # TODO: Move this outside class or to other class
        webbrowser.open_new_tab(url)

    def close_program(self) -> None:
        """ Closes Upwatch """
        # upwatch.write_to_json(self.json_content, json_path)
        self.app.quit()

    def enter_box(self, partialed: QtWidgets.QLabel, event: QtCore.QEvent) -> None:
        print(event)
        partialed.setStyleSheet("text-decoration: underline;")

    def exit_box(self, partialed: QtWidgets.QLabel, event: QtCore.QEvent) -> None:
        partialed.setStyleSheet("text-decoration: none;")

    def job_post_dialog(self) -> None:
        # https://github.com/python-qt-tools/PyQt5-stubs/issues/147
        self.scroll_area = QtWidgets.QScrollArea(widgetResizable=True)  # type: ignore
        self.widget = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.widget)
        self.vbox = QtWidgets.QVBoxLayout()
        self.widget.setLayout(self.vbox)

        self.scroll_area.setFixedWidth(300)
        self.scroll_area.setFixedHeight(600)

        # TODO: Bind escape & enter to close window
        # self.scroll_area.setWindowFlags(
        #     QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        # )

        font_style = QtGui.QFont()
        font_style.setBold(True)

        for job_post in self.selected_new_job_posts:
            self.dialog_groupbox = QtWidgets.QGroupBox(objectName="job_post_box")
            self.groupbox_layout = QtWidgets.QVBoxLayout()
            self.dialog_groupbox.setLayout(self.groupbox_layout)
            self.dialog_groupbox.setMouseTracking(True)

            title = QtWidgets.QLabel()
            title.setText(job_post["Job Title"])
            title.setWordWrap(True)
            title.setFont(font_style)

            self.dialog_groupbox.enterEvent = partial(self.enter_box, title)
            self.dialog_groupbox.leaveEvent = partial(self.exit_box, title)

            payment = QtWidgets.QLabel()
            if job_post["Budget"]:
                payment.setText(
                    job_post["Payment Type"] + ": " + job_post["Budget"] + "\n"
                )
            else:
                payment.setText(job_post["Payment Type"] + "\n")
            payment.setWordWrap(True)

            description = QtWidgets.QLabel()
            description.setText(
                job_post["Job Description"][:150].replace("\n\n", "\n") + "...\n"
            )
            description.setWordWrap(True)
            url = job_post["Job Post URL"]

            self.vbox.addWidget(self.dialog_groupbox)
            self.groupbox_layout.addWidget(title)
            self.groupbox_layout.addWidget(payment)
            self.groupbox_layout.addWidget(description)

            self.dialog_groupbox.mousePressEvent = partial(self.open_url, url)

        self.scroll_area.move(800, 0)
        self.scroll_area.show()

    def on_job_done(self, result: List[upwatch.JobPost]) -> None:
        fixed_dbmr_rate = self.json_content["Fixed Lowest Rate"]

        hourly_dbmr_rate = self.json_content["Hourly Lowest Rate"]

        self.selected_new_job_posts = []

        if self.json_content["Ignore no budget"]:
            for job_post in result:
                # job_post["Payment Type"] can be "Fixed-price", "Hourly: $X.00–$Y.00", or "Hourly"
                if (
                    job_post["Payment Type"] == "Fixed-price"
                    and job_post["Budget"]
                    and (
                        upwatch.extract_fixed_price(job_post["Budget"])
                        >= fixed_dbmr_rate
                        or "placeholder" in job_post["Job Description"].lower()
                    )
                ):
                    self.selected_new_job_posts.append(job_post)
                elif (
                    job_post["Payment Type"].split()[0] == "Hourly:"
                    and upwatch.extract_hourly_price(job_post["Payment Type"])
                    >= hourly_dbmr_rate
                ):
                    self.selected_new_job_posts.append(job_post)
        else:
            for job_post in result:
                if job_post["Payment Type"] == "Fixed-price" and (
                    upwatch.extract_fixed_price(job_post["Budget"]) >= fixed_dbmr_rate
                    or "placeholder" in job_post["Job Description"]
                ):
                    self.selected_new_job_posts.append(job_post)
                elif job_post["Payment Type"] == "Hourly" or (
                    job_post["Payment Type"].split()[0] == "Hourly:"
                    and upwatch.extract_hourly_price(job_post["Payment Type"])
                    >= hourly_dbmr_rate
                ):
                    self.selected_new_job_posts.append(job_post)

        self.selected_job_posts_number = len(self.selected_new_job_posts)

        if self.selected_job_posts_number == 1:
            self.current_job_post = self.selected_new_job_posts[0]
            if self.current_job_post["Payment Type"] == "Fixed-price":
                self.tray.showMessage(
                    self.current_job_post["Budget"]
                    + " – "
                    + self.current_job_post["Job Title"],
                    self.current_job_post["Job Description"][:150],
                    self.icon,
                    10000,
                )
            elif self.current_job_post["Payment Type"].startswith("Hourly:"):
                self.tray.showMessage(
                    self.current_job_post["Budget"]
                    + ": "
                    + self.current_job_post["Job Title"],
                    self.current_job_post["Job Description"][:150],
                    self.icon,
                    10000,
                )  # TODO: Title not shown right until todo in upwatch.py is fixed
            else:
                self.tray.showMessage(
                    self.current_job_post["Payment Type"]
                    + " – "
                    + self.current_job_post["Job Title"],
                    self.current_job_post["Job Description"][:150],
                    self.icon,
                    10000,
                )
        elif self.selected_job_posts_number > 1:
            self.tray.showMessage(
                str(self.selected_job_posts_number) + " New Job Posts",
                "Click here to see job posts.",
                self.icon,
                10000,
            )

    def message_clicked(self) -> None:
        if self.selected_job_posts_number == 1:
            webbrowser.open_new_tab(self.current_job_post["Job Post URL"])
        else:
            self.job_post_dialog()


class UrlDialog:
    """ Creates the 'Set URL' dialog for user to specify URL to scrape from """

    def __init__(self, json_content: upwatch.JsonContent) -> None:
        self.json_content = json_content
        self.window = QtWidgets.QDialog()
        self.window.setGeometry(
            750, 0, 200, 30
        )  # TODO: Make sure this dialog opens under icon
        self.window.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        )
        self.url_input = QtWidgets.QLineEdit(self.window)
        self.url_input.setClearButtonEnabled(True)
        self.url_input.setPlaceholderText("Paste Valid Upwork URL here")
        self.url_input.resize(200, 30)  # Makes QLineEdit fill size of dialog window
        self.url_input.returnPressed.connect(
            lambda: set_url(self.json_content, self.url_input, True)
        )

        # TODO: Add "QRegexpValidator − Checks input against a Regex expression"


class SettingsWindow:
    """ Creates Program's Settings Window """

    def __init__(self, json_content: upwatch.JsonContent) -> None:
        self.json_content = json_content
        grid = QtWidgets.QGridLayout()
        self.window = QtWidgets.QWidget()
        self.window.setLayout(grid)

        # URL Text Input label
        self.url_label = QtWidgets.QLabel("Paste Upwork URL Here")
        self.url_label.setToolTip(
            """Apply appropriate filters for your job on Upwork
            and paste the URL from the browser (Must be a valid Upwork link)"""
        )

        # URL Text Input Box
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("https://www.upwork.com/...")
        self.url_input.textChanged.connect(
            lambda: set_url(self.json_content, self.url_input)
        )

        # Separator lines
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)

        separator_2 = QtWidgets.QFrame()
        separator_2.setFrameShape(QtWidgets.QFrame.HLine)
        separator_2.setFrameShadow(QtWidgets.QFrame.Sunken)

        # Run program on startup
        self.run_on_startup = QtWidgets.QCheckBox()
        self.run_on_startup.setText("Run Upwatch on system startup")
        self.run_on_startup.adjustSize()
        self.run_on_startup.setChecked(json_content["Run on startup"])
        self.run_on_startup.toggled.connect(self.set_startup_state)

        # TODO: Add "Are you sure"-dialog if unchecked

        # Set scraping interval
        self.scrape_interval_label = QtWidgets.QLabel(
            "How often should Upwatch check \nfor new job posts? (minutes)"
        )
        self.scrape_interval_label.adjustSize()
        self.scrape_interval = QtWidgets.QComboBox()
        self.scrape_interval.addItems(["5", "10", "20", "30", "45", "60"])
        self.scrape_interval.setCurrentText(str(json_content["Scrape interval"]))
        self.scrape_interval.currentIndexChanged.connect(self.set_scrape_interval)

        # Don't Bother Me Rate groupBox
        low_rate_grid = QtWidgets.QGridLayout()
        self.dbmr_groupbox = QtWidgets.QGroupBox()
        self.dbmr_groupbox.setLayout(low_rate_grid)
        self.dbmr_groupbox.setFlat(True)
        self.dbmr_groupbox.setCheckable(True)
        self.dbmr_groupbox.setChecked(json_content["DBMR"])
        self.dbmr_groupbox.toggled.connect(self.set_dbmr_state)
        self.dbmr_groupbox.setTitle("Don't-Bother-Me Rate")
        self.dbmr_groupbox.setToolTip(
            "Job posts with a budget lower than your set\nvalue will not trigger a notification."
        )

        # Don't Bother Me Rate Input Boxes
        # Fixed
        self.fixed_dbmr_label = QtWidgets.QLabel(self.dbmr_groupbox)
        self.fixed_dbmr_label.setText("Fixed-price")
        self.fixed_dbmr_input = QtWidgets.QLineEdit(self.dbmr_groupbox)
        self.fixed_dbmr_input.setPlaceholderText("e.g.  120")
        if self.json_content["Fixed Lowest Rate"] != 0:
            self.fixed_dbmr_input.setText(str(self.json_content["Fixed Lowest Rate"]))
        self.fixed_dbmr_input.setClearButtonEnabled(True)
        self.fixed_dbmr_input.setToolTip(
            "Any fixed-price job post paying less than your set value will be ignored."
        )
        self.fixed_dbmr_input.textChanged.connect(self.set_dbmr_fixed)

        # Hourly
        self.hourly_dbmr_label = QtWidgets.QLabel(self.dbmr_groupbox)
        self.hourly_dbmr_label.setText("Hourly")
        self.hourly_dbmr_input = QtWidgets.QLineEdit(self.dbmr_groupbox)
        self.hourly_dbmr_input.setPlaceholderText("e.g.  35")
        if self.json_content["Hourly Lowest Rate"] != 0:
            self.hourly_dbmr_input.setText(str(self.json_content["Hourly Lowest Rate"]))
        self.hourly_dbmr_input.setClearButtonEnabled(True)
        self.hourly_dbmr_input.setToolTip(
            "Any hourly contract paying less than your set value will be ignored."
        )
        self.hourly_dbmr_input.textChanged.connect(self.set_dbmr_hourly)

        # Ignore Posts without budget/rate Checkbox
        self.ignore_no_budget = QtWidgets.QCheckBox(self.dbmr_groupbox)
        self.ignore_no_budget.setText(
            "Don't show me job posts without a specified \nbudget/hourly rate"
        )
        self.ignore_no_budget.adjustSize()
        self.ignore_no_budget.setChecked(json_content["Ignore no budget"])
        self.ignore_no_budget.toggled.connect(self.set_ignore_no_budget)

        # Add widgets to grid layout
        grid.addWidget(self.url_label, 0, 0, alignment=QtCore.Qt.AlignLeft)
        grid.addWidget(self.url_input, 1, 0, 1, 2, alignment=QtCore.Qt.AlignTop)
        grid.addWidget(separator, 2, 0, 1, 2)
        grid.addWidget(self.run_on_startup, 3, 0, alignment=QtCore.Qt.AlignLeft)
        grid.addWidget(self.scrape_interval_label, 4, 0)
        grid.addWidget(self.scrape_interval, 4, 1, alignment=QtCore.Qt.AlignRight)
        grid.addWidget(separator_2, 5, 0, 1, 2)
        grid.addWidget(self.dbmr_groupbox, 6, 0, 3, 2, alignment=QtCore.Qt.AlignBottom)

        low_rate_grid.addWidget(
            self.fixed_dbmr_label, 0, 0, alignment=QtCore.Qt.AlignBottom
        )
        low_rate_grid.addWidget(self.fixed_dbmr_input, 1, 0)
        low_rate_grid.addWidget(
            self.hourly_dbmr_label, 0, 1, alignment=QtCore.Qt.AlignBottom
        )
        low_rate_grid.addWidget(self.hourly_dbmr_input, 1, 1)
        low_rate_grid.addWidget(self.ignore_no_budget, 2, 0, 1, 2)

    def set_startup_state(self) -> None:
        """ Enables / Disables 'Run on startup' in json """
        if self.json_content["Run on startup"]:
            # TODO: Create "are you sure"-window
            self.json_content["Run on startup"] = False
        else:
            self.json_content["Run on startup"] = True

        manage_startup_plist_file(self.json_content)

    def set_scrape_interval(self) -> None:
        """ Sets the 'Scrape interval' state in json """
        self.json_content["Scrape interval"] = int(self.scrape_interval.currentText())

    def set_dbmr_state(self) -> None:
        """ Enables / Disables 'Don't bother me rate' in json """
        if not self.json_content["DBMR"]:
            self.json_content["DBMR"] = True
        else:
            self.json_content["DBMR"] = False
            self.fixed_dbmr_input.clear()
            self.hourly_dbmr_input.clear()
            self.json_content["Fixed Lowest Rate"] = 0
            self.json_content["Hourly Lowest Rate"] = 0

    def set_dbmr_fixed(self) -> None:
        """ Sets the value of 'Don't bother me rate' for fixed-price job posts """
        if self.fixed_dbmr_input.text():
            self.json_content["Fixed Lowest Rate"] = int(self.fixed_dbmr_input.text())
        else:
            self.json_content["Fixed Lowest Rate"] = 0

    def set_dbmr_hourly(self) -> None:
        """ Sets the value of 'Don't bother me rate' for hourly job posts """
        if self.hourly_dbmr_input.text():
            self.json_content["Hourly Lowest Rate"] = int(self.hourly_dbmr_input.text())
        else:
            self.json_content["Hourly Lowest Rate"] = 0

    def set_ignore_no_budget(self) -> None:
        """ Enables / Disables if to ignore job posts without a specified budget in json """
        self.json_content["Ignore no budget"] = not self.json_content[
            "Ignore no budget"
        ]


class AboutWindow:
    """ Creates program's About window """

    def __init__(self) -> None:
        self.window = QtWidgets.QWidget()
        self.window.setWindowTitle("About")
        self.window.setGeometry(300, 300, 300, 300)

        label = QtWidgets.QLabel(self.window)
        label.setText("Created by The Philgrim")
        label.move(75, 80)

        button = QtWidgets.QPushButton(self.window)
        button.setText("Click Here Right Now!")
        button.move(65, 105)


class WorkerThread(QtCore.QThread):

    job_done = QtCore.pyqtSignal(object)

    def __init__(self, json_content: upwatch.JsonContent) -> None:
        super().__init__()
        self.json_content = json_content

    def run(self) -> None:
        """Calls the web scraping function on a scheduled interval,
        and sleeps in between for the time specified in json"""
        while not self.json_content["Requests URL"]:
            time.sleep(0.5)  # wait for url to be entered
        while True:
            sleep_time = self.json_content["Scrape interval"]
            new_job_posts = upwatch.job_post_scraper(self.json_content)
            self.job_done.emit(new_job_posts)
            print("job done. Sleeping " + str(sleep_time) + " minute(s).")
            time.sleep(sleep_time * 60)
            print("Let's go again")


json_path = pathlib.Path(__file__).parent
json_content, json_found = upwatch.read_from_json(json_path)
appcore = AppCore(json_content, json_found)
appcore.app.exec_()
