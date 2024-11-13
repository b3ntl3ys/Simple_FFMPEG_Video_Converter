import sys
import os
import re
import time
import json
import traceback
import requests

import zipfile
import urllib.request
import subprocess
from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW
from datetime import datetime
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtGui import QFont,QDesktopServices

from PyQt5.QtCore import QThread,QSettings,QSize,Qt,QTimer,QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QTableWidget, QPushButton, QComboBox, QTableWidgetItem, QLabel, \
    QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit, QTabWidget,QSizePolicy,QPlainTextEdit,QGroupBox,QAction,QMessageBox,QMenu,QProgressDialog,QDialog,QListWidget,QInputDialog,QSpacerItem,QStatusBar


DARK_STYLE = """
    QMainWindow {
        background-color: #212121;
    }
    QInputDialog{
        background-color: #212121;
    }
    QTabWidget::pane {
        border: none;
    }
    QTabBar {
        background-color: #121212;
        color: #ffffff;
    }
    QTabBar::tab:selected {
        background-color: #424242;
    }
    QTabBar::tab:!selected {
        background-color: #1c1c1c;
    }
    QPushButton {
        border-radius: 15px;
        background-color: #0056b3;
        color: white;
        border: none;
        padding: 8px 15px;
    }
    QPushButton:hover {
        background-color: #474747;
    }
    QLineEdit, QComboBox, QPlainTextEdit {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #333333;
    }
    QComboBox {
        font-weight: bold;  /* Make text bold */
        font-size: 12px;  /* Set the text size */
        border-radius: 10px;  /* Rounded corners */
        padding: 6px 12px;  /* Padding inside the combobox */
    }

    QTableWidget ,QListWidget {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    QTableWidget QHeaderView::section {
        background-color: #333333;
        color: #ffffff;
    }
    QLabel ,QGroupBox{
        color: #ffffff;
        
    }
    QMessageBox {
        background-color: #212121;
        color: #ffffff;
    }
    QMessageBox QPushButton {
        background-color: #333333;
        color: white;
        border: 1px solid #444444;
    }
"""

ABOUT_DARK_STYLE =("""
                   
    QMainWindow {
        background-color: #212121;
    }
                   
    QLabel {
        color: #ffffff;
        background-color: #212121;
        font-size: 14px;  /* Set font size */
        font-weight: bold;  /* Make font bold */
    }
""")


example_commands = [

    'AMD',
    'ffmpeg -i "<input>" -c:v h264_amf -quality balanced -b:v 4M "<output>"',
    'ffmpeg -i "<input>" -c:v h264_amf -quality speed -b:v 4M "<output>"',
    'ffmpeg -i "<input>" -c:v h264_amf -quality quality -b:v 4M "<output>"',
    '',
    'Copy Subtitles',
    'ffmpeg -i "<input>" -map 0 -c:v h264_amf -quality speed -b:v 4M -c:s mov_text "<output>"',
    'ffmpeg -i "<input>" -map 0 -c:v libx264 -preset fast -crf 23 -c:a aac -c:s mov_text "<output>"',
    'ffmpeg -i "<input>" -map 0 -c:v h264_qsv -preset veryfast -b:v 5M -c:s mov_text "<output>"',
    'ffmpeg -hwaccel cuvid -i "<input>" -map 0 -c:v hevc_nvenc -preset fast -c:a copy -c:s mov_text "<output>"',
    '',
    'CPU',
    'ffmpeg -i "<input>" -c:v libx264 -preset slow -crf 23 -c:a aac "<output>"',
    'ffmpeg -i "<input>" -c:v libx264 -preset medium -crf 23 -c:a aac "<output>"',
    'ffmpeg -i "<input>" -c:v libx264 -preset fast -crf 23 -c:a aac "<output>"',
    '',
    'INTEL',
    'ffmpeg -i "<input>" -c:v h264_qsv -preset veryfast -b:v 5M "<output>"',
    'ffmpeg -i "<input>" -c:v h264_qsv -preset faster -b:v 5M "<output>"',
    'ffmpeg -i "<input>" -c:v h264_qsv -preset medium -b:v 5M "<output>"',
    '',
    'NVIDIA',
    'ffmpeg -hwaccel cuvid -i "<input>" -c:v hevc_nvenc -b:v 2M -maxrate 2M -bufsize 2M -preset fast -c:a copy "<output>"',
    'ffmpeg -hwaccel cuvid -i "<input>" -c:v hevc_nvenc -b:v 3M -maxrate 3M -bufsize 3M -preset fast -c:a copy "<output>"',
    'ffmpeg -hwaccel cuvid -i "<input>" -c:v hevc_nvenc -preset slow -qp 23 -c:a aac "<output>"',
    'ffmpeg -hwaccel cuvid -i "<input>" -c:v hevc_nvenc -preset medium -qp 23 -c:a aac "<output>"',
    'ffmpeg -hwaccel cuvid -i "<input>" -c:v hevc_nvenc -preset fast -qp 23 -c:a aac "<output>"',

]

current_version = '1.0.2'
                    
simultaneous_encodes = "1", "2", "3","4","5","6","7","8"


input_folder = ""


