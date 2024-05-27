import sys
import os
import glob
import time
import webbrowser
from PyQt5.QtCore import Qt, QUrl, pyqtSlot, QThread, pyqtSignal, QTranslator, QLocale, QCoreApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QCheckBox, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtGui import QFont

def change_map():
    global map
    global site_url
    global where_am_i_click
    select_map = combobox.currentText()
    
    if map != select_map:
        site_url = f"https://tarkov-market.com/maps/{select_map}"
        map = select_map
        browser.setUrl(QUrl(site_url))
        where_am_i_click = False

def get_latest_file(folder_path):
    files = glob.glob(os.path.join(folder_path, '*'))
    
    if not files:
        return None
    else:
        latest_file = max(files, key=os.path.getmtime)
        return os.path.basename(latest_file)

def changeMarker(screenshot):
    styleList = [
        ['background', '#ff0000'],
        ['height', '30px'],
        ['width', '30px']
    ]
    
    for i in styleList:
        js_code = f"""
            var marker = document.getElementsByClassName('marker')[0];
            if (marker) {{
                marker.style.setProperty('{i[0]}', '{i[1]}', 'important');
            }} else {{
                console.log('Marker not found');
            }}
        """
        browser.page().runJavaScript(js_code)

def checkLocation(paths):
    screenshot = None
    for path in paths:
        screenshot = get_latest_file(path)
        if screenshot:
            break

    if screenshot is None:
        return

    global where_am_i_click
    if where_am_i_click == False:
        where_am_i_click = True
        js_code = """
            var button = document.querySelector('#__nuxt > div > div > div.page-content > div > div > div.panel_top.d-flex > div.d-flex.ml-15.fs-0 > button');
            if (button) {
                button.click();
                console.log('Button clicked');
            } else {
                console.log('Button not found');
            }
        """
        browser.page().runJavaScript(js_code)
        time.sleep(0.5)
        js_code = f"""
            var input = document.querySelector('input[type="text"]');
            if (input) {{
                input.value = '{screenshot.replace(".png", "")}';
                input.dispatchEvent(new Event('input'));
                console.log('Input value set');
            }} else {{
                console.log('Input not found');
            }}
        """
        browser.page().runJavaScript(js_code)
        changeMarker(screenshot)
    else:
        js_code = f"""
            var input = document.querySelector('input[type="text"]');
            if (input) {{
                input.value = '{screenshot.replace(".png", "")}';
                input.dispatchEvent(new Event('input'));
                console.log('Input value set');
            }} else {{
                console.log('Input not found');
            }}
        """
        browser.page().runJavaScript(js_code)
        changeMarker(screenshot)

def fullscreen():
    js_code = """
        var button = document.querySelector('#__nuxt > div > div > div.page-content > div > div > div.panel_top.d-flex > button');
        if (button) {
            button.click();
            console.log('Fullscreen button clicked');
        } else {
            console.log('Fullscreen button not found');
        }
    """
    browser.page().runJavaScript(js_code)

def pannelControl():
    js_code = """
        var button = document.evaluate('//*[@id="__nuxt"]/div/div/div[2]/div/div/div[1]/div[1]/button', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
        if (button) {
            button.click();
            console.log('Panel control button clicked');
        } else {
            console.log('Panel control button not found');
        }
    """
    browser.page().runJavaScript(js_code)

def start_auto_detection(paths):
    global auto_detection_thread
    if not auto_detection_thread.isRunning():
        auto_detection_thread.paths = paths
        auto_detection_thread.start()

class AutoDetectionThread(QThread):
    new_file_detected = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.paths = []
        self.previous_files = {}

    def run(self):
        while True:
            current_files = {}
            for path in self.paths:
                if os.path.exists(path):
                    files = glob.glob(os.path.join(path, '*'))
                    current_files[path] = set(files)

            for path, files in current_files.items():
                if path in self.previous_files:
                    new_files = files - self.previous_files[path]
                    if new_files:
                        latest_file = max(new_files, key=os.path.getmtime)
                        self.new_file_detected.emit([latest_file])
                self.previous_files[path] = files

            time.sleep(2)

def read_paths_from_file(file_path):
    home_directory = os.path.expanduser('~')
    paths = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                path = os.path.join(home_directory, line.strip())
                if os.path.exists(path):
                    paths.append(path)
    return paths

def set_language(language):
    global translator
    if translator.load(f"translation/app_{language}.qm"):
        app.installTranslator(translator)
        QCoreApplication.installTranslator(translator)
        window.retranslateUi()

mapList = ['ground-zero', 'factory', 'customs', 'interchange', 'woods', 'shoreline', 'lighthouse', 'reserve', 'streets', 'lab']

map = "ground-zero"
site_url = f"https://tarkov-market.com/maps/{map}"
txt_file_path = 'file_path.txt'
where_am_i_click = False

