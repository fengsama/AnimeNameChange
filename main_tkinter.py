import sys
import os
import json
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

class MovieRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title('影视文件批量重命名工具')
        # 调整窗口默认尺寸，确保在1366×768及以上分辨率下完整显示
        self.root.geometry('900x650')
        self.root.minsize(800, 600)
        
        self.files = []
        self.config_file = 'config.json'
        self.log_file = 'rename_log.txt'
        self.episode_index = -1  # 存储用户选择的数字索引，-1表示未选择
        
        self.create_widgets()
        self.load_config()
    
    def create_widgets(self):
        # 创建主框架，添加滚动功能
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建滚动区域
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮事件
        def on_mousewheel(event):
            # 计算滚动距离
            delta = -1 * (event.delta // 120) * 3
            canvas.yview_scroll(delta, "units")
        
        # 为Canvas绑定鼠标滚轮事件
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文件/文件夹选择区域
        select_frame = ttk.LabelFrame(scrollable_frame, text='文件/文件夹选择', padding='10')
        select_frame.pack(fill=tk.X, pady=5)
        
        select_buttons = ttk.Frame(select_frame)
        select_buttons.pack(fill=tk.X)
        
        ttk.Button(select_buttons, text='添加文件', command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_buttons, text='添加文件夹', command=self.add_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_buttons, text='清空列表', command=self.clear_list).pack(side=tk.LEFT, padx=5)
        
        # 文件列表显示区域
        list_frame = ttk.LabelFrame(scrollable_frame, text='文件列表', padding='10')
        list_frame.pack(fill=tk.X, pady=5)
        
        # 创建树状视图，设置高度
        self.file_tree = ttk.Treeview(list_frame, columns=('filename', 'ext', 'size', 'path'), show='headings', height=15)
        self.file_tree.heading('filename', text='原始文件名')
        self.file_tree.heading('ext', text='文件类型')
        self.file_tree.heading('size', text='大小')
        self.file_tree.heading('path', text='路径')
        
        # 设置列宽
        self.file_tree.column('filename', width=200)
        self.file_tree.column('ext', width=80)
        self.file_tree.column('size', width=100)
        self.file_tree.column('path', width=400)
        
        # 添加滚动条
        file_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscroll=file_scrollbar.set)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_tree.pack(fill=tk.X, expand=False)
        
        # 启用拖拽功能
        # tkinter的拖拽功能需要不同的实现方式
        # 这里暂时注释掉，避免错误
        
        # 添加右键菜单
        self.file_tree.bind('<Button-3>', self.show_context_menu)
        self.context_menu = tk.Menu(self.file_tree, tearoff=0)
        self.context_menu.add_command(label='从列表中删除', command=self.delete_selected_file)
        
        # 命名规则配置区域
        config_frame = ttk.LabelFrame(scrollable_frame, text='命名规则配置', padding='10')
        config_frame.pack(fill=tk.X, pady=5)
        
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill=tk.X)
        
        # 命名模板
        ttk.Label(config_grid, text='命名模板:').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(config_grid, textvariable=self.template_var, width=40)
        self.template_combo['values'] = [
            '[影视类型] - [标题] - [季数] - [集数]',
            '[标题] - [季数] - [集数]',
            '[影视类型] - [标题]',
            '[标题]'
        ]
        self.template_combo.current(0)
        self.template_combo.bind('<<ComboboxSelected>>', self.update_preview)
        self.template_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 自定义规则
        ttk.Label(config_grid, text='自定义规则:').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.custom_rule_var = tk.StringVar()
        self.custom_rule = ttk.Entry(config_grid, textvariable=self.custom_rule_var, width=40)
        self.custom_rule.insert(0, '')
        self.custom_rule.bind('<KeyRelease>', self.update_preview)
        self.custom_rule.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 影视类型
        ttk.Label(config_grid, text='影视类型:').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.media_type_var = tk.StringVar()
        self.media_type_combo = ttk.Combobox(config_grid, textvariable=self.media_type_var, width=20)
        self.media_type_combo['values'] = ['番剧', '电视剧', '电影', '其他']
        self.media_type_combo.current(0)
        self.media_type_combo.bind('<<ComboboxSelected>>', self.update_preview)
        self.media_type_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 标题
        ttk.Label(config_grid, text='标题:').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        self.title_input = ttk.Entry(config_grid, textvariable=self.title_var, width=40)
        self.title_input.insert(0, '')
        self.title_input.bind('<KeyRelease>', self.update_preview)
        self.title_input.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 季数
        ttk.Label(config_grid, text='季数:').grid(row=4, column=0, sticky=tk.W, pady=5)
        self.season_var = tk.StringVar()
        self.season_input = ttk.Entry(config_grid, textvariable=self.season_var, width=10)
        self.season_input.insert(0, '')
        self.season_input.bind('<KeyRelease>', self.update_preview)
        self.season_input.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # 集数前缀
        ttk.Label(config_grid, text='集数前缀:').grid(row=5, column=0, sticky=tk.W, pady=5)
        
        # 创建集数前缀框架
        self.episode_frame = ttk.Frame(config_grid)
        self.episode_frame.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # 集数前缀变量
        self.episode_prefix_var = tk.StringVar()
        self.episode_input = ttk.Entry(self.episode_frame, textvariable=self.episode_prefix_var, width=10)
        self.episode_input.insert(0, '')
        self.episode_input.bind('<KeyRelease>', self.update_preview)
        
        # 数字匹配显示标签
        self.episode_match_label = ttk.Label(self.episode_frame, text='', font=('Arial', 10))
        self.episode_match_label.bind('<Button-1>', self.on_episode_label_click)
        
        # 布局
        self.episode_input.pack(side=tk.LEFT, padx=5)
        self.episode_match_label.pack(side=tk.LEFT, padx=5)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(scrollable_frame, text='预览', padding='10')
        preview_frame.pack(fill=tk.X, pady=5)
        
        # 创建预览树，设置高度
        self.preview_tree = ttk.Treeview(preview_frame, columns=('original', 'new'), show='headings', height=10)
        self.preview_tree.heading('original', text='原始文件名')
        self.preview_tree.heading('new', text='重命名后')
        
        self.preview_tree.column('original', width=300)
        self.preview_tree.column('new', width=300)
        
        # 添加滚动条
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscroll=preview_scrollbar.set)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preview_tree.pack(fill=tk.X, expand=False)
        
        # 操作控制区域
        control_frame = ttk.LabelFrame(scrollable_frame, text='操作控制', padding='10')
        control_frame.pack(fill=tk.X, pady=5)
        
        control_buttons = ttk.Frame(control_frame)
        control_buttons.pack(fill=tk.X)
        
        ttk.Button(control_buttons, text='开始重命名', command=self.start_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons, text='取消操作', command=self.cancel_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons, text='保存配置', command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons, text='查看日志', command=self.view_log).pack(side=tk.LEFT, padx=5)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(scrollable_frame, text='操作日志', padding='10')
        log_frame.pack(fill=tk.X, pady=5, padx=0, ipady=0)
        
        self.log_text = tk.Text(log_frame, height=8, state=tk.DISABLED)
        
        # 添加滚动条
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscroll=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.pack(fill=tk.X, expand=False)
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            title='选择文件',
            filetypes=[('视频文件', '*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.ts'), ('所有文件', '*.*')]
        )
        if files:
            self.add_files_to_list(files)
    
    def add_folder(self):
        folder = filedialog.askdirectory(title='选择文件夹')
        if folder:
            files = []
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.ts']):
                        files.append(os.path.join(root, filename))
            if files:
                self.add_files_to_list(files)
    
    def extract_numbers(self, filename):
        # 提取文件名中的所有数字序列
        numbers = re.findall(r'\d+', filename)
        return numbers
    
    def natural_sort_key(self, s):
        # 自然排序键函数，将字符串分割成文本和数字部分
        import re
        # 使用正则表达式分割字符串，保留数字和非数字部分
        parts = re.split(r'(\d+)', s)
        # 对数字部分转换为整数，文本部分保持原样
        return [int(part) if part.isdigit() else part for part in parts]
    
    def add_files_to_list(self, files):
        for file_path in files:
            if file_path not in [f['path'] for f in self.files]:
                filename = os.path.basename(file_path)
                file_ext = os.path.splitext(filename)[1]
                file_size = os.path.getsize(file_path)
                size_str = self.format_file_size(file_size)
                
                # 提取文件名中的数字序列
                numbers = self.extract_numbers(filename)
                
                self.files.append({
                    'path': file_path,
                    'filename': filename,
                    'ext': file_ext,
                    'size': file_size,
                    'size_str': size_str,
                    'numbers': numbers
                })
        
        # 使用自然排序
        self.files.sort(key=lambda x: self.natural_sort_key(x['filename']))
        
        self.update_file_tree()
        self.update_preview()
        
        # 更新集数匹配显示
        self.update_episode_match_display()
        
        self.log(f'添加了 {len(files)} 个文件，并按自然数字顺序排序')
    
    def clear_list(self):
        self.files = []
        # 重置episode_pattern属性
        if hasattr(self, 'episode_pattern'):
            delattr(self, 'episode_pattern')
        self.episode_index = -1
        self.update_file_tree()
        self.update_preview()
        self.update_episode_match_display()
        self.log('清空了文件列表')
    
    def update_file_tree(self):
        # 清空树状视图
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # 添加文件信息
        for file_info in self.files:
            self.file_tree.insert('', tk.END, values=(
                file_info['filename'],
                file_info['ext'],
                file_info['size_str'],
                file_info['path']
            ))
    
    def update_preview(self, event=None):
        # 清空预览树
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # 添加预览信息
        for index, file_info in enumerate(self.files):
            new_name = self.generate_new_name(file_info, index)
            self.preview_tree.insert('', tk.END, values=(
                file_info['filename'],
                new_name
            ))
    
    def generate_new_name(self, file_info, index=0):
        # 获取命名规则
        custom_rule = self.custom_rule_var.get()
        rule = custom_rule if custom_rule else self.template_var.get()
        
        # 计算集数
        episode_str = ''
        if hasattr(self, 'episode_pattern'):
            # 根据用户选择的数字序列确定集数
            numbers = file_info.get('numbers', [])
            for num in numbers:
                if num == self.episode_pattern:
                    episode_str = num.zfill(2)  # 确保两位数格式
                    break
        
        # 如果没有找到匹配的数字，使用索引作为集数
        if not episode_str:
            episode_number = index + 1
            episode_str = str(episode_number).zfill(2)
        
        # 获取集数前缀
        episode_prefix = self.episode_prefix_var.get() if hasattr(self, 'episode_prefix_var') else ''
        
        # 组合集数前缀和集数
        if episode_prefix:
            full_episode = f"{episode_prefix}{episode_str}"
        else:
            full_episode = episode_str
        
        # 替换占位符
        new_name = rule
        new_name = new_name.replace('[影视类型]', self.media_type_var.get())
        new_name = new_name.replace('[标题]', self.title_var.get() if self.title_var.get() else os.path.splitext(file_info['filename'])[0])
        new_name = new_name.replace('[季数]', self.season_var.get() if self.season_var.get() else '1')
        new_name = new_name.replace('[集数]', full_episode)
        
        # 特殊处理：如果规则包含季和集的格式，确保使用正确的连接符
        if ('季' in new_name or 'EP' in new_name) and '集' in new_name:
            # 提取季数
            season = self.season_var.get() if self.season_var.get() else '01'
            # 构建标准格式：番剧名 - 季 - 集
            title = self.title_var.get() if self.title_var.get() else os.path.splitext(file_info['filename'])[0]
            new_name = f"{title} - {season} - {full_episode}"
        
        return new_name + file_info['ext']
    
    def start_rename(self):
        if not self.files:
            messagebox.showwarning('警告', '请先添加文件')
            return
        
        if not self.title_var.get():
            messagebox.showwarning('警告', '请输入标题')
            return
        
        success_count = 0
        error_count = 0
        
        for index, file_info in enumerate(self.files):
            try:
                old_path = file_info['path']
                directory = os.path.dirname(old_path)
                new_name = self.generate_new_name(file_info, index)
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
        messagebox.showinfo('完成', f'重命名操作完成\n成功: {success_count} 个\n失败: {error_count} 个')
        
        # 清空列表并更新
        self.clear_list()
    
    def cancel_operation(self):
        self.clear_list()
        self.title_var.set('')
        self.season_var.set('')
        self.episode_var.set('')
        self.custom_rule_var.set('')
        self.log('取消了操作')
    
    def save_config(self):
        config = {
            'template': self.template_var.get(),
            'custom_rule': self.custom_rule_var.get(),
            'media_type': self.media_type_var.get(),
            'title': self.title_var.get(),
            'season': self.season_var.get(),
            'episode': self.episode_var.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.log('配置已保存')
            messagebox.showinfo('成功', '配置已保存')
        except Exception as e:
            self.log(f'保存配置失败: {str(e)}')
            messagebox.showerror('错误', f'保存配置失败: {str(e)}')
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'template' in config:
                    template = config['template']
                    try:
                        index = self.template_combo['values'].index(template)
                        self.template_combo.current(index)
                    except ValueError:
                        pass
                
                if 'custom_rule' in config:
                    self.custom_rule_var.set(config['custom_rule'])
                
                if 'media_type' in config:
                    media_type = config['media_type']
                    try:
                        index = self.media_type_combo['values'].index(media_type)
                        self.media_type_combo.current(index)
                    except ValueError:
                        pass
                
                if 'title' in config:
                    self.title_var.set(config['title'])
                
                if 'season' in config:
                    self.season_var.set(config['season'])
                
                if 'episode' in config:
                    self.episode_var.set(config['episode'])
                
                self.log('配置已加载')
            except Exception as e:
                self.log(f'加载配置失败: {str(e)}')
    
    def view_log(self):
        if os.path.exists(self.log_file):
            try:
                # 打开日志文件
                webbrowser.open(self.log_file)
            except Exception as e:
                messagebox.showerror('错误', f'查看日志失败: {str(e)}')
        else:
            messagebox.showinfo('提示', '暂无日志记录')
    
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f'[{timestamp}] {message}\n'
        
        # 更新日志文本框
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 保存到日志文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f'保存日志失败: {str(e)}')
    
    def format_file_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    # 拖拽事件处理方法暂时注释掉
    # def drag_enter_event(self, event):
    #     # 启用放置
    #     event.widget.focus_set()
    #     return event
    # 
    # def drop_event(self, event):
    #     # 获取放置的文件路径
    #     files = []
    #     if event.data:
    #         # 处理拖拽的文件路径
    #         paths = event.data.strip().split()
    #         for path in paths:
    #             # 移除路径中的引号
    #             path = path.strip('"\'')
    #             if os.path.isfile(path) and any(path.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.ts']):
    #                 files.append(path)
    #             elif os.path.isdir(path):
    #                 # 递归添加文件夹中的视频文件
    #                 for root, _, filenames in os.walk(path):
    #                     for filename in filenames:
    #                         if any(filename.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.ts']):
    #                             files.append(os.path.join(root, filename))
    #     
    #     if files:
    #         self.add_files_to_list(files)
    #     return event
    
    def show_context_menu(self, event):
        # 确保有选中的项目
        item = self.file_tree.identify_row(event.y)
        if item:
            # 选中点击的项目
            self.file_tree.selection_set(item)
            # 显示右键菜单
            self.context_menu.post(event.x_root, event.y_root)
    
    def prompt_episode_selection(self):
        # 创建选择窗口
        selection_window = tk.Toplevel(self.root)
        selection_window.title('选择集数对应的数字')
        selection_window.geometry('600x400')
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        # 创建滚动区域
        canvas = tk.Canvas(selection_window)
        scrollbar = ttk.Scrollbar(selection_window, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 显示文件和数字信息
        ttk.Label(scrollable_frame, text='请选择哪个数字序列代表集数:', font=('Arial', 10, 'bold')).pack(pady=10)
        
        # 收集所有文件中的数字序列
        all_numbers = []
        for file_info in self.files:
            numbers = file_info.get('numbers', [])
            if numbers:
                all_numbers.extend(numbers)
        
        # 去重并排序
        unique_numbers = sorted(list(set(all_numbers)), key=lambda x: int(x))
        
        # 创建选项列表
        if unique_numbers:
            ttk.Label(scrollable_frame, text='可用的数字序列:').pack(anchor=tk.W, padx=20)
            
            # 创建变量存储选择
            selected_var = tk.IntVar(value=-1)
            
            # 创建选项按钮
            for i, num in enumerate(unique_numbers):
                ttk.Radiobutton(
                    scrollable_frame, 
                    text=f'数字: {num}', 
                    variable=selected_var, 
                    value=i
                ).pack(anchor=tk.W, padx=40, pady=2)
            
            # 创建确认按钮
            def confirm_selection():
                selected = selected_var.get()
                if selected >= 0 and selected < len(unique_numbers):
                    # 保存选择的数字
                    self.episode_pattern = unique_numbers[selected]
                    # 根据选择的数字排序文件
                    self.sort_files_by_episode()
                    # 更新预览
                    self.update_preview()
                    self.log(f'选择了数字序列 "{unique_numbers[selected]}" 作为集数')
                    selection_window.destroy()
                else:
                    messagebox.showwarning('警告', '请选择一个数字序列')
            
            ttk.Button(scrollable_frame, text='确认选择', command=confirm_selection).pack(pady=20)
        else:
            ttk.Label(scrollable_frame, text='未在文件名中检测到数字序列').pack(pady=20)
            ttk.Button(scrollable_frame, text='确定', command=selection_window.destroy).pack(pady=10)
    
    def sort_files_by_episode(self):
        # 根据用户选择的数字排序文件
        if not hasattr(self, 'episode_pattern'):
            return
        
        def get_episode_number(file_info):
            numbers = file_info.get('numbers', [])
            for num in numbers:
                if num == self.episode_pattern:
                    return int(num)
            return 0
        
        # 排序文件列表
        self.files.sort(key=get_episode_number)
        # 更新文件树
        self.update_file_tree()
    
    def update_episode_match_display(self):
        # 检查是否有文件
        if not self.files:
            self.episode_match_label.config(text='')
            return
        
        # 获取第一个文件的文件名
        first_file = self.files[0]
        filename = first_file['filename']
        numbers = first_file.get('numbers', [])
        
        if not numbers:
            self.episode_match_label.config(text='')
            return
        
        # 构建带有高亮的文本
        # 这里使用简单的文本显示，实际项目中可以使用更复杂的富文本
        display_text = filename
        
        # 存储数字位置信息
        self.number_positions = []
        pos = 0
        for num in numbers:
            start = display_text.find(num, pos)
            if start >= 0:
                self.number_positions.append((start, start + len(num), num))
                pos = start + len(num)
        
        # 更新标签文本
        self.episode_match_label.config(text=display_text)
        # 设置标签样式，使其看起来可点击
        self.episode_match_label.config(foreground='blue', cursor='hand2')
    
    def on_episode_label_click(self, event):
        # 获取点击位置
        x = event.x
        y = event.y
        
        # 获取标签文本的边界框
        bbox = self.episode_match_label.bbox(0, 0)
        if not bbox:
            return
        
        # 获取标签文本
        text = self.episode_match_label['text']
        text_length = len(text)
        if text_length == 0:
            return
        
        # 计算点击位置对应的文本索引
        text_width = bbox[2] - bbox[0]
        if text_width == 0:
            return
        
        char_width = text_width / text_length
        click_index = int(x / char_width)
        
        # 确保索引在有效范围内
        click_index = max(0, min(click_index, text_length - 1))
        
        # 检查点击位置是否在数字范围内
        for start, end, num in self.number_positions:
            if start <= click_index < end:
                # 选择该数字作为集数模式
                self.episode_pattern = num
                # 根据选择的数字排序文件
                self.sort_files_by_episode()
                # 更新预览
                self.update_preview()
                # 更新标签样式，显示选中状态
                self.episode_match_label.config(foreground='green')
                self.log(f'选择了数字 "{num}" 作为集数模式')
                break
    
    def delete_selected_file(self):
        # 获取选中的项目
        selected_items = self.file_tree.selection()
        if not selected_items:
            return
        
        # 删除选中的文件
        for item in selected_items:
            # 获取项目的索引
            index = self.file_tree.index(item)
            # 从文件列表中删除
            if 0 <= index < len(self.files):
                deleted_file = self.files[index]['filename']
                del self.files[index]
                self.log(f'从列表中删除文件: {deleted_file}')
        
        # 更新文件树和预览
        self.update_file_tree()
        self.update_preview()
        # 更新集数匹配显示
        self.update_episode_match_display()

if __name__ == '__main__':
    root = tk.Tk()
    app = MovieRenamerApp(root)
    root.mainloop()