class StreamRedirector(QtCore.QObject):
    text_written = QtCore.pyqtSignal(str)  # Signal to emit the text to the main thread.

    def __init__(self):
        super().__init__()

    def write(self, message):
        if message.strip() != "":
            self.text_written.emit(message)  # Emit the text to be handled in the main thread.

    def flush(self):
        pass

#region VideoEncoderThread
def get_video_duration(video_file):
    """Get the duration of a video using FFprobe."""
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_file]
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        output = subprocess.check_output(command, universal_newlines=True, startupinfo=startupinfo)
        return float(output.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error getting video duration for {video_file}: {e}")
        return None
    
from concurrent.futures import ThreadPoolExecutor

class VideoEncoderThread(QThread):
    fps_updated = QtCore.pyqtSignal(int, float)
    encoding_canceled = QtCore.pyqtSignal()
    encoding_complete = QtCore.pyqtSignal()
    encoding_progress_updated = QtCore.pyqtSignal(int, str)
    encoding_completed = QtCore.pyqtSignal(int)
    console_output_updated = QtCore.pyqtSignal(str)

    def __init__(self, input_files, output_folder, simultaneous_encodes, format_combobox, custom_command_combobox):
        super().__init__()
        self.input_files = input_files
        self.output_folder = output_folder
        self.simultaneous_encodes = simultaneous_encodes
        self.format_combobox = format_combobox
        self.custom_command_combobox = custom_command_combobox
        self.processes = []
        self.elapsed_times = [0] * len(input_files)
        self.start_times = [simultaneous_encodes] * len(input_files)
        self._is_canceled = False
        self.started_encoding = [False] * len(input_files)
        self.finished_encoding = [False] * len(input_files)
        self.processed_frames = [0] * len(input_files)

    def run(self):
        with ThreadPoolExecutor(max_workers=self.simultaneous_encodes) as executor:
            futures = []

            for i, input_file in enumerate(self.input_files):
                custom_command = self.custom_command_combobox.currentText()
                selected_format = self.format_combobox.currentText()
                output_file = os.path.splitext(os.path.join(self.output_folder, os.path.basename(input_file)))[0] + f'.{selected_format}'

                # Insert the '-y' flag to overwrite existing files without asking
                command = custom_command.replace('<input>', input_file).replace('<output>', output_file)
                command_parts = command.split()
                command_parts.insert(1, '-y')  # Insert '-y' right after 'ffmpeg' command
                command = ' '.join(command_parts)

                future = executor.submit(self.execute_ffmpeg, command, i)
                futures.append(future)

            for i, future in enumerate(futures):
                future.result()

                if self._is_canceled:
                    self.encoding_canceled.emit()
                else:
                    self.encoding_completed.emit(i)  # Emit the signal with the row index

    def shutdown(self):
        self._is_canceled = True
        # Terminate all subprocesses
        for process in self.processes:
            process.terminate()
            process.wait()

    def cancel_encoding(self):
        self._is_canceled = True
        self.shutdown()

    def execute_ffmpeg(self, command, row_index):
        startupinfo = STARTUPINFO()
        startupinfo.dwFlags |= STARTF_USESHOWWINDOW
        try:
            # Process the FFmpeg command and capture the output
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                startupinfo=startupinfo,
                encoding='utf-8',  # Specify encoding directly
                errors='replace',  # Handle decoding errors
                text=True  # Use text mode
            )

            self.processes.append(process)
            self.start_times[row_index] = datetime.now()
            while True:
                line = process.stdout.readline()
                if not line:
                    break

                if self._is_canceled:
                    break

                # Start the elapsed timer only when encoding has started for the video item
                if not self.started_encoding[row_index]:
                    self.started_encoding[row_index] = True
                    self.start_times[row_index] = datetime.now()

                fps_match = re.search(r'(\d+\.?\d*)\sfps', line)
                if fps_match:
                    fps = float(fps_match.group(1))
                    elapsed_time = (datetime.now() - self.start_times[row_index]).total_seconds()
                    if elapsed_time > 0:
                        fps = fps / elapsed_time
                    self.fps_updated.emit(row_index, fps)

                if self.started_encoding[row_index]:
                    self.elapsed_times[row_index] = int((datetime.now() - self.start_times[row_index]).total_seconds())

                # Emit the console output line directly to the main GUI
                self.console_output_updated.emit(line.strip())  # Emitting the stripped output line

                frame_match = re.search(r'frame=\s*(\d+)', line)
                if frame_match:
                    self.processed_frames[row_index] = int(frame_match.group(1))

            process.wait()

            # Emit a signal indicating the task for row_index is completed
            self.encoding_completed.emit(row_index)

        except Exception as e:
            # Handle exceptions (e.g., log the error)
            print(f"An error occurred: {e}")
        
    def get_processed_frames(self, row):
        # Return the number of processed frames for the task at the specified row
        return self.processed_frames[row]
#endregion

