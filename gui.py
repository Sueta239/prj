import os
os.environ.pop("XDG_SESSION_TYPE", None)
os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
import subprocess
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QFileDialog, QSplitter, QListWidget,
    QListWidgetItem, QSlider, QLineEdit, QSpinBox, QFrame
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

STEPS = [
    ("File Splitting", "csv_split.py"),
    ("Retrieve CAS Information", "proj_1.py"),
    ("Patent Search", "proj_2.py"),
    ("Annotations and Translation", "proj_3.py"),
    ("Scoring", "proj_4.py"),
    ("Final Selection", "proj_5.py"),
    ("Filter by Accuracy", "filter_by_accuracy.py"),
    ("Visualization", "info.py")
]

class ScriptRunner(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, tasks, file_path=None, accuracy=0.8, workers=8):
        super().__init__()
        self.tasks = tasks
        self.file_path = file_path
        self.accuracy = accuracy
        self.workers = workers

    def run(self):
        for label, script in self.tasks:
            self.output_signal.emit(f"▶️ {label}...")
            cmd = [sys.executable, script]
            if script == "csv_split.py" and self.file_path:
                cmd.append(self.file_path)
            if script == "filter_by_accuracy.py":
                cmd.append(str(self.accuracy))
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                self.output_signal.emit(line.rstrip())
            proc.wait()
        self.output_signal.emit("✔ All steps completed")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PatentFinder GUI")
        self.resize(1000, 700)
        self.setStyleSheet("""
            QWidget { background: #2e2e2e; color: #ddd; font-family: 'Consolas', monospace; }
            QPushButton { background: #4a90e2; color: white; border: none; padding: 8px 12px; border-radius: 4px; }
            QPushButton:hover { background: #357ab8; }
            QListWidget { background: #3b3b3b; border: none; }
            QTextEdit { background: #1e1e1e; border: none; padding: 4px; }
            QSlider::groove:horizontal { background: #555; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #4a90e2; width: 14px; margin: -4px 0; border-radius: 7px; }
            QLineEdit, QSpinBox { background: #3b3b3b; border: 1px solid #555; border-radius: 4px; padding: 4px; color: #ddd; }
        """)

        splitter = QSplitter(Qt.Horizontal)

        # Левый сайдбар
        sidebar = QWidget()
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10,10,10,10)
        sb_layout.setSpacing(15)
        sb_layout.addWidget(QLabel("Processing Steps:"))
        self.steps_list = QListWidget()
        for label, script in STEPS:
            item = QListWidgetItem(label)
            item.setCheckState(Qt.Unchecked)
            item.script = script
            self.steps_list.addItem(item)
        sb_layout.addWidget(self.steps_list)

        sb_layout.addWidget(QLabel("Accuracy Threshold:"))
        ah_layout = QHBoxLayout()
        self.accuracy_slider = QSlider(Qt.Horizontal)
        self.accuracy_slider.setRange(0,100)
        self.accuracy_slider.setValue(80)
        self.accuracy_slider.valueChanged.connect(self.update_accuracy_label)
        self.accuracy_label = QLabel(f"{self.accuracy_slider.value()/100:.2f}")
        ah_layout.addWidget(self.accuracy_slider,1)
        ah_layout.addWidget(self.accuracy_label)
        sb_layout.addLayout(ah_layout)

        sb_layout.addWidget(QLabel("Max Workers:"))
        wh_layout = QHBoxLayout()
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1,10)
        self.workers_spin.setValue(8)
        self.workers_spin.valueChanged.connect(self.update_workers_label)
        self.workers_label = QLabel(str(self.workers_spin.value()))
        wh_layout.addWidget(self.workers_spin)
        wh_layout.addWidget(self.workers_label)
        sb_layout.addLayout(wh_layout)
        sb_layout.addStretch()
        splitter.addWidget(sidebar)

        # Правый контент
        content = QWidget()
        ct_layout = QVBoxLayout(content)
        ct_layout.setContentsMargins(10,10,10,10)

        # INFO
        info_layout = QHBoxLayout()
        info_label = QLabel("INFO")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size:20px; font-weight:bold; color:#3498db;")
        info_label.setToolTip(
            "<span style='font-size:12px;color:black;'>"
            "Файл должен быть CSV и содержать столбец 'Наименование продукции' с CAS-номером в формате <br>"
            "CAS 13463-67-7, CAS: 13463-67-7 или (CAS 13463-67-7).<br>"
            "Остальные данные будут проигнорированы, но не нарушат работу приложения."
            "</span>"
        )
        info_layout.addWidget(info_label)
        ct_layout.addLayout(info_layout)

        # Файл и кнопки
        path_layout = QHBoxLayout()
        self.file_btn = QPushButton("Select CSV")
        self.file_btn.clicked.connect(self.select_file)
        self.file_label = QLabel("No file selected")
        path_layout.addWidget(self.file_btn)
        path_layout.addWidget(self.file_label)
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_config)
        path_layout.addWidget(self.save_btn)
        ct_layout.addLayout(path_layout)

        # Ключевые слова
        kw_layout = QHBoxLayout()
        kw_layout.addWidget(QLabel("Keywords:"))
        self.keywords = QLineEdit()
        self.keywords.setPlaceholderText("write keywords here")
        kw_layout.addWidget(self.keywords)
        ct_layout.addLayout(kw_layout)

        # Кнопка запуска
        self.run_btn = QPushButton("Run Steps")
        self.run_btn.clicked.connect(self.run_tasks)
        ct_layout.addWidget(self.run_btn)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        ct_layout.addWidget(separator)

        # Выводы
        ct_layout.addWidget(QLabel("Output:"))
        self.main_output = QTextEdit()
        self.main_output.setReadOnly(True)
        ct_layout.addWidget(self.main_output)

        ct_layout.addWidget(QLabel("Progress:"))
        self.script_output = QTextEdit()
        self.script_output.setReadOnly(True)
        self.script_output.setFixedHeight(50)
        ct_layout.addWidget(self.script_output)

        splitter.addWidget(content)
        splitter.setSizes([300,700])
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)

        self.load_config()

    def update_accuracy_label(self, v):
        self.accuracy_label.setText(f"{v/100:.2f}")

    def update_workers_label(self, v):
        self.workers_label.setText(str(v))

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if path:
            self.file_path = path
            self.file_label.setText(path)
            self.main_output.append(f"✔ Файл выбран: {path}")

    def run_tasks(self):
        tasks = []
        for idx in range(self.steps_list.count()):
            item = self.steps_list.item(idx)
            if item.checkState() == Qt.Checked:
                tasks.append((item.text(), item.script))
        if not tasks:
            self.main_output.append("❗ No steps selected")
            return
        if any(s == "csv_split.py" for _,s in tasks) and not hasattr(self, 'file_path'):
            self.main_output.append("❗ Please select a file before running")
            return
        acc = self.accuracy_slider.value() / 100.0
        workers = self.workers_spin.value()
        self.start_time = datetime.now()
        self.main_output.append(f"⏱ Start: {self.start_time.strftime('%H:%M:%S')}")
        self.script_output.clear()
        self.runner = ScriptRunner(tasks, getattr(self, 'file_path', None), acc, workers)
        self.runner.output_signal.connect(self.route_output)
        self.runner.finished.connect(self.on_finished)
        self.runner.start()

    def route_output(self, text):
        if text.startswith("▶️") or text.startswith("❗") or text.startswith("✔"):
            self.main_output.append(text)
        else:
            # self.script_output.setPlainText(text)
            self.script_output.append(text)

    def on_finished(self):
        end_time = datetime.now()
        delta = end_time - self.start_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.main_output.append(
            f"⏱ End: {end_time.strftime('%H:%M:%S')} "
            f"(duration {hours}h {minutes}m {seconds}s)"
        )

    def save_config(self):
        cfg = {
            'first_part_terms': [k.strip() for k in self.keywords.text().split(',') if k.strip()],
            'accuracy_threshold': self.accuracy_slider.value() / 100.0,
            'max_workers': self.workers_spin.value()
        }
        with open('config.json','w',encoding='utf-8') as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        self.main_output.append(f"✔ The settings are saved: {cfg}")

    def load_config(self):
        try:
            data = json.load(open('config.json','r',encoding='utf-8'))
        except:
            data = {}
        if 'first_part_terms' in data:
            self.keywords.setText(', '.join(data['first_part_terms']))
        if 'accuracy_threshold' in data:
            self.accuracy_slider.setValue(int(data['accuracy_threshold']*100))
        if 'max_workers' in data:
            self.workers_spin.setValue(data['max_workers'])

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
