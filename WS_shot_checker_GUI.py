import sys
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLineEdit, QLabel,
                             QTextEdit, QFileDialog, QTabWidget, QTableWidget,
                             QTableWidgetItem, QProgressBar, QMessageBox,
                             QGroupBox, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import pandas as pd
from WS_shot_checker import projectData


class WorkerThread(QThread):
    """Worker thread for processing data without freezing the GUI"""
    progress = pyqtSignal(int, str)  # Changed to include percentage
    finished = pyqtSignal(bool, str)

    def __init__(self, project, operation):
        super().__init__()
        self.project = project
        self.operation = operation
        self.start_time = None

    def progress_callback(self, percentage, message):
        """Callback for progress updates with time estimation"""
        if self.start_time is None:
            self.start_time = time.time()

        elapsed = time.time() - self.start_time

        if percentage > 0:
            estimated_total = elapsed / (percentage / 100.0)
            remaining = estimated_total - elapsed

            if remaining > 60:
                time_str = f"{int(remaining / 60)}m {int(remaining % 60)}s remaining"
            else:
                time_str = f"{int(remaining)}s remaining"

            full_message = f"{message} - {time_str}"
        else:
            full_message = message

        self.progress.emit(percentage, full_message)

    def run(self):
        try:
            self.start_time = time.time()

            if self.operation == 'find_files':
                self.progress.emit(0, "Starting file search...")
                self.project.findShotFiles(progress_callback=self.progress_callback)
                self.finished.emit(True, f"Found {len(self.project.files)} files")

            elif self.operation == 'compile_master':
                self.progress.emit(0, "Compiling master data...")
                self.project.compileMaster()
                self.finished.emit(True, f"Compiled {len(self.project.master)} records")

            elif self.operation == 'check_all':
                self.progress.emit(0, "Running all validation checks...")
                self.project.checkDateConsistency()
                self.finished.emit(True, "All checks completed")

        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class ShotCheckerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project = None
        self.worker = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Willowstick Shot Data Checker")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Path selection section
        path_group = QGroupBox("Project Path")
        path_layout = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select project directory...")
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("Load Project")
        browse_btn.clicked.connect(self.browse_and_load_project)
        path_layout.addWidget(browse_btn)

        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("")
        self.progress_bar.setRange(0, 100)  # Set range for percentage
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Action buttons
        action_layout = QHBoxLayout()

        self.compile_btn = QPushButton("Compile Master Data")
        self.compile_btn.clicked.connect(self.compile_master)
        self.compile_btn.setEnabled(False)
        action_layout.addWidget(self.compile_btn)

        self.validate_btn = QPushButton("Run Validation Checks")
        self.validate_btn.clicked.connect(self.run_validation)
        self.validate_btn.setEnabled(False)
        action_layout.addWidget(self.validate_btn)

        self.export_btn = QPushButton("Export Reorganized Sheets")
        self.export_btn.clicked.connect(self.export_sheets)
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.export_btn)

        main_layout.addLayout(action_layout)

        # Tab widget for different views
        self.tabs = QTabWidget()

        # Files tab
        self.files_tab = QTextEdit()
        self.files_tab.setReadOnly(True)
        self.tabs.addTab(self.files_tab, "Found Files")

        # Data preview tab
        self.data_table = QTableWidget()
        self.tabs.addTab(self.data_table, "Data Preview")

        # Validation results tab
        validation_widget = QWidget()
        validation_layout = QVBoxLayout(validation_widget)

        # Date mismatches
        date_label = QLabel("Date Mismatches:")
        date_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        validation_layout.addWidget(date_label)
        self.date_text = QTextEdit()
        self.date_text.setReadOnly(True)
        validation_layout.addWidget(self.date_text)

        # Operator mismatches
        oper_label = QLabel("Operator Mismatches:")
        oper_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        validation_layout.addWidget(oper_label)
        self.oper_text = QTextEdit()
        self.oper_text.setReadOnly(True)
        validation_layout.addWidget(self.oper_text)

        # RIN mismatches
        rin_label = QLabel("RIN Mismatches:")
        rin_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        validation_layout.addWidget(rin_label)
        self.rin_text = QTextEdit()
        self.rin_text.setReadOnly(True)
        validation_layout.addWidget(self.rin_text)

        self.tabs.addTab(validation_widget, "Validation Results")

        # Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.tabs.addTab(self.log_text, "Log")

        main_layout.addWidget(self.tabs)

        # Status bar
        self.statusBar().showMessage("Ready")

    def browse_and_load_project(self):
        """Open file dialog to select project directory, initialize project, and find files"""
        self.directory = QFileDialog.getExistingDirectory(
            self, "Select Project Directory", ""
        )
        if not self.directory:
            return

        self.path_input.setText(self.directory)

        if not os.path.exists(self.directory):
            QMessageBox.warning(self, "Invalid Path", "The selected path does not exist.")
            return

        # Initialize project
        self.project = projectData(self.directory)
        self.log(f"Project initialized with path: {self.directory}")
        self.statusBar().showMessage("Project loaded, finding files...")

        # Automatically find files
        self.progress_bar.setFormat("Searching for files...")

        # Run in worker thread
        self.worker = WorkerThread(self.project, 'find_files')
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_find_files_finished)
        self.worker.start()


    def display_files(self):
        """Display found files in the files tab"""
        if not self.project or not self.project.files:
            return

        files_text = (f"Total files found: {len(self.project.files)}\n"
                      f"    Base folder: {self.directory}\n\n")
        for i, file in enumerate(self.project.files, 1):
            files_text += f"{i}. {file.replace(self.directory, "")}\n"

        self.files_tab.setPlainText(files_text)
        self.tabs.setCurrentIndex(0)  # Switch to files tab

    def on_find_files_finished(self, success, message):
        """Handle completion of file finding"""
        if success:
            self.log(message)
            self.display_files()
            self.compile_btn.setEnabled(True)
            self.statusBar().showMessage(message)
        else:
            QMessageBox.critical(self, "Error", message)
            self.log(f"ERROR: {message}")

        self.progress_bar.setFormat("")
        self.progress_bar.setValue(0)

    def compile_master(self):
        """Compile master dataframe from all files"""
        if not self.project or not self.project.files:
            QMessageBox.warning(self, "No Files", "Please find files first.")
            return

        self.progress_bar.setFormat("Compiling master data...")
        self.compile_btn.setEnabled(False)

        # Run in worker thread
        self.worker = WorkerThread(self.project, 'compile_master')
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_compile_finished)
        self.worker.start()

    def on_compile_finished(self, success, message):
        """Handle completion of data compilation"""
        if success:
            self.log(message)
            self.display_data_preview()
            self.validate_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.statusBar().showMessage(message)
        else:
            QMessageBox.critical(self, "Error", message)
            self.log(f"ERROR: {message}")

        self.progress_bar.setFormat("")
        self.progress_bar.setValue(0)
        self.compile_btn.setEnabled(True)

    def display_data_preview(self):
        """Display preview of master data"""
        if self.project.master.empty:
            return

        df = self.project.master.head(100)  # Show first 100 rows

        self.data_table.setRowCount(len(df))
        self.data_table.setColumnCount(len(df.columns))
        self.data_table.setHorizontalHeaderLabels(df.columns.tolist())

        for i, row in enumerate(df.itertuples(index=False)):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(i, j, item)

        self.data_table.resizeColumnsToContents()
        self.log(f"Data preview updated (showing first 100 of {len(self.project.master)} rows)")

    def run_validation(self):
        """Run all validation checks"""
        if self.project.master.empty:
            QMessageBox.warning(self, "No Data", "Please compile master data first.")
            return

        self.progress_bar.setFormat("Running validation checks...")
        self.validate_btn.setEnabled(False)

        # Run in worker thread
        self.worker = WorkerThread(self.project, 'check_all')
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_validation_finished)
        self.worker.start()

    def on_validation_finished(self, success, message):
        """Handle completion of validation"""
        if success:
            self.log(message)
            self.display_validation_results()
            self.statusBar().showMessage("Validation complete")
        else:
            QMessageBox.critical(self, "Error", message)
            self.log(f"ERROR: {message}")

        self.progress_bar.setFormat("")
        self.progress_bar.setValue(0)
        self.validate_btn.setEnabled(True)

    def display_validation_results(self):
        """Display validation results in the validation tab"""
        # Date mismatches
        if self.project.date_mismatches:
            date_text = f"Found {len(self.project.date_mismatches)} date mismatches:\n\n"
            for mismatch in self.project.date_mismatches:
                date_text += f"File: {mismatch['file']}\n"
                date_text += f"  File Date: {mismatch['file_date']}\n"
                date_text += f"  Dates present in data: {', '.join(mismatch['data_dates'])}\n\n"
            self.date_text.setPlainText(date_text)
            self.log(f"Found {len(self.project.date_mismatches)} date mismatches")
        else:
            self.date_text.setPlainText("No date mismatches found. ✓")
            self.log("No date mismatches found")

        # Operator mismatches
        oper_mismatches = self.project.checkOperator()
        if oper_mismatches:
            oper_text = f"Found {len(oper_mismatches)} operator mismatches:\n\n"
            for mismatch in oper_mismatches:
                oper_text += f"File: {mismatch['file']}\n"
                oper_text += f"  Operators: {', '.join(mismatch['operators'])}\n\n"
            self.oper_text.setPlainText(oper_text)
            self.log(f"Found {len(oper_mismatches)} operator mismatches")
        else:
            self.oper_text.setPlainText("No operator mismatches found. ✓")
            self.log("No operator mismatches found")

        # RIN mismatches
        rin_mismatches = self.project.checkRIN()
        if rin_mismatches:
            rin_text = f"Found {len(rin_mismatches)} RIN mismatches:\n\n"
            for mismatch in rin_mismatches:
                rin_text += f"File: {mismatch['file']}\n"
                rin_text += f"  RINs: {', '.join(str(r) for r in mismatch['RINs'])}\n\n"
            self.rin_text.setPlainText(rin_text)
            self.log(f"Found {len(rin_mismatches)} RIN mismatches")
        else:
            self.rin_text.setPlainText("No RIN mismatches found. ✓")
            self.log("No RIN mismatches found")

        # Switch to validation tab
        self.tabs.setCurrentIndex(2)

    def export_sheets(self):
        """Export reorganized sheets"""
        if self.project.master.empty:
            QMessageBox.warning(self, "No Data", "Please compile master data first.")
            return

        export_dir = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", ""
        )

        if not export_dir:
            return

        try:
            self.progress_bar.setFormat("Exporting reorganized sheets...")
            self.project.exportReorgSheets(export_dir)
            self.log(f"Reorganized sheets exported to: {export_dir}")
            QMessageBox.information(
                self, "Export Complete",
                f"Reorganized sheets have been exported to:\n{export_dir}"
            )
            self.statusBar().showMessage("Export complete")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error during export: {str(e)}")
            self.log(f"ERROR during export: {str(e)}")
        finally:
            self.progress_bar.setFormat("")

    def update_progress(self, percentage, message):
        """Update progress bar with percentage and message"""
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(message)

    def log(self, message):
        """Add message to log tab"""
        self.log_text.append(message)


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    gui = ShotCheckerGUI()
    gui.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

