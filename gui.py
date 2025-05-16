import sys
import os
import csv
import json
import shutil
import multiprocessing
import importlib.util
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QPushButton, QTextEdit, QLabel,
    QFileDialog, QCheckBox, QStyleFactory, QHeaderView
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import pyqtSignal, Qt, QTimer

from executor.runner import run_test_case
from executor.BaseTest import BaseTest

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
SESSION_CSV = os.path.join(os.path.dirname(__file__), f'test_results_{TIMESTAMP}.csv')
TESTS_DIR = os.path.join(os.path.dirname(__file__), 'tests')

def process_worker(path, config_queue, result_queue):
    cfg = config_queue.get()
    try:
        if path.endswith('.yaml'):
            result = run_test_case(path)
        else:
            spec = importlib.util.spec_from_file_location('test_module', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            test_cls = next(
                obj for obj in module.__dict__.values()
                if isinstance(obj, type) and issubclass(obj, BaseTest) and obj is not BaseTest
            )
            def live_cb(msg): result_queue.put(msg)
            inst = test_cls(console_output=False, live_cb=live_cb)
            result = inst.run(cfg)

        result_queue.put(f"▶ Running: {os.path.basename(path)}")
        for line in result.get('output', '').splitlines():
            result_queue.put(line)
        result_queue.put(f"🔖 Comment: {result.get('comment','')}")
        result_queue.put({'csv': result})

    except Exception:
        import traceback
        result_queue.put(traceback.format_exc())

    finally:
        result_queue.put(None)

class TestRunnerGUI(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOC Automation Test Runner")
        self.resize(1000, 600)

        os.environ['SESSION_CSV'] = SESSION_CSV

        self.processes = []
        self.config_queues = []
        self.result_queue = multiprocessing.Queue()
        self.pending = 0
        self.csv_fp = None
        self.csv_writer = None

        self._init_ui()
        self.log_signal.connect(self.output_box.append)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_results)
        self.timer.start(100)

        self.load_test_cases()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        header = QLabel("SOC Automation Test Runner", self)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 22px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(header)

        ctrl = QHBoxLayout()
        # Dark mode toggle button
        self.dark_mode_btn = QPushButton("🌙", self)
        self.dark_mode_btn.setToolTip("Toggle Dark Mode")
        self.dark_mode_btn.setCheckable(True)
        self.dark_mode_btn.setFixedSize(32, 32)
        self.dark_mode_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 18px; }"
        )
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)
        ctrl.addWidget(self.dark_mode_btn)

        # Control buttons
        for name, slot, color in [
            ("Select All",   self.select_all,   "#28a745"),
            ("Deselect All", self.deselect_all, "#dc3545"),
            ("Run",          self.run_selected_tests, "#007bff"),
            ("Stop",         self.stop_tests,   "#ffc107"),
            ("Export CSV",   self.export_csv,   "#17a2b8"),
            ("Clear Output", self.clear_output, "#6c757d"),
        ]:
            btn = QPushButton(name, self)
            btn.clicked.connect(slot)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{ background-color: {color}; }}
            """)
            ctrl.addWidget(btn)

        self.auto_close_cb = QCheckBox("Close on finish", self)
        ctrl.addWidget(self.auto_close_cb)
        ctrl.addStretch()
        main_layout.addLayout(ctrl)

        splitter = QSplitter(Qt.Horizontal, self)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels(["Category / Test", "Select"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        splitter.addWidget(self.tree)

        self.output_box = QTextEdit(self)
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("font-family: monospace;")
        splitter.addWidget(self.output_box)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

    def toggle_dark_mode(self):
        app = QApplication.instance()
        if self.dark_mode_btn.isChecked():
            # Switch to light icon
            self.dark_mode_btn.setText("☀️")
            # Dark palette
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black)
            app.setPalette(dark_palette)
            # Enhance checkbox/tree indicator visibility
            style = """
                QCheckBox::indicator { width: 20px; height: 20px; }
                QCheckBox::indicator:checked { background-color: #66bb6a; border: 1px solid #66bb6a; }
                QCheckBox::indicator:unchecked { background-color: #555; border: 1px solid #555; }
                QTreeWidget::indicator:checked { background-color: #66bb6a; border: 1px solid #66bb6a; }
                QTreeWidget::indicator:unchecked { background-color: #555; border: 1px solid #555; }
            """
            self.setStyleSheet(style)
        else:
            # Switch to dark icon
            self.dark_mode_btn.setText("🌙")
            # Restore default palette/styles
            app.setPalette(app.style().standardPalette())
            self.setStyleSheet("")

    def _ensure_csv(self):
        if self.csv_writer is None:
            first = not os.path.exists(SESSION_CSV)
            self.csv_fp = open(SESSION_CSV, 'a', newline='')
            self.csv_writer = csv.writer(self.csv_fp)
            if first:
                self.csv_writer.writerow([
                    'Start','End','Test_case_name','executed_command','source_ip','source_hostname',
                    'dest_ip','dest_hostname','dest_port','Proxy','Result','comment'
                ])
                self.csv_fp.flush()

    def load_test_cases(self):
        self.tree.clear()
        cats = {}
        for root, _, files in os.walk(TESTS_DIR):
            cat = os.path.basename(root)
            if cat == os.path.basename(TESTS_DIR):
                cat = "uncategorized"
            if cat not in cats:
                top = QTreeWidgetItem(self.tree, [cat])
                top.setFirstColumnSpanned(True)
                cats[cat] = top
            for f in files:
                if not (f.endswith('.py') or f.endswith('.yaml')):
                    continue
                path = os.path.join(root, f)
                item = QTreeWidgetItem(cats[cat], [os.path.splitext(f)[0], ""])
                item.setCheckState(1, Qt.Unchecked)
                item.setData(0, Qt.UserRole, path)
        self.tree.expandAll()

    def select_all(self):
        def recurse(node):
            for i in range(node.childCount()):
                c = node.child(i)
                if c.childCount(): recurse(c)
                else: c.setCheckState(1, Qt.Checked)
        recurse(self.tree.invisibleRootItem())
        self.log_signal.emit("✅ All selected.")

    def deselect_all(self):
        def recurse(node):
            for i in range(node.childCount()):
                c = node.child(i)
                if c.childCount(): recurse(c)
                else: c.setCheckState(1, Qt.Unchecked)
        recurse(self.tree.invisibleRootItem())
        self.log_signal.emit("✅ All deselected.")

    def clear_output(self):
        self.output_box.clear()
        self.log_signal.emit("🧹 Output cleared.")

    def run_selected_tests(self):
        for p in self.processes:
            if p.is_alive(): p.terminate()
        self.processes.clear()
        self.config_queues.clear()

        chosen = []
        def recurse(node):
            for i in range(node.childCount()):
                c = node.child(i)
                if c.childCount(): recurse(c)
                elif c.checkState(1) == Qt.Checked:
                    chosen.append(c.data(0, Qt.UserRole))
        recurse(self.tree.invisibleRootItem())

        if not chosen:
            self.log_signal.emit("⚠️ No tests selected.")
            return

        self.pending = len(chosen)
        self.log_signal.emit(f"▶ Starting {self.pending} test(s)")
        for path in chosen:
            cfg = {}
            cfgp = os.path.splitext(path)[0] + '.json'
            if os.path.exists(cfgp):
                cfg = json.load(open(cfgp))
            cq = multiprocessing.Queue(); cq.put(cfg)
            self.config_queues.append(cq)
            p = multiprocessing.Process(target=process_worker, args=(path, cq, self.result_queue))
            p.start(); self.processes.append(p)

    def stop_tests(self):
        for p in self.processes:
            if p.is_alive(): p.terminate()
        self.log_signal.emit("⚠️ Stopped all tests.")

    def poll_results(self):
        while not self.result_queue.empty():
            msg = self.result_queue.get()
            if msg is None:
                self.pending -= 1
                if self.pending <= 0 and self.auto_close_cb.isChecked():
                    QApplication.quit()
                continue
            if isinstance(msg, dict) and 'csv' in msg:
                r = msg['csv']
                self._ensure_csv()
                self.csv_writer.writerow([
                    r.get('Start'), r.get('End'), r.get('Test_case_name'),
                    r.get('executed_command'), r.get('source_ip'),
                    r.get('source_hostname'), r.get('dest_ip'),
                    r.get('dest_hostname'), r.get('dest_port'),
                    r.get('Proxy'), r.get('Result'), r.get('comment')
                ])
                self.csv_fp.flush()
            else:
                self.log_signal.emit(str(msg))

    def export_csv(self):
        dest, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", os.getcwd(), "CSV Files (*.csv)")
        if dest:
            shutil.copy(SESSION_CSV, dest)
            self.log_signal.emit(f"✅ Exported to {dest}")

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    app = QApplication(sys.argv)
    gui = TestRunnerGUI()
    gui.show()
    sys.exit(app.exec_())