#region About
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle('About Simple FFMPEG Video Converter')
        self.resize(1080, 400)
      
        # Apply the specific dark style directly to this dialog
        self.setStyleSheet(ABOUT_DARK_STYLE)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        label = QLabel(self.format_about_text(), self)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        button = QPushButton('OK', self)
        button.clicked.connect(self.accept)
        layout.addWidget(button)
        
        self.setLayout(layout)


    def format_about_text(self):
        return (
            'Note: This application is a work in progress, and not all functions work correctly.\n\n'
            'Version: 1.0\n\n'
            'Key Features:\n'
            '- GUI Interface for easy interaction\n'
            '- Concurrent Video Encoding for improved efficiency\n'
            '- Live Encoding Progress display with Elapsed Time, FPS, and Time Remaining\n\n'
            '- In your commands, ensure placeholders are formatted like "<input>" and "<output>" to automatically handle file paths from the user interface.\n\n'
            
            'Example of Customizing a Command:\n'
            'Suppose you want to encode a video using NVIDIA hardware acceleration for high quality. Start with this base command and adjust accordingly:\n\n'
            'ffmpeg -y -hwaccel cuvid -i "<input>" -c:v h264_nvenc -preset slow -qp 18 -c:a aac -b:a 192k "<output>"\n\n'
            
            'More Examples:\n'
            '1. Copy the audio without encoding while encoding video with x264 medium preset:\n\n'
            'ffmpeg -i "<input>" -c:v libx264 -preset medium -c:a copy "<output>"\n\n'
            
            '2. Encode video with x264 medium preset and AAC audio encoding:\n\n'
            'ffmpeg -i "<input>" -c:v libx264 -preset medium -crf 23 -c:a aac "<output>"\n\n'

            'Troubleshooting:\n'
            'If conversion fails, check the console for output and copy any errors. Then, post them in the forums under the help topic for assistance.\n\n'



        )


    # Usage example:
    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec_()
#endregion

#region ui
class VideoEncoder(QMainWindow):
    def __init__(self):
        super().__init__()
        global current_version
        
        self.is_dark_mode = True  # Start with dark mode enabled
        self.setStyleSheet(DARK_STYLE)  
        
        self.setWindowIcon(QtGui.QIcon('Encoding_icon.ico'))
        self.setWindowTitle(f"Simple FFMPEG Video Converter {current_version}")
        self.setGeometry(100, 100, 1000, 800)

        self.init_ui()
        self.check_and_install_ffmpeg()

        self.is_dark_mode = True  # Start with dark mode enabled
        self.setStyleSheet(DARK_STYLE)  


        # Redirect stdout and stderr to update_console_output.
        self.redirector = StreamRedirector()
        self.redirector.text_written.connect(self.update_console_output)
        sys.stdout = self.redirector
        sys.stderr = self.redirector

    def init_ui(self):
        # Create the action
        self.about_action = QAction("About", self)


        self.input_folder = ''
        self.settings = QSettings("MyCompany", "Simple FFMPEG Video Converter")
        self.input_folder = self.settings.value("input_folder", "")
        self.output_folder = self.settings.value("output_folder", "")
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        #update label----------------------------------
         # Horizontal layout for the top of the window
        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        # Spacer to push the update label to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        top_layout.addSpacerItem(spacer)
         # Update label setup
        self.update_label = QLabel("", self)
        self.update_label.setStyleSheet("color: red; font-weight: bold;")
        self.update_label.setVisible(False)  # Start with the label hidden
        top_layout.addWidget(self.update_label)
        #update label----------------------------------

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        # Set tab position to top (optional, in case it was changed elsewhere)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab_widget.addTab(self.tab1, "Encoder")
        self.tab_widget.addTab(self.tab2, "Console")
        self.tab_widget.addTab(self.tab3, "Settings")

        self.init_tab1_ui()
        self.init_tab2_ui()
        self.init_tab3_ui()
        #Create the menu bar and menus as instance variables
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu("File")
        self.help_menu = self.menubar.addMenu("Help")
        # Create actions for the menu items as instance variables
        self.open_action = QAction("Open", self)
        self.open_action.triggered.connect(self.select_input_files)
        self.file_menu.addAction(self.open_action)
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.showAboutDialog)
        self.restore_commands_action = QAction("Restore Commands", self)
        self.restore_commands_action.triggered.connect(self.restore_commands)  # This is correct if the method is intended to reset the commands
        self.help_menu.addAction(self.restore_commands_action)
        self.help_menu.addAction(self.about_action)


