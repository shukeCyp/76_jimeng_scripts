#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt6版本的Jimeng Scripts应用
使用PyQt6构建图形用户界面
"""

import sys
import os
import json
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import uuid
from functools import partial
import asyncio
import requests
from typing import Optional

try:
    # PyQt6 imports
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QTabWidget, QPushButton, QLabel, QTextEdit, QTableWidget, 
        QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView,
        QCheckBox, QGroupBox, QFormLayout, QLineEdit, QSpinBox,
        QRadioButton, QButtonGroup, QProgressBar, QScrollArea,
        QSplitter, QFrame, QDialog, QDialogButtonBox, QGridLayout,
        QScrollArea, QSizePolicy
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QTimer, QUrl
    from PyQt6.QtGui import QPixmap, QIcon, QDesktopServices
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("PyQt6未安装，请运行: pip install PyQt6")
    sys.exit(1)

# 导入现有的模块
from database import init_database, close_database, logger, get_config, set_config, get_all_configs, add_account, batch_add_accounts, delete_accounts, get_accounts_with_usage, add_record
from accounts_utils import get_image_account, get_video_account
# 导入图片生成工具
from jimeng_image_util import generate_image
from jimeng_utils import generate_scene, merge_prompt_with_scene
from jimeng_video_util import generate_video as generate_video_async

# 全局线程池变量
thread_pool = None
handless = False

# 全局字典用于存储生成的图片和视频信息
generated_images_dict = {}
generated_videos_dict = {}

class WorkerSignals(QObject):
    """工作线程信号类"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

class Worker(QThread):
    """工作线程类"""
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

class ClickableLabel(QLabel):
    """可点击的标签"""
    clicked = pyqtSignal(str)  # 发送选中的图片路径
    double_clicked = pyqtSignal(str)  # 发送双击的图片路径
    
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        
    def mousePressEvent(self, ev):
        """处理鼠标点击事件"""
        if ev is not None and ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        """处理鼠标双击事件"""
        if ev is not None and ev.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.image_path)
        super().mouseDoubleClickEvent(ev)

class ImageSelectionDialog(QDialog):
    """图片选择对话框"""
    def __init__(self, folder_path, current_image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择主图")
        self.setGeometry(100, 100, 800, 600)
        self.folder_path = folder_path
        self.current_image = current_image
        self.selected_image = current_image
        
        self.init_ui()
        self.load_images()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"选择主图 - {os.path.basename(self.folder_path)}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 图片滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.images_layout = QGridLayout(scroll_widget)
        self.images_layout.setSpacing(10)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # 移除了确定和取消按钮
        
    def load_images(self):
        """加载文件夹中的所有图片"""
        # 查找所有图片文件
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.webp']:
            pattern = os.path.join(self.folder_path, ext)
            image_files.extend(glob.glob(pattern))
        
        # 按网格布局显示图片
        self.image_labels = []
        col = 0
        row = 0
        
        for i, image_path in enumerate(image_files):
            # 创建图片标签
            image_label = ClickableLabel(image_path)
            image_label.setFixedSize(150, 150)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    background-color: #f8f9fa;
                    padding: 5px;
                }
            """)
            image_label.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # 连接点击信号
            image_label.clicked.connect(lambda path=image_path: self.select_image(path))
            
            # 加载图片
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                pixmap = pixmap.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(pixmap)
            
            # 如果是当前主图，添加选中样式
            if image_path == self.current_image:
                image_label.setStyleSheet("""
                    QLabel {
                        border: 3px solid #007bff;
                        border-radius: 8px;
                        background-color: #f8f9fa;
                        padding: 5px;
                    }
                """)
                self.selected_label = image_label
            
            # 添加到布局
            self.images_layout.addWidget(image_label, row, col)
            self.image_labels.append((image_label, image_path))
            
            col += 1
            if col >= 4:  # 每行显示4张图片
                col = 0
                row += 1
    
    def select_image(self, image_path):
        """选择图片并关闭对话框"""
        self.selected_image = image_path
        self.accept()  # 自动关闭对话框

class ImagePreviewDialog(QDialog):
    """单图预览对话框，支持滚动查看较大图片"""
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查看图片")

        vbox = QVBoxLayout(self)
        self.scroll = QScrollArea(self)
        # 开启自适应视口尺寸，后续按高度等比缩放，避免垂直滚动
        self.scroll.setWidgetResizable(True)
        # 禁用垂直滚动，仅根据需要允许水平滚动
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel(container)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 确保不按控件尺寸缩放图片
        self.image_label.setScaledContents(False)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        if image_path and os.path.exists(image_path):
            self.orig_pixmap = QPixmap(image_path)
            self.image_label.setPixmap(self.orig_pixmap)
            # 标签按图片原始尺寸调整
            self.image_label.adjustSize()
            # 根据图片原始尺寸设置对话框大小，且不超过屏幕可用区域
            try:
                from PyQt6.QtGui import QGuiApplication
                screen = QGuiApplication.primaryScreen()
                if screen is not None:
                    avail = screen.availableGeometry()
                    max_w = int(avail.width() * 0.9)
                    max_h = int(avail.height() * 0.9)
                else:
                    max_w, max_h = 1200, 900
            except Exception:
                max_w, max_h = 1200, 900

            desired_w = min(self.orig_pixmap.width() + 40, max_w)
            desired_h = min(self.orig_pixmap.height() + 80, max_h)
            self.resize(desired_w, desired_h)
            # 首次显示后按高度等比缩放，避免出现上下滚动
            QTimer.singleShot(0, self._fit_to_height)
        else:
            self.orig_pixmap = None
            self.image_label.setText("无法加载图片")

        container_layout.addWidget(self.image_label)
        self.scroll.setWidget(container)
        vbox.addWidget(self.scroll)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        btn_box.rejected.connect(self.reject)
        vbox.addWidget(btn_box)

    def _fit_to_height(self):
        """将图片按视口高度等比缩放，避免垂直滚动，仅可能产生水平滚动"""
        try:
            if not self.orig_pixmap or self.orig_pixmap.isNull():
                return
            viewport_h = self.scroll.viewport().height()
            if viewport_h <= 0:
                return
            orig_w = self.orig_pixmap.width()
            orig_h = self.orig_pixmap.height()
            # 如果原图高度小于视口高度，则保持原图大小
            target_h = min(orig_h, viewport_h)
            # 根据目标高度计算目标宽度，保持纵横比
            scale_ratio = target_h / max(orig_h, 1)
            target_w = max(int(orig_w * scale_ratio), 1)
            scaled = self.orig_pixmap.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.image_label.setFixedSize(scaled.size())
        except Exception as e:
            logger.error(f"预览对话框按高度适配失败: {e}")

class BatchAddDialog(QDialog):
    """批量添加账号对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量添加账号")
        self.setGeometry(200, 200, 500, 400)
        
        layout = QVBoxLayout(self)
        
        # 说明文本
        info_label = QLabel("请输入账号信息，每行一个，格式为 邮箱----密码")
        layout.addWidget(info_label)
        
        # 文本输入框
        self.accounts_text = QTextEdit()
        self.accounts_text.setPlaceholderText("例如:\nuser1@example.com----password1\nuser2@example.com----password2")
        layout.addWidget(self.accounts_text)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_accounts_data(self):
        """获取账号数据"""
        return self.accounts_text.toPlainText().split('\n')

