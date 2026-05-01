import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSlider, QComboBox, QCheckBox,
    QFileDialog, QLineEdit, QDialog, QTabWidget, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QPolygonF, QCursor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.recorder import RecorderManager, RecordingState


class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_path="C:/Videos/CapSure"):
        super().__init__(parent)
        self.current_path = current_path
        self.setWindowTitle("设置")
        self.setFixedSize(360, 300)
        self.setModal(True)
        
        self.setStyleSheet("""
            QDialog {
                background: #18181b;
            }
            QLabel {
                color: #a1a1aa;
                font-size: 12px;
            }
            QLineEdit {
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                padding: 8px 12px;
                color: #fafafa;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #ef4444;
            }
            QComboBox {
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                padding: 8px 12px;
                color: #fafafa;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #27272a;
                color: #fafafa;
                border: 1px solid #3f3f46;
                selection-background-color: #ef4444;
            }
            QCheckBox {
                color: #a1a1aa;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #3f3f46;
                background: #27272a;
            }
            QCheckBox::indicator:checked {
                background: #ef4444;
                border-color: #ef4444;
            }
            QTabWidget::pane {
                border: 1px solid #27272a;
                border-radius: 6px;
                background: #18181b;
            }
            QTabBar::tab {
                background: #27272a;
                color: #a1a1aa;
                padding: 8px 16px;
                border: none;
                border-radius: 6px 6px 0 0;
                font-size: 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #3f3f46;
                color: #fafafa;
            }
            QTabBar::tab:hover:!selected {
                background: #27272a;
                color: #d4d4d8;
            }
            QPushButton {
                background: #3f3f46;
                border: none;
                border-radius: 6px;
                color: #fafafa;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #52525b;
            }
            QPushButton:pressed {
                background: #27272a;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        tabs = QTabWidget()
        tabs.addTab(self.create_basic_tab(), "基础")
        tabs.addTab(self.create_audio_tab(), "音频")
        tabs.addTab(self.create_output_tab(), "输出")
        
        layout.addWidget(tabs)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 32)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                color: #a1a1aa;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #3f3f46;
                color: #fafafa;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(80, 32)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def create_basic_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        
        layout.addWidget(self._create_setting_row("质量", self._create_combo(["1080p", "720p", "4K"])))
        layout.addWidget(self._create_setting_row("帧率", self._create_combo(["30 FPS", "60 FPS", "24 FPS"])))
        layout.addWidget(self._create_setting_row("格式", self._create_combo(["MP4", "MKV", "WebM"])))
        
        layout.addStretch()
        return tab
    
    def create_audio_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        mic_check = QCheckBox("麦克风")
        mic_check.setObjectName("mic_check")
        mic_check.setChecked(True)
        layout.addWidget(mic_check)
        
        mic_volume_layout = QHBoxLayout()
        mic_volume_layout.setSpacing(8)
        mic_volume_label = QLabel("音量")
        mic_volume_label.setStyleSheet("color: #71717a; font-size: 11px;")
        mic_volume_layout.addWidget(mic_volume_label)
        self.mic_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.mic_volume_slider.setRange(0, 100)
        self.mic_volume_slider.setValue(80)
        self.mic_volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #27272a;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ef4444;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
            QSlider::sub-page:horizontal {
                background: #ef4444;
                border-radius: 2px;
            }
        """)
        mic_volume_layout.addWidget(self.mic_volume_slider, 1)
        self.mic_volume_value = QLabel("80")
        self.mic_volume_value.setStyleSheet("color: #a1a1aa; font-size: 11px; min-width: 24px;")
        mic_volume_layout.addWidget(self.mic_volume_value)
        layout.addLayout(mic_volume_layout)
        
        self.mic_volume_slider.valueChanged.connect(lambda v: self.mic_volume_value.setText(str(v)))
        
        sys_check = QCheckBox("系统音频")
        sys_check.setObjectName("sys_check")
        sys_check.setChecked(True)
        layout.addWidget(sys_check)
        
        sys_volume_layout = QHBoxLayout()
        sys_volume_layout.setSpacing(8)
        sys_volume_label = QLabel("音量")
        sys_volume_label.setStyleSheet("color: #71717a; font-size: 11px;")
        sys_volume_layout.addWidget(sys_volume_label)
        self.sys_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.sys_volume_slider.setRange(0, 100)
        self.sys_volume_slider.setValue(100)
        self.sys_volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #27272a;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ef4444;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
            QSlider::sub-page:horizontal {
                background: #ef4444;
                border-radius: 2px;
            }
        """)
        sys_volume_layout.addWidget(self.sys_volume_slider, 1)
        self.sys_volume_value = QLabel("100")
        self.sys_volume_value.setStyleSheet("color: #a1a1aa; font-size: 11px; min-width: 24px;")
        sys_volume_layout.addWidget(self.sys_volume_value)
        layout.addLayout(sys_volume_layout)
        
        self.sys_volume_slider.valueChanged.connect(lambda v: self.sys_volume_value.setText(str(v)))
        
        layout.addStretch()
        return tab
    
    def create_output_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        
        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(8)
        
        self.path_edit = QLineEdit()
        self.path_edit.setText(self.current_path)
        path_layout.addWidget(self.path_edit, 1)
        
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedSize(60, 36)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(self._create_setting_row("路径", path_row))
        
        auto_check = QCheckBox("完成后打开文件夹")
        auto_check.setChecked(True)
        layout.addWidget(auto_check)
        
        layout.addStretch()
        return tab
    
    def browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, 
            "选择保存路径", 
            self.path_edit.text()
        )
        if path:
            self.path_edit.setText(path)
    
    def _create_setting_row(self, label_text, widget):
        row = QHBoxLayout()
        row.setSpacing(12)
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #a1a1aa; font-size: 12px; min-width: 40px;")
        row.addWidget(label)
        row.addWidget(widget, 1)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addLayout(row)
        
        return container
    
    def _create_combo(self, items):
        combo = QComboBox()
        combo.addItems(items)
        return combo


class RecordButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_recording = False
        self.animation_value = 0
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, False)
        self.setMouseTracking(False)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        
        self.setStyleSheet("background: transparent; border: none;")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setPen(Qt.PenStyle.NoPen)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = 22
        
        if self.is_recording:
            for i in range(3):
                r = radius + 8 + i * 8 + self.animation_value * 6
                opacity = int(80 * (1 - self.animation_value) * (1 - i * 0.3))
                if opacity > 0:
                    painter.setPen(QPen(QColor(239, 68, 68, opacity), 2))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(
                        int(center_x - r), int(center_y - r), int(r * 2), int(r * 2)
                    )
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        if self.is_recording:
            gradient.setColorAt(0, QColor(239, 68, 68))
            gradient.setColorAt(1, QColor(185, 28, 28))
        else:
            gradient.setColorAt(0, QColor(239, 68, 68))
            gradient.setColorAt(1, QColor(220, 38, 38))
        
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), radius * 2, radius * 2)
        
        if self.is_recording:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawRoundedRect(int(center_x - 7), int(center_y - 7), 14, 14, 3, 3)
        else:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawPolygon(QPolygonF([
                QPointF(center_x - 7, center_y - 10),
                QPointF(center_x - 7, center_y + 10),
                QPointF(center_x + 10, center_y)
            ]))
    
    def update_animation(self):
        if self.is_recording:
            self.animation_value = (self.animation_value + 0.03) % 1.0
            self.update()
    
    def start_recording(self):
        self.is_recording = True
        self.animation_value = 0
        self.timer.start(40)
        self.update()
    
    def stop_recording(self):
        self.is_recording = False
        self.timer.stop()
        self.animation_value = 0
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CapSure")
        self.setMinimumSize(300, 260)
        self.resize(300, 260)
        self.is_recording = False
        self.elapsed_time = 0
        self.output_path = "C:/Videos/CapSure"
        self.is_processing = False
        
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        icon_path = os.path.join(base_path, 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
        
        self.recorder = RecorderManager()
        self.recorder.set_callback("on_state_change", self.on_recording_state_change)
        self.recorder.set_callback("on_timer", self.on_recording_timer)
        self.recorder.set_callback("on_file_size", self.on_file_size_update)
        self.recorder.set_callback("on_complete", self.on_recording_complete)
        self.recorder.set_callback("on_error", self.on_recording_error)
        
        self.setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background: #18181b;")
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        header = QHBoxLayout()
        
        logo = QLabel("视频录制")
        logo.setStyleSheet("color: #fafafa; font-size: 14px; font-weight: 700;")
        header.addWidget(logo)
        header.addStretch()
        
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: #a1a1aa;")
        header.addWidget(self.time_label)
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self.toggle_settings)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                color: #a1a1aa;
                font-size: 12px;
            }
            QPushButton:hover {
                border-color: #ef4444;
                color: #ef4444;
                background: #3f3f46;
            }
        """)
        header.addWidget(self.settings_btn)
        
        layout.addLayout(header)
        
        self.status_label = QLabel("准备录制")
        self.status_label.setStyleSheet("color: #fafafa; font-size: 13px;")
        layout.addWidget(self.status_label)
        
        self.preview_area = QLabel("点击录制按钮开始")
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setMinimumHeight(50)
        self.preview_area.setStyleSheet("""
            QLabel {
                background: #27272a;
                color: #71717a;
                font-size: 11px;
                border-radius: 8px;
                border: 1px solid #3f3f46;
            }
        """)
        layout.addWidget(self.preview_area)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.record_btn = RecordButton()
        self.record_btn.setFixedSize(56, 56)
        self.record_btn.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        controls = QHBoxLayout()
        controls.addStretch()
        
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setFixedSize(60, 30)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                color: #a1a1aa;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #3f3f46;
                color: #fafafa;
            }
            QPushButton:disabled {
                color: #52525b;
                border-color: #27272a;
            }
        """)
        controls.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedSize(60, 30)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #dc2626;
            }
            QPushButton:disabled {
                background: #7f1d1d;
                color: #a1a1aa;
            }
        """)
        controls.addWidget(self.stop_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        info_layout = QHBoxLayout()
        
        self.info_label = QLabel("1920 × 1080 • 30 FPS")
        self.info_label.setStyleSheet("color: #52525b; font-size: 10px;")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        
        self.size_label = QLabel("0.0 MB")
        self.size_label.setStyleSheet("color: #52525b; font-size: 10px;")
        info_layout.addWidget(self.size_label)
        
        layout.addLayout(info_layout)
    
    def toggle_settings(self):
        dialog = SettingsDialog(self, self.output_path)
        if dialog.exec():
            if dialog.path_edit:
                self.output_path = dialog.path_edit.text()
            
            self.mic_volume = dialog.mic_volume_slider.value()
            self.sys_volume = dialog.sys_volume_slider.value()
            self.mic_enabled = dialog.findChild(QCheckBox, "mic_check").isChecked()
            self.sys_audio_enabled = dialog.findChild(QCheckBox, "sys_check").isChecked()
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        try:
            output_dir = self.output_path
            if not output_dir:
                output_dir = os.path.join(os.path.expanduser("~"), "Videos", "CapSure")
            
            config = {
                "fps": 30,
                "format": "mp4",
                "output_dir": output_dir,
                "mic_volume": getattr(self, 'mic_volume', 80),
                "sys_volume": getattr(self, 'sys_volume', 100),
                "mic_enabled": getattr(self, 'mic_enabled', True),
                "sys_audio_enabled": getattr(self, 'sys_audio_enabled', True)
            }
            
            self.recorder.config = config
            
            success = self.recorder.start_recording()
            
            if success:
                self.is_recording = True
                self.elapsed_time = 0
                self.record_btn.start_recording()
                self.status_label.setText("录制中")
                self.status_label.setStyleSheet("color: #ef4444; font-size: 13px;")
                self.pause_btn.setEnabled(True)
                self.pause_btn.setText("暂停")
                self.stop_btn.setEnabled(True)
                self.timer.start(1000)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", "无法开始录制")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", f"录制失败: {str(e)}")
    
    def stop_recording(self):
        if self.is_recording:
            self.recorder.stop_recording()
    
    def toggle_pause(self):
        if not self.is_recording:
            return
        
        if self.pause_btn.text() == "暂停":
            self.pause_btn.setText("继续")
            self.timer.stop()
            self.recorder.pause_recording()
        else:
            self.pause_btn.setText("暂停")
            self.timer.start(1000)
            self.recorder.resume_recording()
    
    def update_time(self):
        self.elapsed_time += 1
        hours = self.elapsed_time // 3600
        minutes = (self.elapsed_time % 3600) // 60
        seconds = self.elapsed_time % 60
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def on_recording_state_change(self, state):
        if state == RecordingState.IDLE:
            self.is_recording = False
            self.record_btn.stop_recording()
            self.status_label.setText("准备录制")
            self.status_label.setStyleSheet("color: #fafafa; font-size: 13px;")
            self.time_label.setText("00:00:00")
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.timer.stop()
        elif state == RecordingState.RECORDING:
            pass
    
    def on_recording_timer(self, elapsed_time):
        pass
    
    def on_file_size_update(self, file_size_bytes):
        file_size_mb = file_size_bytes / (1024 * 1024)
        self.size_label.setText(f"{file_size_mb:.1f} MB")
    
    def on_recording_complete(self, file_path):
        self.status_label.setText("录制完成")
        self.status_label.setStyleSheet("color: #fafafa; font-size: 13px;")
        self.is_processing = False
    
    def on_recording_error(self, error_msg):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "录制错误", error_msg)
        self.is_recording = False
        self.record_btn.stop_recording()
        self.status_label.setText("准备录制")
        self.status_label.setStyleSheet("color: #fafafa; font-size: 13px;")
        self.time_label.setText("00:00:00")
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.timer.stop()
    
    def closeEvent(self, event):
        if self.is_recording:
            self.stop_recording()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