#region tab1
    def init_tab1_ui(self):
        layout = QVBoxLayout(self.tab1)
    
        input_group = QGroupBox("Input", self.tab1)
        form_layout = QFormLayout(input_group)

        self.input_button = QPushButton("Select Files", self.tab1)
        form_layout.addRow("Files:", self.input_button)
        self.table_widget = QTableWidget(self.tab1)
        self.table_widget.setColumnCount(5)  
        self.table_widget.setHorizontalHeaderLabels(["Input File", "Elapsed Time", "FPS", "Time Remaining", "Status"])
        output_group = QGroupBox("Output", self.tab1)
        form_layout = QFormLayout(output_group)
        self.output_textbox = QLineEdit(self.tab1)
        self.output_button = QPushButton("Select Folder", self.tab1)
        form_layout.addRow("Folder:", self.output_textbox)
        form_layout.addRow("", self.output_button)
        settings_group = QGroupBox("Settings", self.tab1)

        grid_layout = QGridLayout(settings_group)
        self.format_combobox = QComboBox(self.tab1)
        self.format_combobox.setEditable(True)
        self.format_combobox.addItems(["avi", "mp4", "mkv", "ts"])  # Add items to the combobox
        self.format_combobox.setToolTip(
                                        "Container Formats:\n"
                                        "- MP4: Often used with H.264/HEVC codecs.\n"
                                        "- MKV: Supports various codecs and is flexible in handling multiple streams.\n"
                                        "- AVI: Can use various codecs but is less efficient in terms of file size.\n"
                                        "- MOV: Commonly used with the Apple ecosystem."
                                    )

        self.Simultaneous_Encodes_combobox = QComboBox(self.tab1)
        self.Simultaneous_Encodes_combobox.setEditable(True)
        self.Simultaneous_Encodes_combobox.setToolTip("Select the number of simultaneous encodes. Nvidia GPUs support up to 8 encodes; exceeding this will cause failure. AMD GPU limit: N/A.")

        self.Simultaneous_Encodes_combobox.addItems(simultaneous_encodes)
        
        self.custom_command_combobox = QComboBox(self.tab1)
        self.custom_command_combobox.setEditable(True)
        self.custom_command_combobox.setToolTip(
                                        "Video Compression Codecs:\n"
                                        "H.264 (AVC) - A popular codec for high-quality video with good compression. Commonly used in MP4 files.\n"
                                        "H.265 (HEVC) - A newer codec providing better compression and quality compared to H.264. Ideal for 4K and high-definition video.\n"
                                        "VP8/VP9 - Developed by Google, often used in web videos (e.g., YouTube). VP9 offers better compression than VP8.\n"
                                        "AV1 - A newer codec designed to provide even better compression than HEVC. It’s gaining traction but still not as widely supported."
        )

        

        grid_layout.addWidget(QLabel("Format:"), 0,0)
        grid_layout.addWidget(self.format_combobox,0,1)
   
        grid_layout.addWidget(QLabel("Simultaneous"), 1, 0)
        grid_layout.addWidget(self.Simultaneous_Encodes_combobox, 1, 1)

        grid_layout.addWidget(QLabel("FFmpeg Command"), 2, 0)
        grid_layout.addWidget(self.custom_command_combobox, 2, 1)

        self.encode_button = QPushButton("Encode Videos", self.tab1)
        self.cancel_button = QPushButton("Cancel Encode", self.tab1)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.encode_button)
        button_layout.addWidget(self.cancel_button)
        layout.addWidget(input_group)
        layout.addWidget(self.table_widget)
        layout.addWidget(output_group)
        layout.addWidget(settings_group)
        layout.addLayout(button_layout)

        self.input_button.clicked.connect(self.select_input_files)
        self.output_button.clicked.connect(self.select_output_folder)
        self.encode_button.clicked.connect(self.encode_videos)


        self.start_time = None
        self.total_video_duration = 0
        self.simultaneous_encodes = 0
        self.fps_queue = []
        self.frame_count_queue = []
        self.current_fps = 25
        self.timer = QtCore.QTimer(self)
        self.cancel_button.setEnabled(False)  # Initially disable the cancel button
#endregion


#region tab2

    def init_tab2_ui(self):
        layout = QVBoxLayout(self.tab2)
        label2 = QLabel("Console", self.tab2)
        layout.addWidget(label2)
        
        # Add a horizontal layout to contain the buttons
        button_layout = QHBoxLayout()

        # Add a button to check available FFmpeg hardware acceleration
        check_ffmpeg_button = QPushButton("Check Hardware Acceleration", self.tab2)
        check_ffmpeg_button.clicked.connect(self.check_hwaccl)
        button_layout.addWidget(check_ffmpeg_button)

        # Add a button to check available FFmpeg encoders
        check_encoders_button = QPushButton("Check Encoders", self.tab2)
        check_encoders_button.clicked.connect(self.check_encoders)
        button_layout.addWidget(check_encoders_button)

        # Add a button to check available FFmpeg decoders
        check_decoders_button = QPushButton("Check Decoders", self.tab2)
        check_decoders_button.clicked.connect(self.check_decoders)
        button_layout.addWidget(check_decoders_button)

        layout.addLayout(button_layout)

        # Adding a QPlainTextEdit that expands to fill the available space in Tab 2
        self.line_edit_tab2 = QPlainTextEdit(self.tab2)  # Use QPlainTextEdit instead of QLineEdit
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.line_edit_tab2.setSizePolicy(size_policy)
        layout.addWidget(self.line_edit_tab2)



#endregion


