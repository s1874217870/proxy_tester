import tkinter as tk
from tkinter import ttk, messagebox
import requests
import time
import threading
from urllib.parse import urlparse
import json
import re
from concurrent.futures import ThreadPoolExecutor

class ProxySpeedTester:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("代理IP检测工具")
        self.window.geometry("1200x800")
        self.window.configure(bg='#f8fafc')
        
        # 设置主题样式
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # 自定义现代风格
        self.style.configure('TFrame', background='#f8fafc')
        self.style.configure('TLabel', background='#f8fafc', font=('微软雅黑', 10))
        self.style.configure('TButton', font=('微软雅黑', 10), padding=(12, 6))
        self.style.configure('Treeview', font=('微软雅黑', 10), rowheight=35)
        self.style.configure('Card.TFrame', background='#ffffff', relief='solid', borderwidth=1, bordercolor='#e2e8f0')
        self.style.configure('Card.TLabel', background='#ffffff', font=('微软雅黑', 10))
        
        # 按钮样式
        self.style.configure('Primary.TButton',
                           background='#3b82f6',
                           foreground='#ffffff',
                           padding=(24, 10),
                           borderwidth=0,
                           relief='flat')
        self.style.map('Primary.TButton',
                      background=[('active', '#2563eb')])
        
        self.style.configure('Secondary.TButton',
                           background='#64748b',
                           foreground='#ffffff',
                           padding=(24, 10),
                           borderwidth=0,
                           relief='flat')
        self.style.map('Secondary.TButton',
                      background=[('active', '#475569')])
        
        # 表格样式
        self.style.configure('Custom.Treeview',
                           background='#ffffff',
                           fieldbackground='#ffffff',
                           foreground='#334155',
                           font=('微软雅黑', 10),
                           borderwidth=1)
        self.style.map('Custom.Treeview',
                      background=[('selected', '#dbeafe')],
                      foreground=[('selected', '#1e40af')])
        
        # 初始化目标地址
        self.target_entry = None
        self.default_target = "https://ipinfo.io/json"
        self.current_request_id = 0
        
        # 初始化统计数据
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'timeout': 0,
            'status_codes': {}
        }
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=50)
        
        # 初始化UI
        self.setup_ui()

    def test_connection(self, target_name, url, request_id):
        try:
            proxy_url = self.proxy_entry.get().strip()
            proxy = {
                'http': proxy_url,
                'https': proxy_url
            } if proxy_url else None
            
            start_time = time.time()
            response = requests.get(url, proxies=proxy, timeout=10)
            elapsed_time = time.time() - start_time
            
            # 更新状态码统计
            status_code = str(response.status_code)
            self.stats['status_codes'][status_code] = self.stats['status_codes'].get(status_code, 0) + 1
            
            if response.status_code == 200:
                self.stats['success'] += 1
                response.encoding = 'utf-8'  # 设置响应编码为UTF-8
                try:
                    response_data = response.json()
                    details = f"请求ID: {request_id}\n响应时间: {elapsed_time:.2f}秒\n状态码: {response.status_code}\n\n响应数据:\n"
                    formatted_data = json.dumps(response_data, ensure_ascii=False, indent=2)
                    details += formatted_data
                except json.JSONDecodeError:
                    # 如果不是JSON格式，直接显示原始文本
                    details = f"请求ID: {request_id}\n响应时间: {elapsed_time:.2f}秒\n状态码: {response.status_code}\n\n响应数据:\n{response.text}"
                return "成功", details, elapsed_time
            else:
                self.stats['failed'] = self.stats.get('failed', 0) + 1
                response.encoding = 'utf-8'
                error_details = f"HTTP错误: {response.status_code}\n响应内容:\n{response.text}"
                return "失败", error_details, 0
                    
        except requests.exceptions.Timeout:
            self.stats['timeout'] += 1
            self.stats['failed'] = self.stats.get('failed', 0) + 1
            error_code = 'TIMEOUT'
            self.stats['status_codes'][error_code] = self.stats['status_codes'].get(error_code, 0) + 1
            return "失败", "连接超时", 0
        except requests.exceptions.ProxyError as e:
            self.stats['failed'] = self.stats.get('failed', 0) + 1
            error_message = "代理服务器连接失败"
            status_code = 'PROXY_ERROR'
            
            # 获取原始错误对象
            cause = e.__context__
            if cause:
                if hasattr(cause, 'response') and cause.response:
                    try:
                        response = cause.response
                        response.encoding = 'utf-8'
                        error_message = response.text
                        if not error_message and response.content:
                            error_message = response.content.decode('utf-8', errors='replace')
                        status_code = str(response.status_code)
                    except Exception as decode_error:
                        error_message = f"解码错误: {str(decode_error)}"
                elif str(cause).startswith('errorMsg:'):
                    # 直接处理类似 'errorMsg: user forbidden...' 的错误信息
                    error_message = str(cause)
                    status_code = '403'  # 对于这类错误，通常是403 Forbidden
            
            # 更新统计信息
            self.stats['status_codes'][status_code] = self.stats['status_codes'].get(status_code, 0) + 1
            
            return "失败", error_message, 0
            self.stats['failed'] = self.stats.get('failed', 0) + 1
            error_message = "代理服务器连接失败"
            status_code = 'PROXY_ERROR'
            
            # 获取原始错误对象
            cause = e.__context__
            if cause:
                if hasattr(cause, 'response') and cause.response:
                    try:
                        response = cause.response
                        response.encoding = 'utf-8'
                        error_message = response.text
                        if not error_message and response.content:
                            error_message = response.content.decode('utf-8', errors='replace')
                        status_code = str(response.status_code)
                        
                        # 更新统计信息中的状态码
                        self.stats['status_codes'][status_code] = self.stats['status_codes'].get(status_code, 0) + 1
                        return "失败", error_message, 0
                    except Exception as decode_error:
                        error_message = f"解码错误: {str(decode_error)}"
                elif str(cause).startswith('errorMsg:'):
                    # 直接处理类似 'errorMsg: user forbidden...' 的错误信息
                    error_message = str(cause)
                    status_code = '403'  # 对于这类错误，通常是403 Forbidden
                    self.stats['status_codes'][status_code] = self.stats['status_codes'].get(status_code, 0) + 1
                    return "失败", error_message, 0
            
            # 更新统计信息
            self.stats['status_codes'][status_code] = self.stats['status_codes'].get(status_code, 0) + 1
            
            return "失败", error_message, 0
        except requests.exceptions.RequestException as e:
            self.stats['failed'] = self.stats.get('failed', 0) + 1
            error_code = 'CONNECTION_ERROR'
            self.stats['status_codes'][error_code] = self.stats['status_codes'].get(error_code, 0) + 1
            return "失败", f"连接错误: {str(e)}", 0

    def clear_results(self):
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        # 重置统计数据
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'timeout': 0,
            'status_codes': {}
        }
        self.update_stats_display()
        self.update_details_display("")

    def update_stats_display(self):
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            failed_rate = (self.stats['failed'] / self.stats['total']) * 100
            timeout_rate = (self.stats['timeout'] / self.stats['total']) * 100
            
            stats_text = f"测试总数: {self.stats['total']}\n"
            stats_text += f"成功次数: {self.stats['success']}\n"
            stats_text += f"失败次数: {self.stats['failed']}\n"
            stats_text += f"超时次数: {self.stats['timeout']}\n\n"
            stats_text += f"成功率: {success_rate:.2f}%\n"
            stats_text += f"失败率: {failed_rate:.2f}%\n"
            stats_text += f"超时率: {timeout_rate:.2f}%\n\n"
            stats_text += "状态码分布:\n"
            for code, count in self.stats['status_codes'].items():
                percentage = (count / self.stats['total']) * 100
                stats_text += f"状态码 {code}: {count} 次 ({percentage:.2f}%)\n"
        else:
            stats_text = "暂无测试数据"
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', stats_text)
        self.stats_text.config(state=tk.DISABLED)

    def update_details_display(self, details):
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', details)
        self.details_text.config(state=tk.DISABLED)

    def on_tree_select(self, event):
        selected_items = self.result_tree.selection()
        if selected_items:
            item = selected_items[0]
            details = self.result_tree.item(item)['tags'][0]
            self.update_details_display(details)

    def start_test(self):
        try:
            test_count = int(self.count_entry.get())
            concurrency = int(self.concurrency_entry.get())
            if test_count <= 0 or concurrency <= 0:
                messagebox.showerror("错误", "请输入大于0的测试次数和并发数量")
                return
            
            # 更新线程池的并发数量
            self.executor._max_workers = concurrency
        except ValueError:
            messagebox.showerror("错误", "请输入有效的测试次数和并发数量")
            return

        # 清除之前的结果
        self.clear_results()
        
        # 创建线程进行测试
        def run_tests():
            # 创建所有测试任务
            futures = []
            for _ in range(test_count):
                target_url = self.target_entry.get().strip() or self.default_target
                self.current_request_id += 1
                self.stats['total'] += 1
                future = self.executor.submit(self.test_connection, "Target", target_url, self.current_request_id)
                futures.append((self.current_request_id, future))

            # 处理测试结果
            def update_ui(rid, status, elapsed_time, details, status_code):
                self.result_tree.insert('', 'end', values=(rid, status, 
                    f"{elapsed_time:.2f}" if elapsed_time > 0 else "N/A", 
                    status_code if status == "成功" else details.split('\n')[0]), 
                    tags=(details,))
                self.update_stats_display()

            # 批量处理结果
            batch_size = 5
            for i in range(0, len(futures), batch_size):
                batch = futures[i:i + batch_size]
                batch_updates = []
                
                for request_id, future in batch:
                    try:
                        status, details, elapsed_time = future.result()
                        status_code = "N/A"
                        if "状态码:" in details:
                            status_code = details.split("状态码:")[1].split("\n")[0].strip()
                        
                        batch_updates.append((request_id, status, elapsed_time, details, status_code))
                    except Exception as e:
                        error_message = str(e)
                        batch_updates.append((request_id, "失败", 0, f"执行错误: {error_message}", "N/A"))
                
                # 批量更新UI
                if batch_updates:
                    self.window.after(0, lambda updates=batch_updates: 
                        [update_ui(rid, s, rt, d, sc) for rid, s, rt, d, sc in updates])
                    time.sleep(0.01)  # 小延迟以避免UI卡顿
        
        # 启动测试线程
        test_thread = threading.Thread(target=run_tests)
        test_thread.daemon = True
        test_thread.start()

    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(padx=24, pady=24, fill=tk.BOTH, expand=True)
        
        # 代理设置区域 - 使用圆角卡片样式
        proxy_frame = ttk.Frame(main_frame, style='Card.TFrame')
        proxy_frame.pack(fill=tk.X, pady=(0, 24), ipady=18)
        
        # 标题
        title_label = ttk.Label(proxy_frame, text="代理设置", 
                               font=('微软雅黑', 12, 'bold'),
                               style='Card.TLabel')
        title_label.pack(anchor=tk.W, padx=20, pady=(15, 20))
        
        # 输入区域容器 - 使用Grid布局
        input_frame = ttk.Frame(proxy_frame, style='Card.TFrame')
        input_frame.pack(fill=tk.X, padx=20)
        
        # 使用Grid布局重新排列输入框
        # 目标地址输入
        target_label = ttk.Label(input_frame, text="目标地址:", style='Card.TLabel')
        target_label.grid(row=0, column=0, padx=(0, 8), pady=5)
        
        self.target_entry = ttk.Entry(input_frame, width=45, font=('微软雅黑', 10))
        self.target_entry.grid(row=0, column=1, padx=(0, 20), pady=5)
        self.target_entry.insert(0, self.default_target)

        # 代理地址输入
        proxy_label = ttk.Label(input_frame, text="代理地址:", style='Card.TLabel')
        proxy_label.grid(row=1, column=0, padx=(0, 8), pady=5)
        
        self.proxy_entry = ttk.Entry(input_frame, width=45, font=('微软雅黑', 10))
        self.proxy_entry.grid(row=1, column=1, padx=(0, 20), pady=5)
        self.proxy_entry.insert(0, "http://ceshishifuqi:ceshishifuqi@proxy.ipidea.io:2333")
        
        count_label = ttk.Label(input_frame, text="测试次数:", style='Card.TLabel')
        count_label.grid(row=1, column=2, padx=(0, 8), pady=5)
        
        self.count_entry = ttk.Entry(input_frame, width=8, font=('微软雅黑', 10))
        self.count_entry.grid(row=1, column=3, padx=(0, 20), pady=5)
        self.count_entry.insert(0, "100")
        
        concurrency_label = ttk.Label(input_frame, text="并发数量:", style='Card.TLabel')
        concurrency_label.grid(row=1, column=4, padx=(0, 8), pady=5)
        
        self.concurrency_entry = ttk.Entry(input_frame, width=8, font=('微软雅黑', 10))
        self.concurrency_entry.grid(row=1, column=5, pady=5)
        self.concurrency_entry.insert(0, "50")
        
        # 按钮区域
        button_frame = ttk.Frame(proxy_frame, style='Card.TFrame')
        button_frame.pack(anchor=tk.E, padx=15, pady=(12, 0))
        
        test_button = ttk.Button(button_frame, text="开始测试", style="Primary.TButton",
                                command=self.start_test)
        test_button.pack(side=tk.LEFT, padx=6)
        
        clear_button = ttk.Button(button_frame, text="清除结果", style="Secondary.TButton",
                                 command=self.clear_results)
        clear_button.pack(side=tk.LEFT, padx=6)
        
        # 创建下方的三列布局
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧结果列表区域
        result_frame = ttk.Frame(content_frame, style='Card.TFrame')
        result_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        result_title = ttk.Label(result_frame, text="测试结果列表", 
                                font=('微软雅黑', 12, 'bold'),
                                style='Card.TLabel')
        result_title.pack(anchor=tk.W, padx=15, pady=10)
        
        # 创建表格和滚动条
        tree_frame = ttk.Frame(result_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # 创建滚动条
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建表格
        columns = ("request_id", "status", "response_time", "http_status")
        self.result_tree = ttk.Treeview(tree_frame, columns=columns, 
                                       show="headings", 
                                       style="Custom.Treeview",
                                       height=5,  # 限制显示5行
                                       yscrollcommand=tree_scroll.set)
        
        # 设置列标题
        self.result_tree.heading("request_id", text="请求ID")
        self.result_tree.heading("status", text="状态")
        self.result_tree.heading("response_time", text="响应时间(秒)")
        self.result_tree.heading("http_status", text="HTTP状态/错误信息")
        
        # 设置列宽
        self.result_tree.column("request_id", width=100, anchor="center")
        self.result_tree.column("status", width=100, anchor="center")
        self.result_tree.column("response_time", width=120, anchor="center")
        self.result_tree.column("http_status", width=200, anchor="center")
        
        # 设置表格行高和换行显示
        self.style.configure('Custom.Treeview',
                           rowheight=35)  # 调整行高为合适的大小
        
        # 配置滚动条
        tree_scroll.config(command=self.result_tree.yview)
        
        # 中间统计信息区域
        stats_frame = ttk.Frame(content_frame, style='Card.TFrame')
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=8, pady=0)
        
        stats_title = ttk.Label(stats_frame, text="测试统计信息", 
                               font=('微软雅黑', 11, 'bold'),
                               style='Card.TLabel')
        stats_title.pack(anchor=tk.W, padx=12, pady=8)
        
        self.stats_text = tk.Text(stats_frame, width=25, height=20, font=('微软雅黑', 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.stats_text.config(state=tk.DISABLED)
        
        # 右侧详细信息区域
        details_frame = ttk.Frame(content_frame, style='Card.TFrame')
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 0))
        
        details_title = ttk.Label(details_frame, text="详细信息", 
                                 font=('微软雅黑', 11, 'bold'),
                                 style='Card.TLabel')
        details_title.pack(anchor=tk.W, padx=12, pady=8)
        
        self.details_text = tk.Text(details_frame, width=32, height=20, font=('微软雅黑', 9))
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.details_text.config(state=tk.DISABLED)
        
        # 绑定选择事件
        self.result_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.result_tree.pack(fill=tk.BOTH, expand=True)

if __name__ == '__main__':
    app = ProxySpeedTester()
    app.window.mainloop()