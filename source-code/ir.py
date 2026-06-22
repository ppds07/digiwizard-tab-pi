import sys
import os
import subprocess

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QWidget, QMessageBox,
    QComboBox, QGroupBox, QStyleFactory
)
from PyQt5.QtCore import Qt, QProcess


class IRKeyTableGUI(QMainWindow):

    def __init__(self):
        super().__init__()

        self.process = None
        self.terminal_cmd = None
        self.terminal_args = []

        self.initUI()
        self.check_dependencies()


    def check_dependencies(self):
        missing = []

        # check ir-keytable
        if subprocess.run(["which", "ir-keytable"],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).returncode != 0:
            missing.append("ir-keytable (install v4l-utils)")

        # find terminal
        terminals = [
            ("lxterminal", ["-e"]),
            ("konsole", ["-e"]),
            ("gnome-terminal", ["--"]),
            ("xterm", ["-e"]),
            ("xfce4-terminal", ["-e"]),
            ("terminator", ["-e"]),
            ("mate-terminal", ["-e"])
        ]

        for term, args in terminals:
            if subprocess.run(["which", term],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).returncode == 0:
                self.terminal_cmd = term
                self.terminal_args = args
                break

        if not self.terminal_cmd:
            missing.append("Terminal emulator")

        if missing:
            msg = "Missing dependencies:\n• " + "\n• ".join(missing)
            QMessageBox.warning(self, "Missing Dependencies", msg)
            self.output_display.append(msg)
            self.probe_button.setEnabled(False)
            self.test_button.setEnabled(False)
        else:
            self.output_display.append(f"Using terminal: {self.terminal_cmd}")


    def initUI(self):
        self.setWindowTitle("IR Keytable Tester")
        self.setGeometry(100, 100, 600, 400)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("IR Remote Control Tester")
        title.setAlignment(Qt.AlignCenter)
        f = title.font()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        # protocol selector
        group = QGroupBox("IR Protocol")
        g_layout = QVBoxLayout()

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItem("All Protocols", "all")
        self.protocol_combo.addItem("RC-5", "rc-5")
        self.protocol_combo.addItem("RC-6", "rc-6")
        self.protocol_combo.addItem("NEC", "nec")
        self.protocol_combo.addItem("JVC", "jvc")
        self.protocol_combo.addItem("Sony", "sony")

        g_layout.addWidget(self.protocol_combo)
        group.setLayout(g_layout)
        layout.addWidget(group)

        # output
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        layout.addWidget(self.output_display)

        # buttons
        btn_layout = QHBoxLayout()

        self.probe_button = QPushButton("Probe IR Protocols")
        self.probe_button.clicked.connect(self.probe_protocols)
        btn_layout.addWidget(self.probe_button)

        self.test_button = QPushButton("Test IR Input in Terminal")
        self.test_button.clicked.connect(self.launch_terminal_test)
        btn_layout.addWidget(self.test_button)

        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)
        btn_layout.addWidget(self.clear_button)

        layout.addLayout(btn_layout)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

    def clear_output(self):
        self.output_display.clear()

    def probe_protocols(self):
        protocol = self.protocol_combo.currentData()

        self.output_display.clear()
        self.output_display.append(f"Probing {protocol} protocols...\n")
        self.status_label.setText("Running probe...")

        self.process = QProcess()

        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.handle_probe_finished)

        cmd = "ir-keytable"
        if os.geteuid() != 0:
            cmd = "pkexec " + cmd

        self.process.start(cmd, ["-p", protocol])

    def launch_terminal_test(self):
        if not self.terminal_cmd:
            QMessageBox.warning(self, "Error", "No terminal emulator found.")
            return

        cmd = "ir-keytable -t"
        if os.geteuid() != 0:
            cmd = "pkexec " + cmd

        subprocess.Popen([self.terminal_cmd] + self.terminal_args + [cmd])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.output_display.append(data.strip())

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.output_display.append("ERROR: " + data.strip())

    def handle_probe_finished(self, exit_code, _):
        if exit_code == 0:
            self.status_label.setText("Probe completed successfully")
        else:
            self.status_label.setText(f"Probe failed (code {exit_code})")

    def closeEvent(self, event):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
        event.accept()

def main():
    app = QApplication(sys.argv)

    if "Breeze" in QStyleFactory.keys():
        app.setStyle("Breeze")

    window = IRKeyTableGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