class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EFT Where am I? (ver.1.2)")
        self.setGeometry(100, 100, 1200, 1000)
        self.setStyleSheet("background-color: gray; color: white;")

        global browser
        browser = QWebEngineView()
        browser.setUrl(QUrl(site_url))
        browser.loadFinished.connect(self.on_load_finished)
        
        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        top_layout_1 = QHBoxLayout()
        main_layout.addLayout(top_layout_1)

        left_layout = QVBoxLayout()
        self.map_label = QLabel(self.tr('Select The Map.'), self)
        self.map_label.setFont(QFont('Helvetica', 18, QFont.Bold))
        self.map_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.map_label)

        combobox_layout = QHBoxLayout()
        global combobox
        combobox = QComboBox(self)
        combobox.addItems(mapList)
        combobox.setCurrentText("ground-zero")
        combobox.setFont(QFont('Helvetica', 16))
        combobox.setStyleSheet("background-color: white; color: black;")
        combobox_layout.addWidget(combobox)

        self.b1 = QPushButton(self.tr('Apply'), self)
        self.b1.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.b1.clicked.connect(change_map)
        combobox_layout.addWidget(self.b1)

        left_layout.addLayout(combobox_layout)

        self.auto_detect_checkbox = QCheckBox(self.tr('Auto Screenshot Detection'), self)
        self.auto_detect_checkbox.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.auto_detect_checkbox.setStyleSheet("margin: 0 auto;")
        self.auto_detect_checkbox.setLayoutDirection(Qt.LeftToRight)
        self.auto_detect_checkbox.toggled.connect(self.toggle_auto_detection)
        left_layout.addWidget(self.auto_detect_checkbox)

        top_layout_1.addLayout(left_layout)

        left_separator = QFrame()
        left_separator.setFrameShape(QFrame.VLine)
        left_separator.setFrameShadow(QFrame.Sunken)
        top_layout_1.addWidget(left_separator)

        center_layout = QVBoxLayout()
        self.b_panel_control = QPushButton(self.tr('Hide/Show Pannels'), self)
        self.b_panel_control.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.b_panel_control.clicked.connect(pannelControl)
        center_layout.addWidget(self.b_panel_control)

        self.b_fullscreen = QPushButton(self.tr('Full Screen'), self)
        self.b_fullscreen.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.b_fullscreen.clicked.connect(fullscreen)
        center_layout.addWidget(self.b_fullscreen)

        self.b_force = QPushButton(self.tr('Force Run'), self)
        self.b_force.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.b_force.clicked.connect(lambda: checkLocation(read_paths_from_file(txt_file_path)))
        center_layout.addWidget(self.b_force)
        top_layout_1.addLayout(center_layout)

        center_separator = QFrame()
        center_separator.setFrameShape(QFrame.VLine)
        center_separator.setFrameShadow(QFrame.Sunken)
        top_layout_1.addWidget(center_separator)

        right_layout = QVBoxLayout()

        # Language selection layout
        language_layout = QHBoxLayout()
        self.language_combobox = QComboBox(self)
        self.language_combobox.addItem("English", "en")
        self.language_combobox.addItem("한국어", "ko")
        self.language_combobox.setFont(QFont('Helvetica', 16))
        language_layout.addWidget(self.language_combobox)

        self.language_apply_button = QPushButton(self.tr('Apply Language'), self)
        self.language_apply_button.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.language_apply_button.clicked.connect(self.apply_language)
        language_layout.addWidget(self.language_apply_button)

        right_layout.addLayout(language_layout)

        self.b3 = QPushButton(self.tr('How to use'), self)
        self.b3.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.b3.setStyleSheet("color: #0645AD;")
        self.b3.clicked.connect(lambda: open_url("https://github.com/karpitony/eft-where-am-i/blob/main/README.md"))
        right_layout.addWidget(self.b3)

        self.b5 = QPushButton(self.tr('Bug Report'), self)
        self.b5.setFont(QFont('Helvetica', 16, QFont.Bold))
        self.b5.setStyleSheet("color: #0645AD;")
        self.b5.clicked.connect(lambda: open_url("https://github.com/karpitony/eft-where-am-i/issues"))
        right_layout.addWidget(self.b5)

        top_layout_1.addLayout(right_layout)

        main_layout.addWidget(browser)

    def apply_language(self):
        language = self.language_combobox.currentData()
        set_language(language)

    @pyqtSlot(bool)
    def on_load_finished(self, ok):
        if self.auto_detect_checkbox.isChecked():
            checkLocation(read_paths_from_file(txt_file_path))

    @pyqtSlot(bool)
    def toggle_auto_detection(self, checked):
        paths = read_paths_from_file(txt_file_path)
        if checked:
            start_auto_detection(paths)

    def retranslateUi(self):
        self.setWindowTitle(self.tr("EFT Where am I? (ver.1.2)"))
        self.map_label.setText(self.tr('Select The Map.'))
        self.b1.setText(self.tr('Apply'))
        self.auto_detect_checkbox.setText(self.tr('Auto Screenshot Detection'))
        self.b_panel_control.setText(self.tr('Hide/Show Pannels'))
        self.b_fullscreen.setText(self.tr('Full Screen'))
        self.b_force.setText(self.tr('Force Run'))
        self.b3.setText(self.tr('How to use'))
        self.b5.setText(self.tr('Bug Report'))
        self.language_apply_button.setText(self.tr('Apply Language'))

def open_url(url):
    webbrowser.open_new(url)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    translator = QTranslator()
    locale = QLocale.system().name()
    translator.load(f"translation/app_{locale}.qm")
    app.installTranslator(translator)
    QCoreApplication.installTranslator(translator)

    auto_detection_thread = AutoDetectionThread()
    auto_detection_thread.new_file_detected.connect(lambda x: checkLocation(x))
    
    window = BrowserWindow()
    window.show()

    sys.exit(app.exec_())