#region tab 3 settings
    def init_tab3_ui(self):
        layout = QVBoxLayout(self.tab3)

        # Create a group box for managing commands
        command_group = QGroupBox("Manage Commands", self.tab3)
        command_layout = QVBoxLayout()

        # Create a QListWidget to display commands
        self.command_list = QListWidget(self.tab3)
        self.command_list.addItems(example_commands)

        # Create buttons for adding, editing, and removing commands
        add_button = QPushButton("Add Command", self.tab3)
        edit_button = QPushButton("Edit Command", self.tab3)
        remove_button = QPushButton("Remove Command", self.tab3)
        import_button = QPushButton("Import Commands", self.tab3)
        export_button = QPushButton("Export Commands", self.tab3)

        # Add buttons to the layout
        command_layout.addWidget(import_button)
        command_layout.addWidget(export_button)
        command_layout.addWidget(self.command_list)
        command_layout.addWidget(add_button)
        command_layout.addWidget(edit_button) 
        command_layout.addWidget(remove_button)

        command_group.setLayout(command_layout)
        layout.addWidget(command_group)

        # Connect button signals to slots
        add_button.clicked.connect(self.add_command)
        edit_button.clicked.connect(self.edit_command)
        remove_button.clicked.connect(self.remove_command)
        import_button.clicked.connect(self.import_commands)
        export_button.clicked.connect(self.export_commands)

        # Read previous settings using QSettings
        self.settings = QSettings("MyCompany", "VideoEncoder")
        #self.settings.clear()
        #self.settings.sync()

        previous_format = self.settings.value("format", "")
        previous_simultaneous_encodes = self.settings.value("simultaneous_encodes", "1")

        previous_output_folder = self.settings.value("output_folder", "")

        previous_input_folder = self.settings.value("input_folder", "")  # Load the saved input folder
        
        self.format_combobox.setCurrentText(previous_format)
        self.Simultaneous_Encodes_combobox.setCurrentText(previous_simultaneous_encodes)
        self.output_textbox.setText(previous_output_folder)
        self.input_folder = previous_input_folder  # Set the output textbox to the saved value
  

        self.load_commands()

    def import_commands(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Commands", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'r') as file:
                json_commands = json.load(file)
                self.example_commands = json_commands
                self.save_commands()  # Save to QSettings
                self.load_commands()  # Update UI
                self.update_combobox() # Refresh combobox

    def update_combobox(self):
        self.custom_command_combobox.clear()
        self.custom_command_combobox.addItems(self.example_commands)


    def export_commands(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Commands", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'w') as file:
                json.dump(self.example_commands, file, indent=4)

        # Ensure data is written to storage
        self.settings.sync()
    
    def restore_commands(self):
        global example_commands
        self.example_commands = example_commands
        self.command_list.clear()
        self.command_list.addItems(self.example_commands)
        self.save_commands()  # Save to QSettings 
        self.update_combobox() # Refresh combobox

       
    def save_commands(self):
        # Serialize the list to a JSON string and save it
        json_commands = json.dumps(self.example_commands)
        self.settings.setValue("commands_list", json_commands)
        self.settings.sync()  # Ensure data is written to storage

    def load_commands(self):
        # Deserialize the JSON string back to a list
        json_commands = self.settings.value("commands_list", "[]")
        if json_commands == "[]":
            self.example_commands = ['Default Command 1', 'Default Command 2']
        else:
            self.example_commands = json.loads(json_commands)
        self.command_list.clear()
        self.command_list.addItems(self.example_commands)
        self.custom_command_combobox.addItems(self.example_commands)
        previous_custom_command_combobox = self.settings.value("custom_command", "")
        self.custom_command_combobox.setCurrentText(previous_custom_command_combobox)

    def add_command(self):
        command, ok = QInputDialog.getText(self, "Add Command", "Enter the command:")
        if ok and command:
            self.command_list.addItem(command)
            self.example_commands.append(command)
            self.save_commands()
            self.load_commands()

    def edit_command(self):
        selected_item = self.command_list.currentItem()
        if selected_item:
            new_command, ok = QInputDialog.getText(self, "Edit Command", "Edit the command:", text=selected_item.text())
            if ok and new_command:
                idx = self.command_list.row(selected_item)
                self.example_commands[idx] = new_command
                selected_item.setText(new_command)
                self.save_commands()
                self.load_commands()

    def remove_command(self):
        selected_item = self.command_list.currentItem()
        if selected_item:
            confirm = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete this command?",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                idx = self.command_list.row(selected_item)
                if idx < len(self.example_commands):
                    del self.example_commands[idx]
                    self.command_list.takeItem(idx)
                    self.save_commands()
                    self.load_commands()
                else:
                    print("Error: Index out of range")
#endregion


#endregion

    def check_hwaccl(self):
        self.line_edit_tab2.clear()
        # This method checks available FFmpeg encoders and decoders and displays the results in the console
        console_text = ""
        try:
            process = subprocess.Popen(["ffmpeg", "-hide_banner", "-hwaccels"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            console_text += "Hardware Accelerators:\n" + stdout.decode() + "\n"
            console_text += "Errors (if any):\n" + stderr.decode() + "\n"
        except Exception as e:
            console_text = f"Error: {str(e)}"
        
        # Display the results in the console
        self.line_edit_tab2.appendPlainText(console_text)

    def check_encoders(self):
        self.line_edit_tab2.clear()
        # This method checks available FFmpeg encoders and decoders and displays the results in the console
        console_text = ""
        try:
            process = subprocess.Popen(["ffmpeg", "-hide_banner", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            console_text += "Hardware Accelerators:\n" + stdout.decode() + "\n"
            console_text += "Errors (if any):\n" + stderr.decode() + "\n"
        except Exception as e:
            console_text = f"Error: {str(e)}"
        
        # Display the results in the console
        self.line_edit_tab2.appendPlainText(console_text)

    def check_decoders(self):
        self.line_edit_tab2.clear()
        # This method checks available FFmpeg encoders and decoders and displays the results in the console
        console_text = ""
        try:
            process = subprocess.Popen(["ffmpeg", "-hide_banner", "-decoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            console_text += "Hardware Accelerators:\n" + stdout.decode() + "\n"
            console_text += "Errors (if any):\n" + stderr.decode() + "\n"
        except Exception as e:
            console_text = f"Error: {str(e)}"
        
        # Display the results in the console
        self.line_edit_tab2.appendPlainText(console_text)


#region ffmpeg
    def download_and_install_ffmpeg(self):
        print("Downloading FFmpeg...")

        # New download URL
        download_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

        # Rest of the code remains the same
        download_path = os.path.join(os.getcwd(), "ffmpeg.zip")

        # Create a progress dialog
        progress_dialog = QProgressDialog("Downloading FFmpeg...", "Cancel", 0, 100)
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setWindowTitle("Download Progress")
        progress_dialog.setAutoClose(True)

        def reporthook(blocknum, blocksize, totalsize):
            nonlocal progress_dialog

            # Calculate the download progress
            progress = min(int(blocknum * blocksize * 100 / totalsize), 100)

            # Update the progress dialog
            progress_dialog.setValue(progress)

        urllib.request.urlretrieve(download_url, download_path, reporthook=reporthook)

        # Close the progress dialog
        progress_dialog.close()

        print("Extracting FFmpeg...")

        # Extract the downloaded zip file directly to C:\ffmpeg\bin
        ffmpeg_bin_path = "C:\\ffmpeg\\bin"

        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                try:
                    file_info.filename = os.path.basename(file_info.filename)  # Get only the filename
                    zip_ref.extract(file_info, ffmpeg_bin_path)
                except Exception as e:
                    #print(f"Error extracting file: {file_info.filename}")
                    #print(f"Exception: {e}")
                    continue


        # Clean up: remove the downloaded zip file
        os.remove(download_path)

        # Add the FFmpeg bin directory to the system's PATH
        self.add_to_path(ffmpeg_bin_path)

        # Print a message
        print("FFmpeg installed successfully.")


    def check_and_install_ffmpeg(self): 
        if not self.is_ffmpeg_installed():
            message = (
                "FFmpeg is not installed or not found in the system's PATH.\n\n"
                "FFmpeg is required for this application to function properly. "
                "Do you want to download and install it to 'C:\\ffmpeg\\bin'?"
            )

            reply = QMessageBox.question(self, 'FFmpeg Not Found', message,
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.download_and_install_ffmpeg()
                print("FFmpeg installed successfully.")
            else:
                print("User chose not to install FFmpeg.")
                # Handle the case where the user chooses not to install FFmpeg

    def is_ffmpeg_installed(self):
        try:
            # Use subprocess to run the command 'ffmpeg -version'
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print("FFmpeg is already installed.")
            return True
        except FileNotFoundError:
            print("FFmpeg is not installed.")
            return False
        
    def add_to_path(self, program_path: str):
        """Takes in a path to a program and adds it to the user-specific path"""
        if os.name == "nt":  # Windows systems
            import winreg  # Allows access to the windows registry
            import ctypes  # Allows interface with low-level C API's

            with winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER) as root:  # Get the current user registry
                with winreg.OpenKey(root, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:  # Go to the environment key
                    existing_path_value = winreg.QueryValueEx(key, "PATH")[0]  # Grab the current path value

                    # Check if the path is already in the existing value
                    if program_path not in existing_path_value:
                        new_path_value = existing_path_value + ";" + program_path
                        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path_value)  # Update the path

                # Tell other processes to update their environment
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x1A
                SMTO_ABORTIFHUNG = 0x0002
                result = ctypes.c_long()
                SendMessageTimeoutW = ctypes.windll.user32.SendMessageTimeoutW
                SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, u"Environment", SMTO_ABORTIFHUNG, 5000, ctypes.byref(result), )
        else:  # If the system is *nix
            print("This method is intended for Windows systems. For *nix systems, consider modifying the PATH manually.")

        print(f"Added {program_path} to user path, please restart the shell for changes to take effect")

#endregion


#region menu
    def contextMenuEvent(self, event):
        # Ensure the event is within the bounds of the QTableWidget
        if not self.table_widget.underMouse():
            return

        contextMenu = QMenu(self)
        
        # Map the event position to the viewport of the table widget
        tablePos = self.table_widget.viewport().mapFromGlobal(event.globalPos())
        row = self.table_widget.rowAt(tablePos.y())

        # Add 'Delete Row' action if the click is on a valid row
        deleteAction = None
        if row >= 0:
            # Optionally select the row that was right-clicked
            self.table_widget.selectRow(row)

            deleteAction = contextMenu.addAction("Remove Selected")

        # Add 'Remove All' action
        removeAllAction = contextMenu.addAction("Remove All")

        action = contextMenu.exec_(event.globalPos())

        if action == deleteAction and deleteAction is not None:
            self.delete_row(row)
        elif action == removeAllAction:
            self.remove_all_rows()

    def delete_row(self, row):
        # Confirm before deleting
        reply = QMessageBox.question(self, 'Remove Selected', 'Are you sure you want to delete this row?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.table_widget.removeRow(row)

    def remove_all_rows(self):
        # Confirm before removing all rows
        reply = QMessageBox.question(self, 'Remove All Rows', 'Are you sure you want to remove all rows?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.table_widget.setRowCount(0)

#endregion


    def showAboutDialog(self):
            dialog = AboutDialog(self)
            dialog.exec_()


    @QtCore.pyqtSlot(str)
    def update_console_output(self, line):
        self.line_edit_tab2.appendPlainText(line)  # Use appendPlainText to add new lines
        

    def select_input_files(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Files", self.input_folder, "Video Files (*.mp4;*.mkv;*.avi;*.mov;*.wmv;*.flv;*.webm;*.mpeg;*.mpg;*.m4v;*.ts)")
        if file_names:
            self.input_folder = os.path.dirname(file_names[0])
            self.settings.setValue("input_folder", self.input_folder)
            current_row_count = self.table_widget.rowCount()
            new_row_count = current_row_count + len(file_names)
            self.table_widget.setRowCount(new_row_count)

            for i, file_name in enumerate(file_names, start=current_row_count):
                item = QTableWidgetItem(file_name)
                self.table_widget.setItem(i, 0, item)
                elapsed_time_item = QTableWidgetItem("--:--:--")
                self.table_widget.setItem(i, 1, elapsed_time_item)
                fps_item = QTableWidgetItem("--")
                self.table_widget.setItem(i, 2, fps_item)

            self.table_widget.resizeColumnsToContents()
            self.adjustHorizontalSize()
            
            # Calculate the total width needed for all columns
            total_width = self.table_widget.verticalHeader().width()
            total_width += self.table_widget.horizontalScrollBar().height()
            for i in range(self.table_widget.columnCount()):
                total_width += self.table_widget.columnWidth(i)
                

    def select_output_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Select Folder", self.output_folder)
        if folder_name:
            self.output_textbox.setText(folder_name)
            self.output_folder = folder_name
            self.settings.setValue("output_folder", self.output_folder)

    def adjustHorizontalSize(self):
        # Calculate the total width needed for all columns
        total_width = self.table_widget.verticalHeader().width() + 55  # border or spacing pixels
        for i in range(self.table_widget.columnCount()):
            total_width += self.table_widget.columnWidth(i)

        # Optionally add some width for vertical scrollbar
        if self.table_widget.verticalScrollBar().isVisible():
            total_width += self.table_widget.verticalScrollBar().width()

        # Resize the window width
        self.resize(total_width, self.height())


    def encode_videos(self, selected_row):
        self.frame_count = 0
        input_files = []
        self.elapsed_time = 0
        self.elapsed_timer = QtCore.QTimer(self)
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)
        self.elapsed_timer.start(1000)
        

        # Store current settings in QSettings
        self.settings.setValue("format", self.format_combobox.currentText())
        self.settings.setValue("simultaneous_encodes", self.Simultaneous_Encodes_combobox.currentText())
        self.settings.setValue("output_folder", self.output_textbox.text())
        self.settings.setValue("custom_command", self.custom_command_combobox.currentText())
        self.settings.setValue("input_folder", self.input_folder)  # Save the input folder in settings

        rows = self.table_widget.rowCount()

        for row in range(rows):
            self.table_widget.setItem(row, 4, QTableWidgetItem(""))

        # Populate input_files list with selected files
        for row_index in range(self.table_widget.rowCount()):
            input_files.append(self.table_widget.item(row_index, 0).text())

        output_folder = self.output_textbox.text()
        self.simultaneous_encodes = int(self.Simultaneous_Encodes_combobox.currentText())

        # Disable UI elements
        self.input_button.setEnabled(False)
        self.output_button.setEnabled(False)
        self.output_textbox.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.Simultaneous_Encodes_combobox.setEnabled(False)
        self.encode_button.setEnabled(False)

        # Clear queues
        self.fps_queue.clear()
        self.frame_count_queue.clear()

        # Start encoding thread
        self.encoding_thread = VideoEncoderThread(input_files, output_folder, self.simultaneous_encodes, self.format_combobox, self.custom_command_combobox)
        self.encoding_thread.fps_updated.connect(self.update_fps_for_row)
        self.encoding_thread.encoding_complete.connect(self.encoding_complete)
        self.encoding_thread.encoding_progress_updated.connect(self.update_encoding_progress)
        self.encoding_thread.encoding_completed.connect(self.encoding_completed_handler)
        self.encoding_thread.console_output_updated.connect(self.update_console_output)
        self.cancel_button.clicked.connect(self.cancel_encoding_thread)
        self.encoding_thread.start()

        self.start_time = time.time()


    def update_encoding_progress(self, row, status):
        self.table_widget.setItem(row, 4, QTableWidgetItem(status))
        
    def update_elapsed_time(self):
        self.elapsed_time += 1
        self.timer.start(500)
        hours = self.elapsed_time // 3600
        minutes = (self.elapsed_time % 3600) // 60
        seconds = self.elapsed_time % 60
        
        # update elapsed time in table
        for row in range(self.table_widget.rowCount()):
            if self.encoding_thread.started_encoding[row] and not self.encoding_thread.finished_encoding[row]:
          
                item = self.table_widget.item(row, 1)
                elapsed_time = item.data(QtCore.Qt.UserRole)
                if elapsed_time is None:
                    elapsed_time = 0
                elapsed_time += 1
                item.setText(f"{elapsed_time // 3600:02d}:{(elapsed_time % 3600) // 60:02d}:{elapsed_time % 60:02d}")
                item.setData(QtCore.Qt.UserRole, elapsed_time)
            
    @QtCore.pyqtSlot(int, float)  # Updated slot signature to accept both int and float
    def update_frame_and_fps_for_row(self, row, value):
        # Use the 'value' parameter to determine whether it's FPS or frame count update
        if isinstance(value, int):
            # Update the frame count for the corresponding row in the table widget
            item = self.table_widget.item(row, 1)
            item.setText(str(value))
        elif isinstance(value, float):
            # Update the FPS for the corresponding row in the table widget
            item = self.table_widget.item(row, 2)
            item.setText(str(value))

    @QtCore.pyqtSlot(int, float)
    def update_fps_for_row(self, row, fps):
        # Update the FPS for the corresponding row in the table widget
        fps_item = self.table_widget.item(row, 2)
        if fps_item is None:
            return  # Exit the method if the item does not exist

        fps_item.setText(f"{fps:.2f}")  # Keep FPS in float for more precision

        # Calculate remaining time
        total_frames = self.get_total_frames(row)
        
        # Access the processed_frames from the encoding_thread instance
        processed_frames = self.encoding_thread.get_processed_frames(row)  

        if total_frames and fps != 0:  # Make sure fps is not zero before performing the division
            remaining_frames = total_frames - processed_frames
            remaining_time = remaining_frames / fps

            # Update the remaining time in the table widget
            time_item = self.table_widget.item(row, 3)
            if time_item is None:
                time_item = QTableWidgetItem()
                self.table_widget.setItem(row, 3, time_item)

            # Format and set the remaining time
            hours, minutes, seconds = int(remaining_time // 3600), int((remaining_time % 3600) // 60), int(remaining_time % 60)
            time_item.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.table_widget.resizeColumnsToContents()


    def get_total_frames(self, row):
        # Get the total number of frames in the video using FFprobe
        input_file = self.table_widget.item(row, 0).text()
        duration = get_video_duration(input_file)
        if duration is not None:
            fps = self.current_fps
            return int(duration * fps)
        return None

    def cancel_encoding_thread(self,row):
        if hasattr(self, "encoding_thread") and self.encoding_thread.isRunning():
            self.encoding_thread.cancel_encoding()
            self.encoding_thread.terminate()  # Terminate the thread immediately without waiting
            self.elapsed_timer.stop()
            self.input_button.setEnabled(True)
            self.output_button.setEnabled(True)
            self.output_textbox.setEnabled(True)
    
            self.Simultaneous_Encodes_combobox.setEnabled(True)
            self.encode_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.reset_ui()
            #self.status_label.setText("Encoding canceled")
            for row in range(self.table_widget.rowCount()):
                self.table_widget.setItem(row, 1, QTableWidgetItem("--:--:--"))  # Reset elapsed time (assuming it's column 1)
                self.table_widget.setItem(row, 3, QTableWidgetItem("--:--:--"))  # Reset time remaining (assuming it's column 3)

    @QtCore.pyqtSlot(int)
    def encoding_completed_handler(self, row):
        # Update column 5 for the corresponding row to "Done" when an encoding is completed
        self.table_widget.setItem(row, 4, QTableWidgetItem("Done"))
        self.encoding_thread.finished_encoding[row] = True
        self.cancel_button.setEnabled(False)
        self.encode_button.setEnabled(True)
        self.reset_ui()


    def encoding_complete(self):
        self.elapsed_timer.stop()
        self.timer.stop()
        self.input_button.setEnabled(True)
        self.output_button.setEnabled(True)
        self.output_textbox.setEnabled(True)

        self.Simultaneous_Encodes_combobox.setEnabled(True)
        self.encode_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.reset_ui()
        
        # Cleanup the encoding thread
        if hasattr(self, "encoding_thread") and self.encoding_thread.isRunning():
            self.encoding_thread.wait()  # Wait for the encoding thread to finish


    def reset_ui(self):
       
        self.input_button.setEnabled(True)
        self.output_button.setEnabled(True)
        self.output_textbox.setEnabled(True)
        self.Simultaneous_Encodes_combobox.setEnabled(True)
        self.encode_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

    def closeEvent(self, event):
        # Check if the encoding thread is running and cancel it
        if hasattr(self, "encoding_thread") and self.encoding_thread.isRunning():
            self.encoding_thread.cancel_encoding()
            self.encoding_thread.wait()  # Wait for the encoding thread to finish

        # Call the default close event to allow the application to exit
        super().closeEvent(event)

def my_exception_hook(exctype, value, tb):
    # Enhanced function to log detailed unhandled exceptions with traceback.
    error_message = ''.join(traceback.format_exception(exctype, value, tb))
    sys.stderr.write(error_message)  # Redirect detailed exceptions to stderr.

# Replace the default exception hook with our custom function.
sys.excepthook = my_exception_hook

if __name__ == "__main__":
    app = QApplication(sys.argv)
    bold_font = QFont()
    bold_font.setBold(True)
    app.setFont(bold_font) 
    window = VideoEncoder()
    window.show()
    sys.exit(app.exec_())