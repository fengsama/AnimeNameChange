import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QPushButton, QLabel, QLineEdit, QComboBox, QFileDialog, 
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFormLayout, QCheckBox
)
from PyQt5.QtCore import Qt, QDropEvent, QMimeData
from PyQt5.QtGui import QFont

class MovieRenamerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('影视文件批量重命名工具')
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        self.files = []
        self.config_file = 'config.json'
        self.log_file = 'rename_log.txt'
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 文件/文件夹选择区域
        select_group = QGroupBox('文件/文件夹选择')
        select_layout = QHBoxLayout()
        
        self.btn_add_files = QPushButton('添加文件')
        self.btn_add_files.clicked.connect(self.add_files)
        
        self.btn_add_folder = QPushButton('添加文件夹')
        self.btn_add_folder.clicked.connect(self.add_folder)
        
        self.btn_clear = QPushButton('清空列表')
        self.btn_clear.clicked.connect(self.clear_list)
        
        select_layout.addWidget(self.btn_add_files)
        select_layout.addWidget(self.btn_add_folder)
        select_layout.addWidget(self.btn_clear)
        select_group.setLayout(select_layout)
        
        # 文件列表显示区域
        list_group = QGroupBox('文件列表')
        list_layout = QVBoxLayout()
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(['原始文件名', '文件类型', '大小', '路径'])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 启用拖拽功能
        self.file_table.setAcceptDrops(True)
        self.file_table.dragEnterEvent = self.drag_enter_event
        self.file_table.dropEvent = self.drop_event
        
        list_layout.addWidget(self.file_table)
        list_group.setLayout(list_layout)
        
        # 命名规则配置区域
        config_group = QGroupBox('命名规则配置')
        config_layout = QFormLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            '[影视类型] - [标题] - [季数]x[集数]',
            '[标题] - [季数]x[集数]',
            '[影视类型] - [标题]',
            '[标题]'
        ])
        self.template_combo.currentTextChanged.connect(self.update_preview)
        
        self.custom_rule = QLineEdit()
        self.custom_rule.setPlaceholderText('自定义命名规则，例如：[标题] - [年份]')
        self.custom_rule.textChanged.connect(self.update_preview)
        
        self.media_type_combo = QComboBox()
        self.media_type_combo.addItems(['番剧', '电视剧', '电影', '其他'])
        self.media_type_combo.currentTextChanged.connect(self.update_preview)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText('输入标题')
        self.title_input.textChanged.connect(self.update_preview)
        
        self.season_input = QLineEdit()
        self.season_input.setPlaceholderText('输入季数')
        self.season_input.textChanged.connect(self.update_preview)
        
        self.episode_input = QLineEdit()
        self.episode_input.setPlaceholderText('输入集数')
        self.episode_input.textChanged.connect(self.update_preview)
        
        config_layout.addRow('命名模板:', self.template_combo)
        config_layout.addRow('自定义规则:', self.custom_rule)
        config_layout.addRow('影视类型:', self.media_type_combo)
        config_layout.addRow('标题:', self.title_input)
        config_layout.addRow('季数:', self.season_input)
        config_layout.addRow('集数:', self.episode_input)
        config_group.setLayout(config_layout)
        
        # 预览区域
        preview_group = QGroupBox('预览')
        preview_layout = QVBoxLayout()
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(['原始文件名', '重命名后'])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        
        # 操作控制区域
        control_group = QGroupBox('操作控制')
        control_layout = QHBoxLayout()
        
        self.btn_rename = QPushButton('开始重命名')
        self.btn_rename.clicked.connect(self.start_rename)
        
        self.btn_cancel = QPushButton('取消操作')
        self.btn_cancel.clicked.connect(self.cancel_operation)
        
        self.btn_save_config = QPushButton('保存配置')
        self.btn_save_config.clicked.connect(self.save_config)
        
        self.btn_view_log = QPushButton('查看日志')
        self.btn_view_log.clicked.connect(self.view_log)
        
        control_layout.addWidget(self.btn_rename)
        control_layout.addWidget(self.btn_cancel)
        control_layout.addWidget(self.btn_save_config)
        control_layout.addWidget(self.btn_view_log)
        control_group.setLayout(control_layout)
        
        # 日志显示区域
        log_group = QGroupBox('操作日志')
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # 布局组装
        top_layout = QHBoxLayout()
        top_layout.addWidget(select_group, 1)
        
        middle_layout = QHBoxLayout()
        middle_layout.addWidget(list_group, 1)
        middle_layout.addWidget(config_group, 1)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(preview_group, 1)
        bottom_layout.addWidget(log_group, 1)
        
        main_layout.addLayout(top_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(bottom_layout)
        main_layout.addWidget(control_group)
    
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, '选择文件', '', '视频文件 (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.ts)'
        )
        if files:
            self.add_files_to_list(files)
    
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            files = []
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.ts']):
                        files.append(os.path.join(root, filename))
            if files:
                self.add_files_to_list(files)
    
    def add_files_to_list(self, files):
        for file_path in files:
            if file_path not in [f['path'] for f in self.files]:
                filename = os.path.basename(file_path)
                file_ext = os.path.splitext(filename)[1]
                file_size = os.path.getsize(file_path)
                size_str = self.format_file_size(file_size)
                
                self.files.append({
                    'path': file_path,
                    'filename': filename,
                    'ext': file_ext,
                    'size': file_size,
                    'size_str': size_str
                })
        
        self.update_file_table()
        self.update_preview()
        self.log(f'添加了 {len(files)} 个文件')
    
    def clear_list(self):
        self.files = []
        self.update_file_table()
        self.update_preview()
        self.log('清空了文件列表')
    
    def update_file_table(self):
        self.file_table.setRowCount(len(self.files))
        for i, file_info in enumerate(self.files):
            self.file_table.setItem(i, 0, QTableWidgetItem(file_info['filename']))
            self.file_table.setItem(i, 1, QTableWidgetItem(file_info['ext']))
            self.file_table.setItem(i, 2, QTableWidgetItem(file_info['size_str']))
            self.file_table.setItem(i, 3, QTableWidgetItem(file_info['path']))
    
    def update_preview(self):
        self.preview_table.setRowCount(len(self.files))
        for i, file_info in enumerate(self.files):
            self.preview_table.setItem(i, 0, QTableWidgetItem(file_info['filename']))
            
            new_name = self.generate_new_name(file_info)
            self.preview_table.setItem(i, 1, QTableWidgetItem(new_name))
    
    def generate_new_name(self, file_info):
        rule = self.custom_rule.text() if self.custom_rule.text() else self.template_combo.currentText()
        
        new_name = rule
        new_name = new_name.replace('[影视类型]', self.media_type_combo.currentText())
        new_name = new_name.replace('[标题]', self.title_input.text() if self.title_input.text() else os.path.splitext(file_info['filename'])[0])
        new_name = new_name.replace('[季数]', self.season_input.text() if self.season_input.text() else '1')
        new_name = new_name.replace('[集数]', self.episode_input.text() if self.episode_input.text() else '1')
        
        return new_name + file_info['ext']
    
    def start_rename(self):
        if not self.files:
            QMessageBox.warning(self, '警告', '请先添加文件')
            return
        
        if not self.title_input.text():
            QMessageBox.warning(self, '警告', '请输入标题')
            return
        
        success_count = 0
        error_count = 0
        
        for file_info in self.files:
            try:
                old_path = file_info['path']
                directory = os.path.dirname(old_path)
                new_name = self.generate_new_name(file_info)
                new_path = os.path.join(directory, new_name)
                
                # 检查重名
                if os.path.exists(new_path) and new_path != old_path:
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    base_name, ext = os.path.splitext(new_name)
                    new_name = f"{base_name}_{timestamp}{ext}"
                    new_path = os.path.join(directory, new_name)
                
                os.rename(old_path, new_path)
                success_count += 1
                self.log(f'成功重命名: {file_info["filename"]} -> {new_name}')
                
            except Exception as e:
                error_count += 1
                self.log(f'重命名失败: {file_info["filename"]} - {str(e)}')
        
        self.log(f'操作完成: 成功 {success_count} 个, 失败 {error_count} 个')
        QMessageBox.information(self, '完成', f'重命名操作完成\n成功: {success_count} 个\n失败: {error_count} 个')
        
        # 清空列表并更新
        self.clear_list()
    
    def cancel_operation(self):
        self.clear_list()
        self.title_input.clear()
        self.season_input.clear()
        self.episode_input.clear()
        self.custom_rule.clear()
        self.log('取消了操作')
    
    def save_config(self):
        config = {
            'template': self.template_combo.currentText(),
            'custom_rule': self.custom_rule.text(),
            'media_type': self.media_type_combo.currentText(),
            'title': self.title_input.text(),
            'season': self.season_input.text(),
            'episode': self.episode_input.text()
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        self.log('配置已保存')
        QMessageBox.information(self, '成功', '配置已保存')
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'template' in config:
                    index = self.template_combo.findText(config['template'])
                    if index != -1:
                        self.template_combo.setCurrentIndex(index)
                
                if 'custom_rule' in config:
                    self.custom_rule.setText(config['custom_rule'])
                
                if 'media_type' in config:
                    index = self.media_type_combo.findText(config['media_type'])
                    if index != -1:
                        self.media_type_combo.setCurrentIndex(index)
                
                if 'title' in config:
                    self.title_input.setText(config['title'])
                
                if 'season' in config:
                    self.season_input.setText(config['season'])
                
                if 'episode' in config:
                    self.episode_input.setText(config['episode'])
                
                self.log('配置已加载')
            except Exception as e:
                self.log(f'加载配置失败: {str(e)}')
    
    def view_log(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                log_window = QWidget()
                log_window.setWindowTitle('操作日志')
                log_window.setGeometry(200, 200, 800, 600)
                
                layout = QVBoxLayout()
                log_text = QTextEdit()
                log_text.setReadOnly(True)
                log_text.setText(log_content)
                
                layout.addWidget(log_text)
                log_window.setLayout(layout)
                log_window.show()
            except Exception as e:
                QMessageBox.warning(self, '错误', f'查看日志失败: {str(e)}')
        else:
            QMessageBox.information(self, '提示', '暂无日志记录')
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f'[{timestamp}] {message}\n'
        
        self.log_text.append(log_entry)
        
        # 保存到日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def format_file_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def drop_event(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path) and any(path.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.ts']):
                files.append(path)
            elif os.path.isdir(path):
                for root, _, filenames in os.walk(path):
                    for filename in filenames:
                        if any(filename.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.ts']):
                            files.append(os.path.join(root, filename))
        
        if files:
            self.add_files_to_list(files)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MovieRenamerApp()
    window.show()
    sys.exit(app.exec_())
