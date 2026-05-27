import sys
import os
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QComboBox, QCheckBox,
    QFileDialog, QLineEdit, QDialog, QTabWidget,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QSettings, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QBrush, QPen, QLinearGradient,
    QPolygonF, QCursor, QIcon, QImage, QPixmap, QAction
)

logger = logging.getLogger(__name__)

# 全局快捷键（可选依赖）
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.recorder import RecorderManager, RecordingState


class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_path=None):
        super().__init__(parent)
        self.settings = QSettings("CapSure", "CapSure")
        if current_path is None:
            current_path = self.settings.value("output_path", 
                os.path.join(os.path.expanduser("~"), "Videos", "CapSure"))
        self.current_path = current_path
        self.setWindowTitle("设置")
        self.setFixedSize(360, 360)
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
        
        quality_value = self.settings.value("quality", "1080p")
        self.quality_combo = self._create_combo(["1080p", "720p", "4K"])
        self.quality_combo.setCurrentText(quality_value)
        layout.addWidget(self._create_setting_row("质量", self.quality_combo))
        
        fps_value = self.settings.value("fps", "30 FPS")
        self.fps_combo = self._create_combo(["30 FPS", "60 FPS", "24 FPS"])
        self.fps_combo.setCurrentText(fps_value)
        layout.addWidget(self._create_setting_row("帧率", self.fps_combo))
        
        format_value = self.settings.value("format", "MP4")
        self.format_combo = self._create_combo(["MP4", "MKV", "WebM"])
        self.format_combo.setCurrentText(format_value)
        layout.addWidget(self._create_setting_row("格式", self.format_combo))
        
        countdown_checked = self.settings.value("countdown_enabled", "true") == "true"
        self.countdown_check = QCheckBox("录制前显示倒计时")
        self.countdown_check.setChecked(countdown_checked)
        self.countdown_check.setStyleSheet("color: #a1a1aa; font-size: 12px; spacing: 8px;")
        layout.addWidget(self.countdown_check)
        
        layout.addStretch()
        return tab
    
    def create_audio_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        mic_checked = self.settings.value("mic_enabled", "true") == "true"
        self.mic_check = QCheckBox("麦克风")
        self.mic_check.setObjectName("mic_check")
        self.mic_check.setChecked(mic_checked)
        layout.addWidget(self.mic_check)
        
        mic_volume_layout = QHBoxLayout()
        mic_volume_layout.setSpacing(8)
        mic_volume_label = QLabel("音量")
        mic_volume_label.setStyleSheet("color: #71717a; font-size: 11px;")
        mic_volume_layout.addWidget(mic_volume_label)
        self.mic_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.mic_volume_slider.setRange(0, 100)
        mic_vol = int(self.settings.value("mic_volume", "80"))
        self.mic_volume_slider.setValue(mic_vol)
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
        self.mic_volume_value = QLabel(str(mic_vol))
        self.mic_volume_value.setStyleSheet("color: #a1a1aa; font-size: 11px; min-width: 24px;")
        mic_volume_layout.addWidget(self.mic_volume_value)
        layout.addLayout(mic_volume_layout)
        
        self.mic_volume_slider.valueChanged.connect(lambda v: self.mic_volume_value.setText(str(v)))
        
        sys_checked = self.settings.value("sys_audio_enabled", "true") == "true"
        self.sys_check = QCheckBox("系统音频")
        self.sys_check.setObjectName("sys_check")
        self.sys_check.setChecked(sys_checked)
        layout.addWidget(self.sys_check)
        
        sys_volume_layout = QHBoxLayout()
        sys_volume_layout.setSpacing(8)
        sys_volume_label = QLabel("音量")
        sys_volume_label.setStyleSheet("color: #71717a; font-size: 11px;")
        sys_volume_layout.addWidget(sys_volume_label)
        self.sys_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.sys_volume_slider.setRange(0, 100)
        sys_vol = int(self.settings.value("sys_volume", "100"))
        self.sys_volume_slider.setValue(sys_vol)
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
        self.sys_volume_value = QLabel(str(sys_vol))
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
        self.setFixedSize(64, 64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_recording = False
        self.animation_value = 0
        self.ring_progress = 0.0  # 0.0 ~ 1.0 环形进度
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
        ring_radius = radius + 7
        
        # 画环形进度条（录制中时显示）
        if self.is_recording:
            # 波纹动画
            for i in range(3):
                r = radius + 8 + i * 8 + self.animation_value * 6
                opacity = int(80 * (1 - self.animation_value) * (1 - i * 0.3))
                if opacity > 0:
                    painter.setPen(QPen(QColor(239, 68, 68, opacity), 2))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(
                        int(center_x - r), int(center_y - r), int(r * 2), int(r * 2)
                    )
            
            # 环形进度背景
            painter.setPen(QPen(QColor(239, 68, 68, 40), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                int(center_x - ring_radius), int(center_y - ring_radius),
                int(ring_radius * 2), int(ring_radius * 2)
            )
            
            # 环形进度前景
            if self.ring_progress > 0:
                painter.setPen(QPen(QColor(239, 68, 68, 200), 3))
                span_angle = int(self.ring_progress * 360 * 16)
                painter.drawArc(
                    int(center_x - ring_radius), int(center_y - ring_radius),
                    int(ring_radius * 2), int(ring_radius * 2),
                    90 * 16, -span_angle
                )
        
        # 红色圆形按钮
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        if self.is_recording:
            gradient.setColorAt(0, QColor(239, 68, 68))
            gradient.setColorAt(1, QColor(185, 28, 28))
        else:
            gradient.setColorAt(0, QColor(239, 68, 68))
            gradient.setColorAt(1, QColor(220, 38, 38))
        
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), radius * 2, radius * 2)
        
        # 内部图标
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
    
    def set_ring_progress(self, elapsed_seconds):
        """设置环形进度（以60分钟为满圈）"""
        self.ring_progress = min(elapsed_seconds / 3600.0, 1.0)
        self.update()
    
    def start_recording(self):
        self.is_recording = True
        self.animation_value = 0
        self.ring_progress = 0.0
        self.timer.start(40)
        self.update()
    
    def stop_recording(self):
        self.is_recording = False
        self.timer.stop()
        self.animation_value = 0
        self.ring_progress = 0.0
        self.update()