class MainWindow(QMainWindow):
    """主窗口类"""
    image_generated_signal = pyqtSignal(int, str)
    video_generated_signal = pyqtSignal(int, str)
    status_message_signal = pyqtSignal(str)
    # 新增：主线程重置按钮与刷新账号列表的信号
    reset_button_signal = pyqtSignal(object, str, str)
    refresh_accounts_signal = pyqtSignal()
    
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jimeng Scripts - PyQt6版本")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化数据库
        if not init_database():
            QMessageBox.critical(self, "错误", "数据库初始化失败，程序退出")
            sys.exit(1)
        
        # 从数据库配置中获取线程池大小
        max_threads_str = get_config('max_threads', '5')
        try:
            max_threads = int(max_threads_str)
        except (ValueError, TypeError):
            max_threads = 5
            logger.warning(f"无法解析线程池大小配置，使用默认值: {max_threads}")
        
        # 创建线程池
        global thread_pool
        thread_pool = ThreadPoolExecutor(max_workers=max_threads)
        logger.info(f"线程池已创建，最大线程数: {max_threads}")
        
        # 初始化变量
        self.current_files = []
        self.current_folder_path = ""
        # 失败重试计数器（每行独立，最多重试三次）
        self._image_retry_counts = {}
        self._video_retry_counts = {}

        # 统一生成文件的保存目录（项目根目录）
        try:
            self.project_root = Path(__file__).resolve().parent.parent
            self.generated_images_dir = self.project_root / 'generated_images'
            self.generated_videos_dir = self.project_root / 'generated_videos'
            self.generated_images_dir.mkdir(parents=True, exist_ok=True)
            self.generated_videos_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"生成图片保存目录: {self.generated_images_dir}")
            logger.info(f"生成视频保存目录: {self.generated_videos_dir}")
        except Exception as e:
            logger.error(f"创建生成目录失败: {e}")
        
        # 创建UI
        self.init_ui()
        
        # 加载配置
        self.load_configs()

        self.image_generated_signal.connect(self.add_image_to_gallery, Qt.ConnectionType.QueuedConnection)
        self.video_generated_signal.connect(self._update_video_cell, Qt.ConnectionType.QueuedConnection)
        self.status_message_signal.connect(self._update_status_bar, Qt.ConnectionType.QueuedConnection)
        # 新增：确保在主线程执行按钮重置与账号刷新
        self.reset_button_signal.connect(self._reset_generate_button, Qt.ConnectionType.QueuedConnection)
        self.refresh_accounts_signal.connect(self.refresh_accounts, Qt.ConnectionType.QueuedConnection)

    def _update_status_bar(self, message):
        status_bar = self.statusBar()
        if status_bar:
            status_bar.showMessage(message)
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个标签页
        self.create_home_tab()
        self.create_accounts_tab()
        self.create_settings_tab()
        
        # 创建状态栏
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage("就绪")
        
    def create_home_tab(self):
        """创建首页标签页"""
        home_widget = QWidget()
        layout = QVBoxLayout(home_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建顶部控制区域
        control_group = QGroupBox("控制面板")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(10)
        
        self.import_btn = QPushButton("导入文件夹")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.import_btn.clicked.connect(self.import_folder)
        
        self.batch_image_btn = QPushButton("图片批量生成")
        self.batch_image_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.batch_image_btn.clicked.connect(self.batch_generate_images)
        
        self.batch_video_btn = QPushButton("视频批量生成")
        self.batch_video_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        self.batch_video_btn.clicked.connect(self.batch_generate_videos)
        
        control_layout.addWidget(self.import_btn)
        control_layout.addWidget(self.batch_image_btn)
        control_layout.addWidget(self.batch_video_btn)
        control_layout.addStretch()
        
        # 文件列表区域 - 占据更多空间
        files_group = QGroupBox("文件列表")
        files_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        files_layout = QVBoxLayout(files_group)
        files_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建表格
        self.files_table = QTableWidget(0, 4)
        self.files_table.setHorizontalHeaderLabels(["主图", "模特图", "视频", "操作"])
        header = self.files_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v_header = self.files_table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        self.files_table.setAlternatingRowColors(True)
        self.files_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                color: #495057;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #dee2e6;
            }
        """)
        
        # 设置表格列宽比例
        header = self.files_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 主图列
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 模特图列
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 视频列
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 操作列
        self.files_table.setColumnWidth(0, 160)  # 主图列宽度
        self.files_table.setColumnWidth(2, 140)  # 视频列宽度
        self.files_table.setColumnWidth(3, 140)  # 操作列宽度
        
        files_layout.addWidget(self.files_table)
        
        # 添加到主布局 - 移除了提示词区域
        layout.addWidget(control_group)
        layout.addWidget(files_group, 1)  # 文件列表区域占据更多空间
        
        self.tab_widget.addTab(home_widget, "首页")
        
    def create_accounts_tab(self):
        """创建账号管理标签页"""
        accounts_widget = QWidget()
        layout = QVBoxLayout(accounts_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 控制按钮区域
        control_group = QGroupBox("账号操作")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(10)
        
        self.add_account_btn = QPushButton("添加账号")
        self.add_account_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.add_account_btn.clicked.connect(self.add_account)
        
        self.batch_add_btn = QPushButton("批量添加")
        self.batch_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.batch_add_btn.clicked.connect(self.batch_add_accounts)
        
        self.delete_account_btn = QPushButton("删除选中")
        self.delete_account_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.delete_account_btn.clicked.connect(self.delete_selected_accounts)
        
        self.refresh_accounts_btn = QPushButton("刷新列表")
        self.refresh_accounts_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        self.refresh_accounts_btn.clicked.connect(self.refresh_accounts)
        
        # 新增：全选复选框
        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.setToolTip("选择/取消选择所有账号")
        self.select_all_checkbox.stateChanged.connect(self.on_accounts_select_all_toggled)
        
        control_layout.addWidget(self.add_account_btn)
        control_layout.addWidget(self.batch_add_btn)
        control_layout.addWidget(self.delete_account_btn)
        control_layout.addWidget(self.refresh_accounts_btn)
        control_layout.addWidget(self.select_all_checkbox)
        control_layout.addStretch()
        
        # 账号列表区域
        accounts_list_group = QGroupBox("账号列表")
        accounts_list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        accounts_list_layout = QVBoxLayout(accounts_list_group)
        accounts_list_layout.setContentsMargins(10, 10, 10, 10)
        
        # 账号表格
        self.accounts_table = QTableWidget(0, 5)
        self.accounts_table.setHorizontalHeaderLabels(["选择", "ID", "用户名", "当日图片数", "当日视频数"])
        header = self.accounts_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v_header = self.accounts_table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px;
                font-weight: bold;
                border: 1px solid #dee2e6;
            }
        """)
        
        # 设置表格列宽比例
        header = self.accounts_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 选择列
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # ID列
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 用户名列
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 当日图片数列
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 当日视频数列
        self.accounts_table.setColumnWidth(0, 60)   # 选择列宽度
        self.accounts_table.setColumnWidth(1, 80)   # ID列宽度
        self.accounts_table.setColumnWidth(3, 100)  # 当日图片数列宽度
        self.accounts_table.setColumnWidth(4, 100)  # 当日视频数列宽度
        
        accounts_list_layout.addWidget(self.accounts_table)
        
        layout.addWidget(control_group)
        layout.addWidget(accounts_list_group)
        
        self.tab_widget.addTab(accounts_widget, "账号管理")
        
        # 新增：首次打开自动加载账号列表
        try:
            QTimer.singleShot(0, self.refresh_accounts)
        except Exception:
            # 兜底直接调用
            self.refresh_accounts()
        
    def create_settings_tab(self):
        """创建设置标签页"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 配置设置
        config_group = QGroupBox("基本配置")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                font-size: 14px;
            }
        """)
        config_layout = QFormLayout(config_group)
        config_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        config_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        config_layout.setHorizontalSpacing(20)
        config_layout.setVerticalSpacing(15)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        config_layout.addRow(QLabel("API Key:"), self.api_key_edit)
        
        self.api_proxy_edit = QLineEdit()
        self.api_proxy_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        config_layout.addRow(QLabel("API Proxy:"), self.api_proxy_edit)
        
        self.model_edit = QLineEdit()
        self.model_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        config_layout.addRow(QLabel("Model:"), self.model_edit)
        
        # 图片和视频提示词
        self.settings_image_prompt_edit = QTextEdit()
        self.settings_image_prompt_edit.setMaximumHeight(80)
        self.settings_image_prompt_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        config_layout.addRow(QLabel("图片提示词:"), self.settings_image_prompt_edit)
        
        self.settings_video_prompt_edit = QTextEdit()
        self.settings_video_prompt_edit.setMaximumHeight(80)
        self.settings_video_prompt_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        config_layout.addRow(QLabel("视频提示词:"), self.settings_video_prompt_edit)
        
        # 视频时长设置
        video_duration_layout = QHBoxLayout()
        video_duration_layout.setSpacing(20)
        self.video_duration_5 = QRadioButton("5秒")
        self.video_duration_5.setStyleSheet("font-size: 13px;")
        self.video_duration_10 = QRadioButton("10秒")
        self.video_duration_10.setStyleSheet("font-size: 13px;")
        self.video_duration_group = QButtonGroup()
        self.video_duration_group.addButton(self.video_duration_5)
        self.video_duration_group.addButton(self.video_duration_10)
        video_duration_layout.addWidget(self.video_duration_5)
        video_duration_layout.addWidget(self.video_duration_10)
        video_duration_layout.addStretch()
        config_layout.addRow(QLabel("视频时长:"), video_duration_layout)
        
        # 线程和限制设置
        limits_group = QGroupBox("限制设置")
        limits_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                font-size: 14px;
            }
        """)
        limits_layout = QFormLayout(limits_group)
        limits_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        limits_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        limits_layout.setHorizontalSpacing(20)
        limits_layout.setVerticalSpacing(15)
        
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 50)
        self.max_threads_spin.setValue(5)
        self.max_threads_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
        """)
        limits_layout.addRow(QLabel("最大线程数:"), self.max_threads_spin)
        
        self.daily_video_limit_spin = QSpinBox()
        self.daily_video_limit_spin.setRange(1, 100)
        self.daily_video_limit_spin.setValue(2)
        self.daily_video_limit_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
        """)
        limits_layout.addRow(QLabel("单账号单日视频数:"), self.daily_video_limit_spin)
        
        self.daily_image_limit_spin = QSpinBox()
        self.daily_image_limit_spin.setRange(1, 1000)
        self.daily_image_limit_spin.setValue(10)
        self.daily_image_limit_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
        """)
        limits_layout.addRow(QLabel("单账号单日图片数:"), self.daily_image_limit_spin)
        
        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        
        # 居中保存按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        
        layout.addWidget(config_group)
        layout.addWidget(limits_group)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "设置")
        
    def import_folder(self):
        """导入文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            try:
                files = self._get_folder_images(folder_path)
                if files:
                    self.current_folder_path = folder_path
                    self.current_files = files
                    self.display_folder_content(files)
                    status_bar = self.statusBar()
                    if status_bar is not None:
                        status_bar.showMessage(f"成功导入文件夹，找到 {len(files)} 个子文件夹")
                else:
                    QMessageBox.warning(self, "警告", "未找到有效的图片文件")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入文件夹失败: {str(e)}")
                
    def _get_folder_images(self, folder_path):
        """获取文件夹中的图片文件"""
        import os
        import glob
        import json
        
        logger.info(f"开始遍历文件夹: {folder_path}")
        
        # 验证文件夹路径是否存在
        if not os.path.exists(folder_path):
            logger.error(f"文件夹路径不存在: {folder_path}")
            return []
        
        # 验证是否为文件夹
        if not os.path.isdir(folder_path):
            logger.error(f"路径不是文件夹: {folder_path}")
            return []
        
        # 查找 images 文件夹
        images_folder = os.path.join(folder_path, "images")
        items_folder = os.path.join(folder_path, "items")
        
        logger.info(f"images文件夹路径: {images_folder}")
        logger.info(f"items文件夹路径: {items_folder}")
        
        if not os.path.exists(images_folder):
            logger.error(f"未找到 images 文件夹: {images_folder}")
            return []
        
        if not os.path.exists(items_folder):
            logger.error(f"未找到 items 文件夹: {items_folder}")
            return []
        
        files = []
        
        # 遍历 images 文件夹中的所有子文件夹
        try:
            subdirs = os.listdir(images_folder)
            logger.info(f"images文件夹中的子文件夹数量: {len(subdirs)}")
            
            for subdir in subdirs:
                subdir_path = os.path.join(images_folder, subdir)
                if os.path.isdir(subdir_path):
                    logger.info(f"处理子文件夹: {subdir_path}")
                    
                    # 查找该子文件夹中的所有图片文件
                    image_files = []
                    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.webp']:
                        pattern = os.path.join(subdir_path, ext)
                        image_files.extend(glob.glob(pattern))
                    
                    logger.info(f"子文件夹 {subdir} 中找到图片文件数量: {len(image_files)}")
                    
                    if image_files:
                        # 取第一张图片作为默认主图
                        main_image = image_files[0]
                        file_name = os.path.basename(subdir_path)
                        
                        logger.info(f"子文件夹 {subdir} 的主图: {main_image}")
                        
                        # 查找对应的 JSON 文件（如果存在）
                        json_file = os.path.join(items_folder, f"{subdir}.json")
                        title = subdir  # 默认使用文件夹名作为标题
                        if os.path.exists(json_file):
                            try:
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    # 尝试从 JSON 中获取标题
                                    if isinstance(data, dict):
                                        title = data.get('title', data.get('name', subdir))
                                logger.info(f"从JSON文件 {json_file} 中获取标题: {title}")
                            except Exception as e:
                                logger.warning(f"读取 JSON 文件失败 {json_file}: {e}")
                        else:
                            logger.info(f"未找到对应的JSON文件: {json_file}")
                        
                        # 添加文件夹路径信息
                        file_info = {
                            'name': title,
                            'main_image': main_image,
                            'folder_path': subdir_path,
                            'uniqueId': f"{subdir}_{int(time.time())}",  # 生成唯一ID
                            'selected_model_image': None  # 当前选中的模特图（未选择/未生成时为None）
                        }
                        
                        files.append(file_info)
                        logger.info(f"添加文件信息: {file_info}")
                    else:
                        logger.info(f"子文件夹 {subdir} 中没有找到图片文件")
        except Exception as e:
            logger.error(f"遍历 images 文件夹时出错: {e}")
            return []
        
        logger.info(f"总共找到 {len(files)} 个文件夹")
        return files
                
    def display_folder_content(self, files):
        """显示文件夹内容"""
        self.files_table.setRowCount(len(files))
        
        # 设置表格行高
        v_header = self.files_table.verticalHeader()
        if v_header is not None:
            v_header.setDefaultSectionSize(180)
        
        for row, file in enumerate(files):
            # 主图列 - 改进布局和样式
            main_image_widget = QWidget()
            main_layout = QVBoxLayout(main_image_widget)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(5)
            
            # 图片显示区域
            image_label = ClickableLabel(file['main_image'])
            image_label.setFixedSize(140, 140)
            image_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    background-color: #f8f9fa;
                    padding: 5px;
                }
            """)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # 连接点击信号
            image_label.clicked.connect(lambda path, r=row, f=file: self.on_main_image_clicked(r, f))
            
            # 加载图片
            if os.path.exists(file['main_image']):
                pixmap = QPixmap(file['main_image'])
                pixmap = pixmap.scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("无图片")
                image_label.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #ced4da;
                        border-radius: 8px;
                        background-color: #f8f9fa;
                        color: #6c757d;
                        font-size: 12px;
                        padding: 5px;
                    }
                """)
            
            # 文件名显示
            name_label = QLabel(file['name'][:20] + "..." if len(file['name']) > 20 else file['name'])
            name_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #495057;
                    qproperty-alignment: AlignCenter;
                }
            """)
            name_label.setWordWrap(True)
            
            main_layout.addWidget(image_label, 0, Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignCenter)
            
            self.files_table.setCellWidget(row, 0, main_image_widget)
            
            # 模特图列 - 水平排列
            model_images_widget = QWidget()
            model_layout = QHBoxLayout(model_images_widget)
            model_layout.setContentsMargins(5, 5, 5, 5)
            model_layout.setSpacing(10)
            
            # 创建4个水平排列的模特图展示区域
            for i in range(4):
                model_label = ClickableLabel("")
                model_label.setProperty("row", row)
                model_label.setProperty("slot_index", i)
                model_label.setFixedSize(100, 100)  # 增大尺寸到100x100
                model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                model_label.setStyleSheet("""
                    QLabel {
                        border: 1px dashed #ced4da;
                        border-radius: 4px;
                        background-color: #f8f9fa;
                        color: #6c757d;
                        font-size: 11px;
                    }
                """)
                model_label.setText(f"模特图{i+1}\n待生成")
                # 连接单击和双击事件
                model_label.clicked.connect(lambda path, r=row, lbl=model_label: self.on_model_image_clicked(r, lbl, path))
                model_label.double_clicked.connect(lambda path, r=row, lbl=model_label: self.on_model_image_double_clicked(r, lbl, path))
                model_layout.addWidget(model_label)
            
            self.files_table.setCellWidget(row, 1, model_images_widget)

            # 默认选择第一个模型图
            first_item = model_layout.itemAt(0)
            if first_item is not None and first_item.widget():
                self._set_model_label_selected(first_item.widget(), True)
            
            # 视频列 - 改进布局
            video_widget = QWidget()
            video_layout = QVBoxLayout(video_widget)
            video_layout.setContentsMargins(5, 20, 5, 20)
            video_layout.setSpacing(10)
            
            # 视频展示区域（可点击打开系统播放器）
            video_label = ClickableLabel("")
            video_label.setFixedSize(100, 80)
            video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            video_label.setStyleSheet("""
                QLabel {
                    border: 1px dashed #ced4da;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                    color: #6c757d;
                    font-size: 11px;
                }
            """)
            video_label.setText("视频\n待生成")
            # 连接点击事件：打开系统默认视频播放器
            video_label.clicked.connect(lambda path, r=row: self.on_video_label_clicked(r, path))
            
            # 视频状态
            video_status = QLabel("未生成")
            video_status.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #6c757d;
                    qproperty-alignment: AlignCenter;
                }
            """)
            
            video_layout.addWidget(video_label, 0, Qt.AlignmentFlag.AlignCenter)
            video_layout.addWidget(video_status, 0, Qt.AlignmentFlag.AlignCenter)
            
            self.files_table.setCellWidget(row, 2, video_widget)
            
            # 操作列
            action_widget = QWidget()
            action_layout = QVBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 15, 5, 15)
            action_layout.setSpacing(10)
            
            # 创建按钮并保存引用以避免lambda闭包问题
            generate_image_btn = QPushButton("生成图片")
            generate_image_btn.setFixedWidth(100)
            generate_image_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            # 设定对象名称，便于批量操作检索
            generate_image_btn.setObjectName("generate_image_btn")
            # 保存按钮引用以便后续更新状态
            generate_image_btn.setProperty("row", row)
            # 使用functools.partial避免闭包问题
            from functools import partial
            generate_image_btn.clicked.connect(partial(self.generate_image, row, generate_image_btn))
            
            generate_video_btn = QPushButton("生成视频")
            generate_video_btn.setFixedWidth(100)
            generate_video_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1e7e34;
                }
            """)
            # 设定对象名称，便于批量操作检索
            generate_video_btn.setObjectName("generate_video_btn")
            generate_video_btn.setProperty("row", row)
            generate_video_btn.clicked.connect(partial(self.generate_video, row, generate_video_btn))
            # 初始状态：未有模特图，禁用视频生成按钮
            try:
                init_selected = file.get('selected_model_image')
                enabled = bool(init_selected and os.path.exists(init_selected))
                generate_video_btn.setEnabled(enabled)
                if not enabled:
                    generate_video_btn.setToolTip("请先生成并选择模特图")
            except Exception:
                generate_video_btn.setEnabled(False)
                generate_video_btn.setToolTip("请先生成并选择模特图")
            
            delete_btn = QPushButton("删除")
            delete_btn.setFixedWidth(100)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            delete_btn.clicked.connect(partial(self.delete_item, row))
            
            action_layout.addWidget(generate_image_btn, 0, Qt.AlignmentFlag.AlignCenter)
            action_layout.addWidget(generate_video_btn, 0, Qt.AlignmentFlag.AlignCenter)
            action_layout.addWidget(delete_btn, 0, Qt.AlignmentFlag.AlignCenter)
            action_layout.addStretch()
            
            self.files_table.setCellWidget(row, 3, action_widget)
            
            # 设置行的样式
            self.files_table.setRowHeight(row, 180)

    def on_main_image_clicked(self, row, file_info):
        """处理主图点击事件"""
        # 创建图片选择对话框
        dialog = ImageSelectionDialog(file_info['folder_path'], file_info['main_image'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新选中的图片
            selected_image = dialog.selected_image
            if selected_image != file_info['main_image']:
                # 更新文件信息
                self.current_files[row]['main_image'] = selected_image
                
                # 更新表格中的图片显示
                main_image_widget = self.files_table.cellWidget(row, 0)
                if main_image_widget:
                    # 找到图片标签并更新图片
                    layout = main_image_widget.layout()
                    if layout and layout.count() > 0:
                        item = layout.itemAt(0)
                        if item is not None:
                            image_label = item.widget()
                            if isinstance(image_label, ClickableLabel) and os.path.exists(selected_image):
                                pixmap = QPixmap(selected_image)
                                pixmap = pixmap.scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                image_label.setPixmap(pixmap)
                                image_label.image_path = selected_image

    def generate_image(self, row, button):
        """生成图片"""
        if row < len(self.current_files):
            file = self.current_files[row]
            # 从数据库获取提示词
            prompt = get_config('image_prompt', '')
            
            if not prompt:
                QMessageBox.warning(self, "警告", "请输入图片提示词")
                return
                
            # 重置该行的重试计数
            try:
                self._image_retry_counts[row] = 0
            except Exception:
                pass

            # 更新按钮状态
            button.setText("正在生成")
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            
            # 显示进度提示
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage("正在生成图片...")

            # 使用线程池执行任务
            global thread_pool
            if thread_pool:
                # 提交任务到线程池
                future = thread_pool.submit(self._generate_image_task, file['main_image'], prompt, row)
                # 添加回调处理结果（保持在主线程更新UI）
                future.add_done_callback(lambda f, btn=button, r=row: self._on_image_generate_finished(f, btn, r))
            else:
                QMessageBox.critical(self, "错误", "线程池不可用")
                # 恢复按钮状态
                self._reset_generate_button(button, "生成图片", "#007bff")

    def _set_model_label_selected(self, label: QLabel, selected: bool):
        """设置模型图标签选中/未选中样式"""
        if selected:
            label.setStyleSheet("""
                QLabel {
                    border: 2px solid #007bff;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                    color: #495057;
                    font-size: 11px;
                }
            """)
        else:
            label.setStyleSheet("""
                QLabel {
                    border: 1px dashed #ced4da;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                    color: #6c757d;
                    font-size: 11px;
                }
            """)

    def _update_video_button_state(self, row: int):
        """根据是否选择/生成模特图，动态启用/禁用该行视频生成按钮"""
        try:
            action_widget = self.files_table.cellWidget(row, 3)
            if not action_widget:
                return
            layout = action_widget.layout()
            if not layout:
                return
            video_btn = None
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QPushButton):
                    w = item.widget()
                    if w.objectName() == "generate_video_btn":
                        video_btn = w
                        break
            if video_btn is None:
                return

            selected_path = None
            if 0 <= row < len(self.current_files):
                selected_path = self.current_files[row].get('selected_model_image')
            enabled = bool(selected_path and os.path.exists(selected_path))
            video_btn.setEnabled(enabled)
            video_btn.setToolTip("生成视频" if enabled else "请先生成并选择模特图")
        except Exception as e:
            logger.error(f"更新视频按钮状态失败: {e}")

    def on_model_image_clicked(self, row: int, label: QLabel, image_path: str):
        """单击选择模型图"""
        try:
            model_widget = self.files_table.cellWidget(row, 1)
            if not model_widget:
                return
            layout = model_widget.layout()
            if not layout:
                return
            # 清除该行所有标签的选中状态
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    self._set_model_label_selected(item.widget(), False)
            # 设置当前标签为选中
            self._set_model_label_selected(label, True)
            # 记录所选模型图路径（仅当存在有效路径时）
            try:
                if 0 <= row < len(self.current_files):
                    self.current_files[row]['selected_model_image'] = image_path if (image_path and os.path.exists(image_path)) else None
                    # 选择变化后，更新该行的视频生成按钮状态
                    self._update_video_button_state(row)
            except Exception as e:
                logger.error(f"记录选中模型图路径失败: {e}")
        except Exception as e:
            logger.error(f"选择模型图失败: {e}")

    def on_model_image_double_clicked(self, row: int, label: QLabel, image_path: str):
        """双击打开预览对话框查看模型图"""
        try:
            if image_path and os.path.exists(image_path):
                dialog = ImagePreviewDialog(image_path, self)
                dialog.exec()
            else:
                QMessageBox.information(self, "提示", "该槽位暂无图片")
        except Exception as e:
            logger.error(f"预览模型图失败: {e}")

    def _generate_image_task(self, image_path, prompt, row):
        """在子线程中执行的实际图片生成任务"""
        try:
            # 获取可用的图片账号
            account_info = get_image_account()
            if not account_info:
                return {"success": False, "error": "没有可用的图片账号"}

            # 在生成图片前，调用AI基于图片与标题生成展示场景
            try:
                title = ""
                if 0 <= row < len(self.current_files):
                    title = str(self.current_files[row].get('name', ''))
                scene = generate_scene(image_path, title)
                effective_prompt = merge_prompt_with_scene(prompt or '', title, scene or '')
            except Exception as e:
                # 若场景生成或占位填充失败，则继续使用原始提示词
                logger.warning(f"场景生成或占位填充失败，将使用原始提示词: {e}")
                effective_prompt = prompt

            # 调用实际的图片生成函数
            # 使用asyncio.run()运行异步函数
            result = asyncio.run(generate_image(
                cookies=account_info['cookies'],
                username=account_info['username'],
                password=account_info['password'],
                prompt=effective_prompt,
                image_path=image_path,
                headless=True,
                account_id=account_info['id']
            ))
            
            # 如果生成成功，添加记录到数据库
            if result.get('success'):
                add_record(account_info['id'], 1)  # 1代表图片类型
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _on_image_generate_finished(self, future, button, row):
        """图片生成完成回调（支持失败自动重试，最多三次）"""
        try:
            result = future.result()
            if result.get('success'):
                self.status_message_signal.emit("图片生成完成")
                self._show_message_in_main_thread("成功", "图片生成完成")
                # 如果有生成的图片URL，更新UI显示
                image_urls = result.get('image_urls', [])
                if image_urls:
                    if row < len(self.current_files):
                        file_info = self.current_files[row]
                        folder_path = str(self.generated_images_dir)
                        # 下载并保存图片
                        for i, url in enumerate(image_urls):
                            try:
                                response = requests.get(url, stream=True)
                                if response.status_code == 200:
                                    new_image_name = f"generated_{int(time.time())}_{i+1}.jpg"
                                    new_image_path = os.path.join(folder_path, new_image_name)
                                    with open(new_image_path, 'wb') as f:
                                        for chunk in response.iter_content(1024):
                                            f.write(chunk)
                                    # 发出信号，在主线程中更新UI
                                    self.image_generated_signal.emit(row, new_image_path)
                            except Exception as e:
                                logger.error(f"下载或保存图片失败: {e}")
            else:
                # 失败：尝试重试（最多三次）
                attempts = self._image_retry_counts.get(row, 0)
                if attempts < 3:
                    self._image_retry_counts[row] = attempts + 1
                    try:
                        prompt = get_config('image_prompt', '')
                        if not prompt or row >= len(self.current_files):
                            raise RuntimeError('缺少提示词或行越界')
                        image_path = self.current_files[row].get('main_image')
                        if not image_path or not os.path.exists(image_path):
                            raise RuntimeError('主图路径无效，无法重试')
                        global thread_pool
                        if not thread_pool:
                            raise RuntimeError('线程池不可用')
                        # 保持按钮禁用与“正在生成”状态，不进行重置
                        self.status_message_signal.emit(f"图片生成失败，重试第{attempts + 1}次")
                        future2 = thread_pool.submit(self._generate_image_task, image_path, prompt, row)
                        future2.add_done_callback(lambda f, btn=button, r=row: self._on_image_generate_finished(f, btn, r))
                        return
                    except Exception as e:
                        err = result.get('error', '未知错误')
                        self.status_message_signal.emit(f"图片生成失败，无法重试: {err}")
                        self._show_message_in_main_thread("失败", f"图片生成失败: {err}")
                else:
                    err = result.get('error', '未知错误')
                    self.status_message_signal.emit("图片生成失败，已达最大重试次数")
                    self._show_message_in_main_thread("失败", f"图片生成失败(已重试3次): {err}")
        except Exception as e:
            self._show_message_in_main_thread("失败", f"处理生成结果时出错: {e}")
            self.status_message_signal.emit("处理结果失败")
        # 在成功或最终失败后，才重置按钮与刷新账号列表
        try:
            is_success = False
            try:
                is_success = bool(future.result().get('success'))
            except Exception:
                is_success = False
            attempts = self._image_retry_counts.get(row, 0)
            if is_success or attempts >= 3:
                if row in self._image_retry_counts:
                    del self._image_retry_counts[row]
                self.reset_button_signal.emit(button, "生成图片", "#007bff")
                self.refresh_accounts_signal.emit()
        except Exception:
            pass

    def add_image_to_gallery(self, row, image_path):
        """将图片添加到指定行的图库中"""
        logger.info(f"add_image_to_gallery called on thread: {threading.current_thread().name} for row {row}")
        try:
            model_widget = self.files_table.cellWidget(row, 1)
            if not model_widget:
                logger.error(f"No cell widget found at row {row}, column 1.")
                return

            layout = model_widget.layout()
            if not layout:
                logger.error(f"No layout found in cell widget at row {row}, column 1.")
                return

            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    image_label = item.widget()
                    if isinstance(image_label, ClickableLabel):
                        current_pixmap = image_label.pixmap()
                        is_empty = (current_pixmap is None) or getattr(current_pixmap, "isNull", lambda: True)()
                        if is_empty:
                            logger.info(f"Found empty image label at index {i} in row {row}. Setting pixmap.")
                            pixmap = QPixmap(image_path)
                            pixmap = pixmap.scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            image_label.setPixmap(pixmap)
                            image_label.setText("")
                            image_label.image_path = image_path
                            # 若尚未选择模特图，则自动选择第一个生成的
                            try:
                                if 0 <= row < len(self.current_files):
                                    current_selected = self.current_files[row].get('selected_model_image')
                                    if not current_selected or not os.path.exists(current_selected):
                                        # 清除其他选中样式
                                        for j in range(layout.count()):
                                            it2 = layout.itemAt(j)
                                            if it2 and it2.widget():
                                                self._set_model_label_selected(it2.widget(), False)
                                        # 设置当前为选中
                                        self._set_model_label_selected(image_label, True)
                                        self.current_files[row]['selected_model_image'] = image_path
                                        # 更新该行的视频生成按钮状态
                                        self._update_video_button_state(row)
                            except Exception as e:
                                logger.error(f"自动选择首个生成模特图失败: {e}")
                            return

            logger.warning(f"No empty image label found in row {row}.")

        except Exception as e:
            logger.error(f"添加图片到图库失败: {e}")

    def _update_video_cell(self, row, video_path):
        """在主线程更新指定行的视频单元格展示与状态"""
        try:
            # 记录到数据结构中，便于后续操作
            if 0 <= row < len(self.current_files):
                self.current_files[row]['video_path'] = video_path

            video_widget = self.files_table.cellWidget(row, 2)
            if video_widget is None:
                logger.error(f"Row {row} 的视频单元未找到")
                return

            v_layout = video_widget.layout()
            if v_layout is None or v_layout.count() < 2:
                logger.error(f"Row {row} 的视频单元布局异常")
                return

            video_label = v_layout.itemAt(0).widget()
            video_status = v_layout.itemAt(1).widget()
            if isinstance(video_status, QLabel):
                video_status.setText("已生成")
            if isinstance(video_label, QLabel):
                # 展示用于生成视频的图片作为预览
                preview_path = None
                if 0 <= row < len(self.current_files):
                    preview_path = self.current_files[row].get('selected_model_image')
                    if not preview_path or not os.path.exists(preview_path):
                        preview_path = self.current_files[row].get('main_image')
                if preview_path and os.path.exists(preview_path):
                    try:
                        pixmap = QPixmap(preview_path)
                        pixmap = pixmap.scaled(video_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        video_label.setPixmap(pixmap)
                        video_label.setText("")
                        video_label.setToolTip("点击播放")
                    except Exception as e:
                        logger.error(f"设置视频预览图失败: {e}")
                        video_label.setText("视频\n已生成")
                else:
                    video_label.setText("视频\n已生成")

                # 记录路径以便点击时打开
                setattr(video_label, 'video_path', video_path)
                # 对于可点击标签，设置其image_path用于clicked信号传递
                try:
                    video_label.image_path = video_path
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"更新视频单元格失败: {e}")

    def on_video_label_clicked(self, row: int, video_path: str):
        """点击视频标签后，调用系统播放器播放该视频"""
        try:
            # 如果未通过信号获取到路径，回退到当前行记录
            if not video_path and 0 <= row < len(self.current_files):
                video_path = self.current_files[row].get('video_path', '')

            if video_path and os.path.exists(video_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(video_path))
            else:
                QMessageBox.information(self, "提示", "该行视频尚未生成或路径无效")
        except Exception as e:
            logger.error(f"打开视频失败: {e}")
            QMessageBox.critical(self, "错误", f"打开视频失败: {e}")

    def _reset_generate_button(self, button, text, color):
        """重置生成按钮状态"""
        if button:
            button.setText(text)
            button.setEnabled(True)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(color)};
                }}
            """)

    def _darken_color(self, color):
        """简单颜色加深函数"""
        if color == "#007bff":
            return "#0056b3"
        elif color == "#28a745":
            return "#1e7e34"
        else:
            return color

    def generate_video(self, row, button):
        """生成视频"""
        if row < len(self.current_files):
            file = self.current_files[row]
            # 从数据库获取提示词
            prompt = get_config('video_prompt', '')
            
            if not prompt:
                QMessageBox.warning(self, "警告", "请输入视频提示词")
                return

            # 重置该行的重试计数
            try:
                self._video_retry_counts[row] = 0
            except Exception:
                pass

            # 预检查：账号可用性
            try:
                account_check = get_video_account()
            except Exception as e:
                account_check = None
                logger.error(f"获取视频账号失败: {e}")
            if not account_check:
                QMessageBox.warning(self, "警告", "没有可用的视频账号")
                return

            # 预检查：选中模特图存在性
            image_path = file.get('selected_model_image')
            if not image_path or not os.path.exists(image_path):
                QMessageBox.warning(self, "警告", "请先选择已生成的模特图，才能生成视频")
                return
                
            # 更新按钮状态
            button.setText("正在生成")
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            
            # 显示进度提示
            self.status_message_signal.emit("正在生成视频...")
            
            # 在线程中执行视频生成
            def _generate_video_task():
                try:
                    # 获取可用的视频账号
                    account_info = get_video_account()
                    if not account_info:
                        return {"success": False, "error": "没有可用的视频账号"}

                    # 获取视频时长配置
                    duration_cfg = get_config('video_duration', '5')
                    try:
                        seconds = int(duration_cfg)
                    except (ValueError, TypeError):
                        seconds = 5

                    # 使用选中的模特图作为输入
                    image_path = file.get('selected_model_image')
                    if not image_path or not os.path.exists(image_path):
                        return {"success": False, "error": "模特图未生成或未选择，无法生成视频"}

                    # 调用实际的视频生成函数（异步）
                    result = asyncio.run(generate_video_async(
                        cookies=account_info['cookies'],
                        username=account_info['username'],
                        password=account_info['password'],
                        prompt=prompt,
                        seconds=seconds,
                        image_path=image_path,
                        headless=True,
                        account_id=account_info['id']
                    ))

                    # 如果生成成功，添加记录到数据库
                    if result.get('success'):
                        add_record(account_info['id'], 2)  # 2代表视频类型

                    return result
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            # 使用线程池执行任务
            global thread_pool
            if thread_pool:
                future = thread_pool.submit(_generate_video_task)
                # 添加回调处理结果（带行号）
                future.add_done_callback(lambda f, btn=button, r=row: self._on_video_generate_finished(f, btn, r))
            else:
                QMessageBox.critical(self, "错误", "线程池不可用")
                # 恢复按钮状态
                self._reset_generate_button(button, "生成视频", "#28a745")

    def _on_video_generate_finished(self, future, button, row):
        """视频生成完成回调（支持失败自动重试，最多三次）"""
        try:
            result = future.result()
            if result.get('success'):
                # 通过信号更新状态栏，确保在主线程执行
                self.status_message_signal.emit("视频生成完成")
                # 使用信号在主线程中显示消息框
                self._show_message_in_main_thread("成功", "视频生成完成")

                # 如有视频URL，下载并保存到项目根目录 generated_videos
                video_url = result.get('video_url')
                if video_url:
                    try:
                        response = requests.get(video_url, stream=True)
                        if response.status_code == 200:
                            # 推断扩展名，默认.mp4
                            base = os.path.basename(video_url)
                            ext = os.path.splitext(base)[1] or '.mp4'
                            # 使用主图的文件夹名作为视频文件名
                            folder_name = None
                            try:
                                if 0 <= row < len(self.current_files):
                                    folder_path = self.current_files[row].get('folder_path')
                                    if folder_path:
                                        folder_name = os.path.basename(folder_path)
                                # 兜底：从主图路径推断父文件夹名
                                if not folder_name:
                                    main_image_path = self.current_files[row].get('main_image') if 0 <= row < len(self.current_files) else None
                                    if main_image_path:
                                        folder_name = os.path.basename(os.path.dirname(main_image_path))
                            except Exception:
                                folder_name = None

                            base_name = folder_name or f"generated_{int(time.time())}"
                            new_video_name = f"{base_name}{ext}"
                            new_video_path = os.path.join(str(self.generated_videos_dir), new_video_name)
                            # 如果文件已存在，追加序号避免覆盖
                            if os.path.exists(new_video_path):
                                idx = 1
                                while True:
                                    alt_name = f"{base_name}_{idx}{ext}"
                                    alt_path = os.path.join(str(self.generated_videos_dir), alt_name)
                                    if not os.path.exists(alt_path):
                                        new_video_name = alt_name
                                        new_video_path = alt_path
                                        break
                                    idx += 1
                            with open(new_video_path, 'wb') as f:
                                for chunk in response.iter_content(1024 * 64):
                                    f.write(chunk)
                            # 通过信号在主线程更新UI
                            self.video_generated_signal.emit(row, new_video_path)
                    except Exception as e:
                        logger.error(f"下载或保存视频失败: {e}")
                else:
                    # 即使未能获取到URL，也更新前端状态为已完成
                    self.video_generated_signal.emit(row, "")
            else:
                # 失败：尝试重试（最多三次）
                attempts = self._video_retry_counts.get(row, 0)
                if attempts < 3:
                    self._video_retry_counts[row] = attempts + 1
                    try:
                        # 准备重试所需参数
                        account_info = get_video_account()
                        if not account_info:
                            raise RuntimeError('没有可用的视频账号')
                        duration_cfg = get_config('video_duration', '5')
                        try:
                            seconds = int(duration_cfg)
                        except (ValueError, TypeError):
                            seconds = 5
                        prompt = get_config('video_prompt', '')
                        if not prompt:
                            raise RuntimeError('请输入视频提示词')
                        if row >= len(self.current_files):
                            raise RuntimeError('行越界')
                        file = self.current_files[row]
                        image_path = file.get('selected_model_image')
                        if not image_path or not os.path.exists(image_path):
                            raise RuntimeError('模特图未生成或未选择，无法生成视频')

                        global thread_pool
                        if not thread_pool:
                            raise RuntimeError('线程池不可用')

                        # 保持按钮禁用与“正在生成”状态，不进行重置
                        self.status_message_signal.emit(f"视频生成失败，重试第{attempts + 1}次")

                        def _retry_video_task():
                            try:
                                result_local = asyncio.run(generate_video_async(
                                    cookies=account_info['cookies'],
                                    username=account_info['username'],
                                    password=account_info['password'],
                                    prompt=prompt,
                                    seconds=seconds,
                                    image_path=image_path,
                                    headless=True,
                                    account_id=account_info['id']
                                ))
                                if result_local.get('success'):
                                    add_record(account_info['id'], 2)
                                return result_local
                            except Exception as e:
                                return {"success": False, "error": str(e)}

                        future2 = thread_pool.submit(_retry_video_task)
                        future2.add_done_callback(lambda f, btn=button, r=row: self._on_video_generate_finished(f, btn, r))
                        return
                    except Exception as e:
                        err = result.get('error', '未知错误')
                        status_bar = self.statusBar()
                        if status_bar is not None:
                            status_bar.showMessage(f"视频生成失败，无法重试: {err}")
                        self._show_message_in_main_thread("错误", f"视频生成失败: {err}")
                else:
                    err = result.get('error', '未知错误')
                    status_bar = self.statusBar()
                    if status_bar is not None:
                        status_bar.showMessage("视频生成失败，已达最大重试次数")
                    self._show_message_in_main_thread("错误", f"视频生成失败(已重试3次): {err}")
        except Exception as e:
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage(f"视频生成异常: {str(e)}")
            self._show_message_in_main_thread("错误", f"视频生成异常: {str(e)}")
        # 在成功或最终失败后，才重置按钮与刷新账号列表
        try:
            is_success = False
            try:
                is_success = bool(future.result().get('success'))
            except Exception:
                is_success = False
            attempts = self._video_retry_counts.get(row, 0)
            if is_success or attempts >= 3:
                if row in self._video_retry_counts:
                    del self._video_retry_counts[row]
                self.reset_button_signal.emit(button, "生成视频", "#28a745")
                self.refresh_accounts_signal.emit()
        except Exception:
            pass

    def delete_item(self, row):
        """删除项目"""
        if row < len(self.current_files):
            reply = QMessageBox.question(self, "确认", "确定要删除这个项目吗？", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    # 删除文件系统中的文件
                    file = self.current_files[row]
                    if os.path.exists(file['main_image']):
                        # 删除主图文件
                        os.remove(file['main_image'])
                        # 同时删除对应的文件夹
                        folder_path = os.path.dirname(file['main_image'])
                        if os.path.exists(folder_path) and os.path.isdir(folder_path):
                            import shutil
                            shutil.rmtree(folder_path)
                    
                    # 从列表中移除
                    del self.current_files[row]
                    
                    # 重新显示
                    self.display_folder_content(self.current_files)
                    status_bar = self.statusBar()
                    if status_bar is not None:
                        status_bar.showMessage("项目已删除")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"删除项目失败: {str(e)}")
                    
    def batch_generate_images(self):
        """批量生成图片"""
        if not self.current_files:
            QMessageBox.warning(self, "警告", "请先导入文件夹")
            return
            
        # 从数据库获取提示词
        prompt = get_config('image_prompt', '')
        if not prompt:
            QMessageBox.warning(self, "警告", "请输入图片提示词")
            return
            
        # 直接在主线程触发每一行的图片生成（生成过程仍在线程池中执行）
        triggered = 0
        for row in range(len(self.current_files)):
            try:
                action_widget = self.files_table.cellWidget(row, 3)
                if not action_widget:
                    continue
                layout = action_widget.layout()
                if not layout:
                    continue
                image_btn = None
                for i in range(layout.count()):
                    itm = layout.itemAt(i)
                    if itm and itm.widget() and isinstance(itm.widget(), QPushButton):
                        w = itm.widget()
                        if w.objectName() == "generate_image_btn":
                            image_btn = w
                            break
                if image_btn is not None and image_btn.isEnabled():
                    self.generate_image(row, image_btn)
                    triggered += 1
            except Exception as e:
                logger.error(f"触发第{row}行图片生成失败: {e}")

        # 通过状态栏/信号提示批量触发完成
        self.status_message_signal.emit(f"图片批量生成已触发: {triggered} 行")
            
    def _on_batch_images_finished(self, future):
        """批量图片生成完成回调"""
        try:
            result = future.result()
            if result.get('success'):
                success_count = result.get('success_count', 0)
                failed_count = result.get('failed_count', 0)
                # 使用主线程信号更新状态栏，避免跨线程UI操作
                self.status_message_signal.emit(f"批量图片生成完成: 成功{success_count}个，失败{failed_count}个")
            else:
                self.status_message_signal.emit(f"批量图片生成失败: {result.get('message', '未知错误')}")
        except Exception as e:
            self.status_message_signal.emit(f"批量图片生成异常: {str(e)}")
            
    def batch_generate_videos(self):
        """批量生成视频"""
        if not self.current_files:
            QMessageBox.warning(self, "警告", "请先导入文件夹")
            return
            
        # 从数据库获取提示词
        prompt = get_config('video_prompt', '')
        if not prompt:
            QMessageBox.warning(self, "警告", "请输入视频提示词")
            return
        
        # 仅触发可生成的行（存在有效的selected_model_image）
        triggered = 0
        skipped = 0
        for row in range(len(self.current_files)):
            try:
                selected_path = self.current_files[row].get('selected_model_image')
                if not selected_path or not os.path.exists(selected_path):
                    skipped += 1
                    continue
                action_widget = self.files_table.cellWidget(row, 3)
                if not action_widget:
                    skipped += 1
                    continue
                layout = action_widget.layout()
                if not layout:
                    skipped += 1
                    continue
                video_btn = None
                for i in range(layout.count()):
                    itm = layout.itemAt(i)
                    if itm and itm.widget() and isinstance(itm.widget(), QPushButton):
                        w = itm.widget()
                        if w.objectName() == "generate_video_btn":
                            video_btn = w
                            break
                if video_btn is not None and video_btn.isEnabled():
                    self.generate_video(row, video_btn)
                    triggered += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"触发第{row}行视频生成失败: {e}")
                skipped += 1

        self.status_message_signal.emit(f"视频批量生成已触发: 成功{triggered}个，跳过{skipped}个")
            
    def _on_batch_videos_finished(self, future):
        """批量视频生成完成回调"""
        try:
            result = future.result()
            if result.get('success'):
                success_count = result.get('success_count', 0)
                failed_count = result.get('failed_count', 0)
                # 使用主线程信号更新状态栏，避免跨线程UI操作
                self.status_message_signal.emit(f"批量视频生成完成: 成功{success_count}个，失败{failed_count}个")
            else:
                self.status_message_signal.emit(f"批量视频生成失败: {result.get('message', '未知错误')}")
        except Exception as e:
            self.status_message_signal.emit(f"批量视频生成异常: {str(e)}")

    def save_image_prompt(self):
        """保存图片提示词"""
        # 从设置界面获取提示词
        prompt = self.settings_image_prompt_edit.toPlainText()
        result = set_config('image_prompt', prompt)
        if result.get('success'):
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage("图片提示词已保存")
        else:
            QMessageBox.critical(self, "错误", f"保存图片提示词失败: {result.get('error')}")
            
    def save_video_prompt(self):
        """保存视频提示词"""
        # 从设置界面获取提示词
        prompt = self.settings_video_prompt_edit.toPlainText()
        result = set_config('video_prompt', prompt)
        if result.get('success'):
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage("视频提示词已保存")
        else:
            QMessageBox.critical(self, "错误", f"保存视频提示词失败: {result.get('error')}")

    def load_configs(self):
        """加载配置"""
        configs = get_all_configs()
        if configs:
            self.api_key_edit.setText(configs.get('api_key', ''))
            self.api_proxy_edit.setText(configs.get('api_proxy', ''))
            self.model_edit.setText(configs.get('model', ''))
            self.settings_image_prompt_edit.setPlainText(configs.get('image_prompt', ''))
            self.settings_video_prompt_edit.setPlainText(configs.get('video_prompt', ''))
            
            # 视频时长设置
            video_duration = configs.get('video_duration', '5')
            if video_duration == '10':
                self.video_duration_10.setChecked(True)
            else:
                self.video_duration_5.setChecked(True)
                
            # 限制设置
            self.max_threads_spin.setValue(int(configs.get('max_threads', '5')))
            self.daily_video_limit_spin.setValue(int(configs.get('daily_video_limit', '2')))
            self.daily_image_limit_spin.setValue(int(configs.get('daily_image_limit', '10')))

    def save_settings(self):
        """保存设置"""
        try:
            # 保存基本配置
            set_config('api_key', self.api_key_edit.text())
            set_config('api_proxy', self.api_proxy_edit.text())
            set_config('model', self.model_edit.text())
            set_config('image_prompt', self.settings_image_prompt_edit.toPlainText())
            set_config('video_prompt', self.settings_video_prompt_edit.toPlainText())
            
            # 保存视频时长
            video_duration = '10' if self.video_duration_10.isChecked() else '5'
            set_config('video_duration', video_duration)
            
            # 保存限制设置
            set_config('max_threads', str(self.max_threads_spin.value()))
            set_config('daily_video_limit', str(self.daily_video_limit_spin.value()))
            set_config('daily_image_limit', str(self.daily_image_limit_spin.value()))
            
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage("设置已保存")
            QMessageBox.information(self, "成功", "设置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
            
    def add_account(self):
        """添加账号"""
        # 创建一个简单的对话框来添加账号
        dialog = QDialog(self)
        dialog.setWindowTitle("添加账号")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 用户名输入
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("用户名:"))
        self.username_edit = QLineEdit()
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)
        
        # 密码输入
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("密码:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_edit)
        layout.addLayout(password_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # 连接信号
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = self.username_edit.text()
            password = self.password_edit.text()
            
            if username:
                result = add_account(username, password)
                if result.get('success'):
                    status_bar = self.statusBar()
                    if status_bar is not None:
                        status_bar.showMessage("账号添加成功")
                    self.refresh_accounts()
                else:
                    QMessageBox.critical(self, "错误", f"账号添加失败: {result.get('error')}")
            else:
                QMessageBox.warning(self, "警告", "请输入用户名")
        
    def batch_add_accounts(self):
        """批量添加账号"""
        dialog = BatchAddDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            accounts_data = dialog.get_accounts_data()
            if accounts_data and any(accounts_data):
                result = batch_add_accounts(accounts_data)
                if result.get('success'):
                    status_bar = self.statusBar()
                    if status_bar is not None:
                        status_bar.showMessage(f"批量添加账号完成: 成功{result['added_count']}个，失败{result['failed_count']}个")
                    self.refresh_accounts()
                    QMessageBox.information(self, "成功", f"批量添加账号完成: 成功{result['added_count']}个，失败{result['failed_count']}个")
                else:
                    QMessageBox.critical(self, "错误", f"批量添加账号失败: {result.get('error')}")
            else:
                QMessageBox.warning(self, "警告", "请输入账号信息")
        
    def delete_selected_accounts(self):
        """删除选中账号"""
        selected_ids = []
        for row in range(self.accounts_table.rowCount()):
            checkbox = self.accounts_table.cellWidget(row, 0)
            if checkbox and isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                item = self.accounts_table.item(row, 1)
                if item:
                    selected_ids.append(int(item.text()))
        
        if selected_ids:
            reply = QMessageBox.question(self, "确认", f"确定要删除选中的 {len(selected_ids)} 个账号吗？", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                result = delete_accounts(selected_ids)
                if result.get('success'):
                    status_bar = self.statusBar()
                    if status_bar is not None:
                        status_bar.showMessage(f"成功删除 {result['deleted_count']} 个账号")
                    self.refresh_accounts()
                else:
                    QMessageBox.critical(self, "错误", f"删除账号失败: {result.get('error')}")
        else:
            QMessageBox.warning(self, "警告", "请选择要删除的账号")
    
    def on_accounts_select_all_toggled(self, _state):
        """全选/取消全选账号列表中的复选框"""
        try:
            check = bool(self.select_all_checkbox.isChecked())
        except Exception:
            check = False
        try:
            for row in range(self.accounts_table.rowCount()):
                widget = self.accounts_table.cellWidget(row, 0)
                if widget and isinstance(widget, QCheckBox):
                    widget.setChecked(check)
        except Exception:
            pass
        
    def refresh_accounts(self):
        """刷新账号列表"""
        try:
            accounts = get_accounts_with_usage()
            self.accounts_table.setRowCount(len(accounts))
            
            for row, account in enumerate(accounts):
                # 选择列
                checkbox = QCheckBox()
                self.accounts_table.setCellWidget(row, 0, checkbox)
                
                # ID列
                id_item = QTableWidgetItem(str(account['id']))
                self.accounts_table.setItem(row, 1, id_item)
                
                # 用户名列
                username_item = QTableWidgetItem(account['username'])
                self.accounts_table.setItem(row, 2, username_item)
                
                # 当日图片数列
                image_count_item = QTableWidgetItem(str(account['image_count']))
                self.accounts_table.setItem(row, 3, image_count_item)
                
                # 当日视频数列
                video_count_item = QTableWidgetItem(str(account['video_count']))
                self.accounts_table.setItem(row, 4, video_count_item)
                
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.showMessage(f"账号列表已刷新，共 {len(accounts)} 个账号")
            # 刷新后重置“全选”复选框为未选中
            try:
                if hasattr(self, 'select_all_checkbox') and self.select_all_checkbox:
                    self.select_all_checkbox.blockSignals(True)
                    self.select_all_checkbox.setChecked(False)
                    self.select_all_checkbox.blockSignals(False)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新账号列表失败: {str(e)}")
        
    def closeEvent(self, a0):
        """关闭事件"""
        # 关闭数据库连接
        close_database()
        # 关闭线程池
        global thread_pool
        if thread_pool:
            thread_pool.shutdown(wait=True)
            logger.info("线程池已关闭")
        logger.info("应用关闭")
        super().closeEvent(a0)

    def _show_message_in_main_thread(self, title, message):
        """在主线程中显示消息框"""
        # 使用QTimer在主线程中执行UI操作
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: QMessageBox.information(self, title, message))

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Jimeng Scripts")
    app.setApplicationVersion("1.0.0")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