class CountdownOverlay(QLabel):
    """录制前倒计时遮罩"""
    countdown_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setVisible(False)
        self._count = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setStyleSheet("""
            QLabel {
                background-color: #B418181b;
                color: #ef4444;
                font-size: 72px;
                font-weight: bold;
                font-family: 'Consolas';
                border-radius: 12px;
            }
        """)
    
    def start(self, from_sec=3):
        self._count = from_sec
        self.setText(str(self._count))
        self.setVisible(True)
        self.raise_()
        self._timer.start(1000)
    
    def _tick(self):
        self._count -= 1
        if self._count <= 0:
            self._timer.stop()
            self.setText("录制!")
            self.setVisible(True)
            QTimer.singleShot(400, self._finish)
        else:
            self.setText(str(self._count))
    
    def _finish(self):
        self.setVisible(False)
        self.countdown_finished.emit()


class MainWindow(QMainWindow):
    frame_ready = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CapSure")
        self.setMinimumSize(300, 260)
        self.resize(300, 260)
        self.is_recording = False
        self.elapsed_time = 0
        self.is_processing = False
        
        # QSettings 加载设置
        self.settings = QSettings("CapSure", "CapSure")
        self.output_path = self.settings.value("output_path",
            os.path.join(os.path.expanduser("~"), "Videos", "CapSure"))
        self.mic_volume = int(self.settings.value("mic_volume", "80"))
        self.sys_volume = int(self.settings.value("sys_volume", "100"))
        self.mic_enabled = self.settings.value("mic_enabled", "true") == "true"
        self.sys_audio_enabled = self.settings.value("sys_audio_enabled", "true") == "true"
        self.countdown_enabled = self.settings.value("countdown_enabled", "true") == "true"
        
        # 应用图标
        if getattr(sys, 'frozen', False):
            base_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
        
        icon_path = os.path.join(base_path, 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.recorder = RecorderManager()
        self.recorder.set_callback("on_state_change", self.on_recording_state_change)
        self.recorder.set_callback("on_timer", self.on_recording_timer)
        self.recorder.set_callback("on_file_size", self.on_file_size_update)
        self.recorder.set_callback("on_complete", self.on_recording_complete)
        self.recorder.set_callback("on_error", self.on_recording_error)
        self.recorder.set_callback("on_frame", self._on_frame_for_preview)
        
        self.setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        
        # 缩略图预览信号连接
        self.frame_ready.connect(self._update_preview)
        
        # 系统托盘
        self._setup_tray()
        
        # 全局快捷键
        self._setup_hotkeys()
    
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
        self.time_label.setToolTip("录制时长")
        header.addWidget(self.time_label)
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setToolTip("打开设置")
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
        
        # 预览区域（含倒计时遮罩）
        preview_container = QWidget()
        preview_container.setMinimumHeight(50)
        preview_container.setStyleSheet("background: transparent;")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        self.countdown_overlay = CountdownOverlay(preview_container)
        self.countdown_overlay.countdown_finished.connect(self._on_countdown_finished)
        
        layout.addWidget(preview_container)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.record_btn = RecordButton()
        self.record_btn.setFixedSize(64, 64)
        self.record_btn.setToolTip("开始/停止录制")
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
        self.pause_btn.setToolTip("暂停/继续录制")
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
        self.stop_btn.setToolTip("停止录制")
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
                self.settings.setValue("output_path", self.output_path)
            
            self.mic_volume = dialog.mic_volume_slider.value()
            self.sys_volume = dialog.sys_volume_slider.value()
            self.mic_enabled = dialog.mic_check.isChecked()
            self.sys_audio_enabled = dialog.sys_check.isChecked()
            self.countdown_enabled = dialog.countdown_check.isChecked()
            
            self.settings.setValue("mic_volume", str(self.mic_volume))
            self.settings.setValue("sys_volume", str(self.sys_volume))
            self.settings.setValue("mic_enabled", "true" if self.mic_enabled else "false")
            self.settings.setValue("sys_audio_enabled", "true" if self.sys_audio_enabled else "false")
            self.settings.setValue("countdown_enabled", "true" if self.countdown_enabled else "false")
            self.settings.setValue("quality", dialog.quality_combo.currentText())
            self.settings.setValue("fps", dialog.fps_combo.currentText())
            self.settings.setValue("format", dialog.format_combo.currentText())
            self.settings.sync()
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        if self.countdown_enabled:
            self._pending_recording = True
            self.status_label.setText("准备开始...")
            self.status_label.setStyleSheet("color: #f59e0b; font-size: 13px;")
            self.countdown_overlay.setGeometry(self.preview_area.geometry())
            self.countdown_overlay.start(3)
        else:
            self._do_start_recording()
    
    def _on_countdown_finished(self):
        if getattr(self, '_pending_recording', False):
            self._pending_recording = False
            self._do_start_recording()
    
    def _do_start_recording(self):
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
                # 录制中窗口置顶
                self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
                self.show()
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
        # 更新环形进度
        self.record_btn.set_ring_progress(self.elapsed_time)
    
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
            # 取消窗口置顶
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.show()
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
        # 最小化到托盘而非退出
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self._unregister_hotkeys()
            event.accept()
    
    def _setup_tray(self):
        """设置系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系统托盘不可用")
            self.tray_icon = None
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("CapSure - 视频录制")
        
        # 创建一个红色圆点图标作为系统托盘图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#E53935"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # 托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
    
    def _on_tray_activated(self, reason):
        """双击托盘图标显示窗口"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()
    
    def _show_from_tray(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.activateWindow()
        self.raise_()
    
    def _quit_app(self):
        if self.is_recording:
            self.stop_recording()
        self._unregister_hotkeys()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()
    
    def _setup_hotkeys(self):
        """注册全局快捷键"""
        self._hotkey_handles = []
        if not HAS_KEYBOARD:
            logger.info("keyboard 库未安装，全局快捷键不可用")
            return
        
        try:
            self._hotkey_handles.append(
                keyboard.add_hotkey('ctrl+shift+r', self._hotkey_record, suppress=False)
            )
            self._hotkey_handles.append(
                keyboard.add_hotkey('ctrl+shift+p', self._hotkey_pause, suppress=False)
            )
            self._hotkey_handles.append(
                keyboard.add_hotkey('ctrl+shift+s', self._hotkey_stop, suppress=False)
            )
            logger.info("全局快捷键已注册: Ctrl+Shift+R(录制) P(暂停) S(停止)")
        except Exception as e:
            logger.warning(f"全局快捷键注册失败: {e}")
    
    def _unregister_hotkeys(self):
        """注销全局快捷键"""
        if not HAS_KEYBOARD:
            return
        try:
            keyboard.unhook_all()
            self._hotkey_handles.clear()
        except Exception:
            pass
    
    def _hotkey_record(self):
        """快捷键: 开始/停止录制"""
        self.toggle_recording()
    
    def _hotkey_pause(self):
        """快捷键: 暂停/继续"""
        if self.is_recording:
            self.toggle_pause()
    
    def _hotkey_stop(self):
        """快捷键: 停止录制"""
        if self.is_recording:
            self.stop_recording()
    
    def _on_frame_for_preview(self, frame):
        """接收录制帧用于缩略图预览（每30帧更新一次）"""
        self._preview_counter = getattr(self, '_preview_counter', 0) + 1
        if self._preview_counter % 30 == 0:
            try:
                # 缩小帧以减少信号开销
                import numpy as np
                h, w = frame.shape[:2]
                scale = 160 / w
                new_w, new_h = 160, int(h * scale)
                small = frame[::max(1, h // new_h), ::max(1, w // new_w)]
                self.frame_ready.emit(small.copy())
            except Exception:
                pass
    
    def _update_preview(self, frame):
        """在主线程更新缩略图预览"""
        try:
            import numpy as np
            h, w = frame.shape[:2]
            # BGR -> RGB
            rgb = frame[:, :, ::-1].copy()
            bytes_per_line = 3 * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.preview_area.setPixmap(
                pixmap.scaled(self.preview_area.width(), self.preview_area.height(),
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )
        except Exception:
            pass


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(
                os.path.join(os.path.expanduser("~"), "Videos", "CapSure", "capsure.log"),
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
