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

        # 添加警告按钮样式
        self.style.configure('Warning.TButton',
                           background='#f59e0b',
                           foreground='#ffffff',
                           padding=(24, 10),
                           borderwidth=0,
                           relief='flat')
        self.style.map('Warning.TButton',
                      background=[('active', '#d97706')])

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
            'status_codes': {},
            'total_response_time': 0  # 添加总响应时间统计
        }

        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=50)

        # 初始化测试状态
        self.is_testing = False
        self.pause_testing = False

        # 初始化UI
        self.setup_ui()

        # 异步检测本机IP归属地
        threading.Thread(target=self.check_local_ip, daemon=True).start()

    def check_local_ip(self):
        # 使用多个IP查询服务，按顺序尝试
        ip_services = [
            'https://ipinfo.ipidea.io',
            'https://ipinfo.io/json',
            'https://api.ipify.org?format=json',
            'https://api.myip.com'
        ]

        for service_url in ip_services:
            try:
                # 增加超时时间到10秒
                response = requests.get(service_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    # 根据不同服务解析不同的返回格式
                    ip = data.get('ip', '')
                    country = data.get('country_code', data.get('country', ''))
                    region = data.get('province', data.get('region', ''))
                    city = data.get('city', '')
                    country_code = data.get('country_code', data.get('countryCode', ''))
                    org = data.get('org', '')
                    hostname = data.get('hostname', '')
                    loc = data.get('loc', '')
                    postal = data.get('postal', '')
                    timezone = data.get('timezone', '')
                    asn = data.get('asn', {}).get('asn', data.get('asn', ''))
                    asn_name = data.get('asn', {}).get('name', data.get('asn_name', ''))
                    asn_domain = data.get('asn', {}).get('domain', data.get('asn_domain', ''))
                    asn_route = data.get('asn', {}).get('route', data.get('asn_route', ''))
                    asn_type = data.get('asn', {}).get('type', data.get('asn_type', ''))

                    # 构建完整的IP信息
                    location_info = f"IP: {ip}"

                    if hostname:
                        location_info += f"\n主机名: {hostname}"

                    if country or region or city:
                        location_info += f"\n位置: {country} {region} {city}"

                    if loc:
                        location_info += f"\n坐标: {loc}"

                    if postal:
                        location_info += f"\n邮编: {postal}"

                    if timezone:
                        location_info += f"\n时区: {timezone}"

                    if org:
                        location_info += f"\n组织: {org}"

                    if asn:
                        location_info += f"\nASN: {asn}"

                    if asn_name:
                        location_info += f"\nASN名称: {asn_name}"

                    if asn_domain:
                        location_info += f"\nASN域名: {asn_domain}"

                    if asn_route:
                        location_info += f"\nASN路由: {asn_route}"

                    if asn_type:
                        location_info += f"\nASN类型: {asn_type}"

                    # 判断是否为国内IP
                    if country_code == 'CN':
                        location_info += "\n\n⚠️ 当前IP为中国大陆IP，可能无法正常使用代理服务"
                        text_color = '#ef4444'
                    else:
                        location_info += "\n\n✅ 当前IP为海外IP，可以正常使用代理服务"
                        text_color = '#22c55e'

                    # 更新Text控件内容
                    self.ip_info_text.config(state=tk.NORMAL)
                    self.ip_info_text.delete('1.0', tk.END)
                    self.ip_info_text.insert('1.0', location_info)
                    self.ip_info_text.tag_configure("color", foreground=text_color)
                    self.ip_info_text.tag_add("color", "1.0", "end")
                    self.ip_info_text.config(state=tk.DISABLED)

                    # 同时更新隐藏的Label以保持兼容性
                    self.ip_info_label.config(text=location_info, foreground=text_color)
                    return
            except requests.exceptions.Timeout:
                continue  # 超时则尝试下一个服务
            except requests.exceptions.RequestException:
                continue  # 请求异常则尝试下一个服务
            except Exception:
                continue  # 其他异常则尝试下一个服务

        # 所有服务都失败时显示错误信息
        error_message = "获取IP信息失败: 所有IP查询服务均无响应，请检查网络连接"
        # 更新Text控件显示错误信息
        self.ip_info_text.config(state=tk.NORMAL)
        self.ip_info_text.delete('1.0', tk.END)
        self.ip_info_text.insert('1.0', error_message)
        self.ip_info_text.tag_configure("error", foreground='#ef4444')
        self.ip_info_text.tag_add("error", "1.0", "end")
        self.ip_info_text.config(state=tk.DISABLED)

        # 同时更新隐藏的Label以保持兼容性
        self.ip_info_label.config(text=error_message, foreground='#ef4444')

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
                self.stats['total_response_time'] += elapsed_time  # 累计响应时间
                self.stats['response_times'].append(elapsed_time)  # 记录所有响应时间

                # 更新最大和最小响应时间
                if elapsed_time > self.stats['max_response_time']:
                    self.stats['max_response_time'] = elapsed_time
                if elapsed_time < self.stats['min_response_time']:
                    self.stats['min_response_time'] = elapsed_time

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
        except requests.exceptions.RequestException as e:
            self.stats['failed'] = self.stats.get('failed', 0) + 1
            error_code = 'CONNECTION_ERROR'
            self.stats['status_codes'][error_code] = self.stats['status_codes'].get(error_code, 0) + 1
            return "失败", f"连接错误: {str(e)}", 0

    def clear_results(self):
        # 清除树视图中的所有项目
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        # 重置统计数据
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'timeout': 0,
            'status_codes': {},
            'total_response_time': 0,  # 总响应时间统计
            'max_response_time': 0,    # 最大响应时间
            'min_response_time': float('inf'),  # 最小响应时间
            'response_times': []       # 所有响应时间列表，用于计算中位数和其他统计
        }
        self.update_stats_display()
        self.update_details_display("")
        # 确保UI更新
        self.window.update_idletasks()

    def update_stats_display(self):
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            failed_rate = (self.stats['failed'] / self.stats['total']) * 100
            timeout_rate = (self.stats['timeout'] / self.stats['total']) * 100

            # 计算平均响应时间
            avg_response_time = 0
            if self.stats['success'] > 0:
                avg_response_time = self.stats['total_response_time'] / self.stats['success']

            stats_text = f"测试总数: {self.stats['total']}\n"
            stats_text += f"成功次数: {self.stats['success']}\n"
            stats_text += f"失败次数: {self.stats['failed']}\n"
            stats_text += f"超时次数: {self.stats['timeout']}\n"
            stats_text += f"平均响应时间: {avg_response_time:.3f}秒\n\n"  # 添加平均响应时间
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
        # 如果测试已经在运行，则不重复启动
        if self.is_testing:
            return

        # 清除之前的测试结果
        self.clear_results()

        try:
            test_count = int(self.count_entry.get())
            concurrency = int(self.concurrency_entry.get())
            if test_count <= 0 or concurrency <= 0:
                messagebox.showerror("错误", "请输入大于0的测试次数和并发数量")
                return

            # 更新线程池的并发数量
            self.executor._max_workers = concurrency

            # 启用测试按钮，确保UI状态正确
            self.test_button.config(state="normal")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的测试次数和并发数量")
            return

        # 设置测试状态
        self.is_testing = True
        self.pause_testing = False
        self.pause_button.config(text="暂停测试", state="normal")

        # 创建结果队列，用于线程安全地传递测试结果
        import queue
        result_queue = queue.Queue()

        # 定义UI更新函数，在主线程中定期检查队列并更新UI
        def update_ui():
            try:
                # 尝试从队列获取结果，但不阻塞
                while not result_queue.empty():
                    rid, status, elapsed_time, details, status_code = result_queue.get_nowait()
                    # 插入结果到树视图
                    self.result_tree.insert('', 'end', values=(rid, status,
                        f"{elapsed_time:.2f}" if elapsed_time > 0 else "N/A",
                        status_code if status == "成功" else details.split('\n')[0]),
                        tags=(details,))
                    # 确保滚动到最新的结果
                    self.result_tree.see(self.result_tree.get_children()[-1])
                    # 更新统计信息显示
                    self.update_stats_display()
                    # 标记任务完成
                    result_queue.task_done()
                    # 确保UI更新
                    self.window.update_idletasks()
            except queue.Empty:
                # 队列为空，继续等待
                pass

            # 如果测试仍在进行，继续定期检查队列
            if self.is_testing:
                self.window.after(100, update_ui)

        # 启动UI更新循环
        self.window.after(100, update_ui)

        # 创建线程进行测试
        def run_tests():
            try:
                # 创建所有测试任务
                futures = []
                for _ in range(test_count):
                    target_url = self.target_entry.get().strip() or self.default_target
                    self.current_request_id += 1
                    self.stats['total'] += 1
                    future = self.executor.submit(self.test_connection, "Target", target_url, self.current_request_id)
                    futures.append((self.current_request_id, future))

                # 批量处理结果
                batch_size = 5
                for i in range(0, len(futures), batch_size):
                    # 检查是否暂停
                    while self.pause_testing and self.is_testing:
                        time.sleep(0.1)

                    # 检查是否停止测试
                    if not self.is_testing:
                        break

                    batch = futures[i:i + batch_size]

                    for request_id, future in batch:
                        try:
                            status, details, elapsed_time = future.result()
                            status_code = "N/A"
                            if "状态码:" in details:
                                status_code = details.split("状态码:")[1].split("\n")[0].strip()
                            elif "状态码: " in details:
                                status_code = details.split("状态码: ")[1].split("\n")[0].strip()
                            elif status == "成功":
                                status_code = "200"

                            # 将结果放入队列，由主线程处理UI更新
                            result_queue.put((request_id, status, elapsed_time, details, status_code))

                        except Exception as e:
                            error_message = str(e)
                            # 将错误结果放入队列
                            result_queue.put((request_id, "失败", 0, f"执行错误: {error_message}", "N/A"))

                    # 小延迟以避免UI卡顿
                    time.sleep(0.01)
            finally:
                # 测试完成后重置状态
                self.is_testing = False
                self.pause_testing = False
                # 使用after方法在主线程中更新按钮状态
                self.window.after(0, lambda: self.pause_button.config(text="暂停测试", state="disabled"))
                # 恢复测试按钮状态
                self.window.after(0, lambda: self.test_button.config(text="开始测试", state="normal"))
                # 确保最后一次更新UI
                self.window.after(0, self.update_stats_display)

        # 设置测试按钮状态
        self.test_button.config(text="测试中...", state="disabled")

        # 启动测试线程
        test_thread = threading.Thread(target=run_tests)
        test_thread.daemon = True
        test_thread.start()

    def toggle_pause(self):
        if not self.is_testing:
            return

        self.pause_testing = not self.pause_testing
        if self.pause_testing:
            self.pause_button.config(text="继续测试", state="normal")
        else:
            self.pause_button.config(text="暂停测试", state="normal")

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
        target_label.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="e")

        self.target_entry = ttk.Entry(input_frame, width=45, font=('微软雅黑', 10))
        self.target_entry.grid(row=0, column=1, padx=(0, 20), pady=5, sticky="ew")
        self.target_entry.insert(0, self.default_target)

        # 代理地址输入
        proxy_label = ttk.Label(input_frame, text="代理地址:", style='Card.TLabel')
        proxy_label.grid(row=1, column=0, padx=(0, 8), pady=5, sticky="e")

        self.proxy_entry = ttk.Entry(input_frame, width=45, font=('微软雅黑', 10))
        self.proxy_entry.grid(row=1, column=1, padx=(0, 20), pady=5, sticky="ew")
        self.proxy_entry.insert(0, "http://ceshishifuqi:ceshishifuqi@proxy.ipidea.io:2333")

        count_label = ttk.Label(input_frame, text="测试次数:", style='Card.TLabel')
        count_label.grid(row=0, column=2, padx=(0, 8), pady=5, sticky="e")

        self.count_entry = ttk.Entry(input_frame, width=8, font=('微软雅黑', 10))
        self.count_entry.grid(row=0, column=3, padx=(0, 20), pady=5)
        self.count_entry.insert(0, "100")

        concurrency_label = ttk.Label(input_frame, text="并发数量:", style='Card.TLabel')
        concurrency_label.grid(row=1, column=2, padx=(0, 8), pady=5, sticky="e")

        self.concurrency_entry = ttk.Entry(input_frame, width=8, font=('微软雅黑', 10))
        self.concurrency_entry.grid(row=1, column=3, pady=5)
        self.concurrency_entry.insert(0, "50")

        # 配置列权重，使输入框可以随窗口调整大小
        input_frame.columnconfigure(1, weight=1)

        # 按钮区域
        button_frame = ttk.Frame(proxy_frame, style='Card.TFrame')
        button_frame.pack(anchor=tk.E, padx=15, pady=(12, 0))

        self.test_button = ttk.Button(button_frame, text="开始测试", style="Primary.TButton",
                                command=self.start_test)
        self.test_button.pack(side=tk.LEFT, padx=6)

        self.pause_button = ttk.Button(button_frame, text="暂停测试", style="Warning.TButton",
                                 command=self.toggle_pause, state="disabled")
        self.pause_button.pack(side=tk.LEFT, padx=6)

        clear_button = ttk.Button(button_frame, text="清除结果", style="Secondary.TButton",
                                 command=self.clear_results)
        clear_button.pack(side=tk.LEFT, padx=6)

        # 创建标签页容器
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 创建代理连接测试标签页
        self.main_tab = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.main_tab, text='代理连接测试')

        # 创建下方的三列布局
        content_frame = ttk.Frame(self.main_tab)
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
                                       height=10,  # 增加显示行数
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

        # 绑定选择事件
        self.result_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.result_tree.pack(fill=tk.BOTH, expand=True)

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

        # 右侧区域 - 包含详细信息和IP信息
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 0))

        # 详细信息区域
        details_frame = ttk.Frame(right_frame, style='Card.TFrame')
        details_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))

        details_title = ttk.Label(details_frame, text="详细信息",
                                 font=('微软雅黑', 11, 'bold'),
                                 style='Card.TLabel')
        details_title.pack(anchor=tk.W, padx=12, pady=8)

        # 创建滚动条和文本框
        details_scroll = ttk.Scrollbar(details_frame)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.details_text = tk.Text(details_frame, width=32, height=20, font=('微软雅黑', 9), yscrollcommand=details_scroll.set)
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=(12, 12), pady=(0, 12))
        self.details_text.config(state=tk.DISABLED)
        details_scroll.config(command=self.details_text.yview)

        # IP信息区域 - 现在放在右下角，使用文本框和滚动条显示更多信息
        ip_frame = ttk.Frame(right_frame, style='Card.TFrame')
        ip_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 0))

        # IP信息标题
        ip_title = ttk.Label(ip_frame, text="本机IP信息",
                            font=('微软雅黑', 11, 'bold'),
                            style='Card.TLabel')
        ip_title.pack(anchor=tk.W, padx=12, pady=8)

        # 创建滚动条和文本框用于显示IP信息
        ip_scroll = ttk.Scrollbar(ip_frame)
        ip_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 使用Text控件替代Label，以便显示更多内容并支持滚动
        # 增加height参数从8到12，以便能够显示两行信息
        self.ip_info_text = tk.Text(ip_frame, width=32, height=12, font=('微软雅黑', 9), yscrollcommand=ip_scroll.set)
        self.ip_info_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.ip_info_text.insert('1.0', "正在获取IP信息...")
        self.ip_info_text.config(state=tk.DISABLED)
        ip_scroll.config(command=self.ip_info_text.yview)

        # 保留一个隐藏的Label用于兼容现有代码
        self.ip_info_label = ttk.Label(ip_frame, text="", style='Card.TLabel')
        self.ip_info_label.pack_forget()

        # 绑定选择事件
        self.result_tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        # 创建下载速度测试标签页
        self.download_speed_tab = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.download_speed_tab, text='下载速度测试')

        # 下载速度测试设置区域
        speed_settings_frame = ttk.Frame(self.download_speed_tab, style='Card.TFrame')
        speed_settings_frame.pack(fill=tk.X, pady=(24, 24), ipady=18, padx=24)

        # 标题
        speed_title_label = ttk.Label(speed_settings_frame, text="下载速度测试设置",
                                   font=('微软雅黑', 12, 'bold'),
                                   style='Card.TLabel')
        speed_title_label.pack(anchor=tk.W, padx=20, pady=(15, 20))

        # 输入区域容器
        speed_input_frame = ttk.Frame(speed_settings_frame, style='Card.TFrame')
        speed_input_frame.pack(fill=tk.X, padx=20)

        # 测试次数输入
        speed_count_label = ttk.Label(speed_input_frame, text="测试次数:", style='Card.TLabel')
        speed_count_label.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="e")

        self.speed_count_entry = ttk.Entry(speed_input_frame, width=8, font=('微软雅黑', 10))
        self.speed_count_entry.grid(row=0, column=1, padx=(0, 20), pady=5)
        self.speed_count_entry.insert(0, "10")

        # 并发数量输入
        speed_concurrency_label = ttk.Label(speed_input_frame, text="并发数量:", style='Card.TLabel')
        speed_concurrency_label.grid(row=0, column=2, padx=(0, 8), pady=5, sticky="e")

        self.speed_concurrency_entry = ttk.Entry(speed_input_frame, width=8, font=('微软雅黑', 10))
        self.speed_concurrency_entry.grid(row=0, column=3, pady=5)
        self.speed_concurrency_entry.insert(0, "5")

        # 按钮区域
        speed_button_frame = ttk.Frame(speed_settings_frame, style='Card.TFrame')
        speed_button_frame.pack(anchor=tk.E, padx=15, pady=(12, 0))

        self.speed_test_button = ttk.Button(speed_button_frame, text="开始测试", style="Primary.TButton",
                                        command=self.test_download_speed, width=15)
        self.speed_test_button.pack(side=tk.LEFT, padx=6)

        # 创建结果区域
        speed_content_frame = ttk.Frame(self.download_speed_tab)
        speed_content_frame.pack(fill=tk.BOTH, expand=True, padx=24)

        # 创建隐藏的速度标签和进度条（用于存储数据，但不显示）
        self.speed_label = ttk.Label(speed_content_frame, text="实时速度: 0.00 KB/s")
        self.speed_label.pack_forget()  # 不显示，仅用于存储数据

        self.progress_bar = ttk.Progressbar(speed_content_frame, orient="horizontal", length=1, mode="determinate")
        self.progress_bar.pack_forget()  # 不显示

        self.size_label = ttk.Label(speed_content_frame, text="已下载: 0.00 KB / 0.00 KB")
        self.size_label.pack_forget()  # 不显示

        # 结果列表区域（占据整个宽度和更多高度）
        speed_result_frame = ttk.Frame(speed_content_frame, style='Card.TFrame')
        speed_result_frame.pack(fill=tk.BOTH, expand=True)

        # 创建标题和说明区域
        title_frame = ttk.Frame(speed_result_frame, style='Card.TFrame')
        title_frame.pack(fill=tk.X, padx=15, pady=(10, 0))

        speed_result_title = ttk.Label(title_frame, text="速度测试结果列表",
                                    font=('微软雅黑', 12, 'bold'),
                                    style='Card.TLabel')
        speed_result_title.pack(side=tk.LEFT, anchor=tk.W)

        # 添加说明标签
        speed_hint_label = ttk.Label(title_frame,
                                  text="(实时速度会在测试过程中动态更新)",
                                  font=('微软雅黑', 9),
                                  style='Card.TLabel')
        speed_hint_label.pack(side=tk.LEFT, padx=(10, 0), pady=2)

        # 创建一个新的标签来显示成功率和平均下载速度
        self.speed_stats_label = ttk.Label(speed_result_frame,
                                       text="成功率: 0.00% | 平均下载速度: 0.00 KB/s",
                                       font=('微软雅黑', 10, 'bold'),
                                       foreground='#0078D7',
                                       style='Card.TLabel')
        self.speed_stats_label.pack(anchor=tk.W, padx=15, pady=(5, 0))

        # 创建表格和滚动条
        speed_tree_frame = ttk.Frame(speed_result_frame)
        speed_tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        # 创建滚动条
        speed_tree_scroll = ttk.Scrollbar(speed_tree_frame)
        speed_tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建表格
        speed_columns = ("test_id", "status", "file_size", "time", "realtime_speed", "avg_speed", "progress")
        self.speed_result_tree = ttk.Treeview(speed_tree_frame, columns=speed_columns,
                                           show="headings",
                                           style="Custom.Treeview",
                                           height=18,  # 增加高度以显示更多行
                                           yscrollcommand=speed_tree_scroll.set)

        # 设置列标题
        self.speed_result_tree.heading("test_id", text="测试ID")
        self.speed_result_tree.heading("status", text="状态")
        self.speed_result_tree.heading("file_size", text="文件大小")
        self.speed_result_tree.heading("time", text="耗时")
        self.speed_result_tree.heading("realtime_speed", text="实时速度")
        self.speed_result_tree.heading("avg_speed", text="平均速度")
        self.speed_result_tree.heading("progress", text="进度")

        # 设置列宽
        self.speed_result_tree.column("test_id", width=60, anchor="center")
        self.speed_result_tree.column("status", width=70, anchor="center")
        self.speed_result_tree.column("file_size", width=90, anchor="center")
        self.speed_result_tree.column("time", width=80, anchor="center")
        self.speed_result_tree.column("realtime_speed", width=180, anchor="center")  # 增加宽度以显示更多信息
        self.speed_result_tree.column("avg_speed", width=120, anchor="center")
        self.speed_result_tree.column("progress", width=100, anchor="center")  # 新增进度列

        # 配置滚动条
        speed_tree_scroll.config(command=self.speed_result_tree.yview)
        self.speed_result_tree.pack(fill=tk.BOTH, expand=True)

        # 创建底部统计信息区域
        stats_summary_frame = ttk.Frame(speed_content_frame, style='Card.TFrame')
        stats_summary_frame.pack(fill=tk.X, pady=(10, 0))

        # 创建统计信息标签
        self.stats_summary_label = ttk.Label(stats_summary_frame,
                                          text="速度测试统计信息: 暂无数据",
                                          style='Card.TLabel',
                                          font=('微软雅黑', 10))
        self.stats_summary_label.pack(anchor=tk.W, padx=15, pady=10)

        # 创建隐藏的统计信息文本框（用于保持代码兼容性）
        self.speed_stats_text = tk.Text(self.window, width=1, height=1)
        self.speed_stats_text.pack_forget()  # 不显示

    # 更新速度测试统计显示
    def update_speed_stats_display(self):
        if hasattr(self, 'speed_stats') and self.speed_stats['total'] > 0:
            # 计算平均速度
            avg_speed = 0
            if len(self.speed_stats['speeds']) > 0:
                avg_speed = sum(self.speed_stats['speeds']) / len(self.speed_stats['speeds'])

            # 计算成功率
            success_rate = (self.speed_stats['success'] / self.speed_stats['total']) * 100 if self.speed_stats['total'] > 0 else 0

            # 计算总下载量（KB）
            total_downloaded = sum([speed * time for speed, time in zip(self.speed_stats['speeds'], [1] * len(self.speed_stats['speeds']))])

            # 格式化总下载量
            if total_downloaded < 1024:
                total_size_str = f"{total_downloaded:.2f} KB"
            elif total_downloaded < 1024 * 1024:
                total_size_str = f"{total_downloaded/1024:.2f} MB"
            else:
                total_size_str = f"{total_downloaded/(1024*1024):.2f} GB"

            # 构建简洁的统计信息文本（用于底部标签）
            summary_text = f"速度测试统计信息: 总测试 {self.speed_stats['total']} | 成功 {self.speed_stats['success']} | "
            summary_text += f"总下载 {total_size_str} | 平均速度 {self.format_speed(avg_speed)} | "
            summary_text += f"最大速度 {self.format_speed(self.speed_stats['max_speed'])}"

            # 更新底部统计信息标签
            self.stats_summary_label.config(text=summary_text)

            # 更新成功率和平均下载速度标签
            # 根据成功率设置不同的颜色
            if success_rate >= 90:
                success_color = '#008800'  # 绿色
            elif success_rate >= 70:
                success_color = '#0078D7'  # 蓝色
            elif success_rate >= 50:
                success_color = '#FF8C00'  # 橙色
            else:
                success_color = '#FF0000'  # 红色

            # 构建成功率和平均下载速度文本
            stats_label_text = f"成功率: {success_rate:.2f}% | 平均下载速度: {self.format_speed(avg_speed)}"

            # 如果测试已完成，添加更多信息
            if not self.speed_testing and self.speed_stats['total'] == int(self.speed_count_entry.get()):
                stats_label_text += f" | 总测试: {self.speed_stats['total']} | 成功: {self.speed_stats['success']} | 失败: {self.speed_stats['failed']}"

            # 更新标签
            self.speed_stats_label.config(text=stats_label_text, foreground=success_color)

            # 构建详细统计信息文本（用于隐藏的文本框，保持兼容性）
            stats_text = f"测试总数: {self.speed_stats['total']}\n"
            stats_text += f"成功次数: {self.speed_stats['success']}\n"
            stats_text += f"失败次数: {self.speed_stats['failed']}\n\n"
            stats_text += f"成功率: {success_rate:.2f}%\n\n"
            stats_text += f"总下载: {total_size_str}\n"
            stats_text += f"最大速度: {self.format_speed(self.speed_stats['max_speed'])}\n"
            stats_text += f"最小速度: {self.format_speed(self.speed_stats['min_speed']) if self.speed_stats['min_speed'] != float('inf') else '0.00 KB/s'}\n"
            stats_text += f"平均速度: {self.format_speed(avg_speed)}\n"
        else:
            # 无数据时的显示
            self.stats_summary_label.config(text="速度测试统计信息: 暂无数据")
            self.speed_stats_label.config(text="成功率: 0.00% | 平均下载速度: 0.00 KB/s", foreground='#0078D7')
            stats_text = "暂无测试数据"

        # 更新隐藏的统计信息文本框（保持兼容性）
        self.speed_stats_text.config(state=tk.NORMAL)
        self.speed_stats_text.delete('1.0', tk.END)
        self.speed_stats_text.insert('1.0', stats_text)
        self.speed_stats_text.config(state=tk.DISABLED)

    # 添加一个新方法来重置测试状态
    def reset_test_state(self):
        self.is_testing = False
        self.pause_testing = False
        self.pause_button.config(text="暂停测试")

    # 添加一个辅助方法来智能转换速度单位
    def format_speed(self, speed_kbps):
        """根据速度大小智能转换单位（KB/s, MB/s, GB/s）"""
        if speed_kbps < 0:
            return "0.00 KB/s"
        elif speed_kbps < 1024:  # 小于1MB/s
            return f"{speed_kbps:.2f} KB/s"
        elif speed_kbps < 1024 * 1024:  # 小于1GB/s
            return f"{speed_kbps/1024:.2f} MB/s"
        else:  # 大于等于1GB/s
            return f"{speed_kbps/(1024*1024):.2f} GB/s"

    # 下载速度测试函数
    def test_download_speed(self):
        # 检查是否已经在测试中
        if hasattr(self, 'speed_testing') and self.speed_testing:
            # 如果已经在测试中，则停止测试
            self.speed_testing = False
            self.speed_test_button.config(text="开始测试", style="Primary.TButton")
            return

        # 获取测试参数
        try:
            test_count = int(self.speed_count_entry.get())
            concurrency = int(self.speed_concurrency_entry.get())
            if test_count <= 0 or concurrency <= 0:
                messagebox.showerror("错误", "请输入大于0的测试次数和并发数量")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效的测试次数和并发数量")
            return

        # 清除之前的结果
        for item in self.speed_result_tree.get_children():
            self.speed_result_tree.delete(item)

        # 重置统计数据
        self.speed_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'total_speed': 0,
            'max_speed': 0,
            'min_speed': float('inf'),
            'speeds': []
        }

        # 重置进度显示
        self.progress_bar["value"] = 0
        self.speed_label.config(text=f"实时速度: {self.format_speed(0)}")
        self.size_label.config(text="已下载: 0.00 KB / 0.00 KB")

        # 重置底部统计信息标签
        self.stats_summary_label.config(text="速度测试统计信息: 暂无数据")

        # 重置成功率和平均下载速度标签
        self.speed_stats_label.config(text="成功率: 0.00% | 平均下载速度: 0.00 KB/s", foreground='#0078D7')

        # 更新统计显示
        self.update_speed_stats_display()

        # 设置测试状态
        self.speed_testing = True
        self.speed_test_button.config(text="停止测试", style="Warning.TButton")

        # 创建一个全局的速度更新映射表
        self.speed_update_map = {}

        # 启动全局实时速度更新函数
        self.start_global_speed_updater()

        # 创建结果队列
        import queue
        speed_result_queue = queue.Queue()

        # 定义UI更新函数
        def update_speed_ui():
            try:
                while True:
                    try:
                        result = speed_result_queue.get_nowait()
                    except queue.Empty:
                        break

                    # 处理测试结果
                    if result[1] == "成功":  # 检查状态
                        # 解包参数，现在包含实时速度
                        test_id, status, url, size_kb, time_s, realtime_speed, speed_kbps, error = result

                        # 检查是否已经有对应的树项
                        if hasattr(self, 'speed_update_map') and test_id in self.speed_update_map:
                            try:
                                # 获取已存在的树项ID
                                tree_item_id = self.speed_update_map[test_id]['tree_item_id']

                                if tree_item_id:
                                    # 为实时速度添加动态指示器
                                    formatted_speed = self.format_speed(realtime_speed)
                                    if realtime_speed > 0:
                                        # 根据速度大小选择不同的指示器
                                        if realtime_speed < 100:
                                            indicator = "▲"
                                        elif realtime_speed < 500:
                                            indicator = "▲▲"
                                        elif realtime_speed < 1000:
                                            indicator = "▲▲▲"
                                        elif realtime_speed < 5000:
                                            indicator = "▲▲▲▲"
                                        else:
                                            indicator = "▲▲▲▲▲"

                                        # 添加指示器到速度显示
                                        realtime_display = f"{formatted_speed} {indicator}"
                                    else:
                                        realtime_display = formatted_speed

                                    # 进度为100%（已完成）
                                    progress_display = "100% ▓▓▓▓▓▓▓▓▓▓"

                                    # 更新树项
                                    self.speed_result_tree.item(tree_item_id, values=(
                                        test_id,
                                        status,
                                        f"{size_kb:.2f} KB",
                                        f"{time_s:.2f} 秒",
                                        realtime_display,  # 使用带指示器的实时速度显示
                                        self.format_speed(speed_kbps),  # 平均速度，智能单位转换
                                        progress_display  # 进度显示
                                    ))

                                    # 确保滚动到当前测试项
                                    self.speed_result_tree.see(tree_item_id)

                                    # 打印调试信息
                                    print(f"已更新测试ID {test_id} 的最终结果")
                                else:
                                    print(f"警告: 测试ID {test_id} 的树项ID为空")
                            except Exception as e:
                                print(f"更新树项错误: {str(e)}")
                        else:
                            print(f"警告: 未找到测试ID {test_id} 的速度更新映射")
                    else:
                        try:
                            test_id, status, url, size_kb, time_s, realtime_speed, speed_kbps, error = result

                            # 检查是否已经有对应的树项
                            if hasattr(self, 'speed_update_map') and test_id in self.speed_update_map:
                                try:
                                    # 获取已存在的树项ID
                                    tree_item_id = self.speed_update_map[test_id]['tree_item_id']

                                    if tree_item_id:
                                        # 更新树项为失败状态
                                        self.speed_result_tree.item(tree_item_id, values=(
                                            test_id,
                                            status,
                                            "N/A",
                                            "N/A",
                                            "0.00 KB/s ✖",  # 显示0速度并添加失败标记
                                            error or "连接失败",  # 错误信息显示在平均速度列
                                            "0%"  # 进度为0%
                                        ))

                                        # 确保滚动到当前测试项
                                        self.speed_result_tree.see(tree_item_id)

                                        # 打印调试信息
                                        print(f"已更新测试ID {test_id} 的失败结果")
                                    else:
                                        # 如果没有树项ID，创建一个新的
                                        self.speed_result_tree.insert('', 'end', values=(
                                            test_id,
                                            status,
                                            "N/A",
                                            "N/A",
                                            "0.00 KB/s ✖",  # 显示0速度并添加失败标记
                                            error or "连接失败",  # 错误信息显示在平均速度列
                                            "0%"  # 进度为0%
                                        ))
                                except Exception as e:
                                    print(f"更新失败树项错误: {str(e)}")
                            else:
                                # 如果没有映射，创建一个新的树项
                                self.speed_result_tree.insert('', 'end', values=(
                                    test_id,
                                    status,
                                    "N/A",
                                    "N/A",
                                    "0.00 KB/s ✖",  # 显示0速度并添加失败标记
                                    error or "连接失败",  # 错误信息显示在平均速度列
                                    "0%"  # 进度为0%
                                ))
                        except Exception as e:
                            print(f"处理失败结果错误: {str(e)}")
                            # 尝试使用更安全的方式插入
                            try:
                                error_msg = str(result[-1]) if len(result) > 7 else "未知错误"
                                self.speed_result_tree.insert('', 'end', values=(
                                    result[0] if len(result) > 0 else 0,
                                    "失败",
                                    "N/A",
                                    "N/A",
                                    "0.00 KB/s ✖",  # 显示0速度并添加失败标记
                                    error_msg,  # 错误信息显示在平均速度列
                                    "0%"  # 进度为0%
                                ))
                            except Exception as ex:
                                print(f"备用插入失败: {str(ex)}")
                                pass

                    # 更新统计信息
                    self.update_speed_stats_display()

                    # 标记任务完成
                    speed_result_queue.task_done()
                    # 确保UI更新
                    self.window.update_idletasks()
            except Exception as e:
                print(f"更新UI错误: {str(e)}")

            # 如果测试仍在进行，继续更新UI
            if self.speed_testing:
                self.window.after(100, update_speed_ui)

        # 创建futures列表，用于存储所有测试任务
        futures = []

        # 启动UI更新
        self.window.after(100, update_speed_ui)

        # 测试单个URL的下载速度
        def test_single_download(test_id, url):
            proxy_url = self.proxy_entry.get().strip()
            proxy = {
                'http': proxy_url,
                'https': proxy_url
            } if proxy_url else None

            start_time = time.time()
            try:
                response = requests.get(url, proxies=proxy, timeout=15, stream=True)

                # 获取文件总大小（如果服务器提供）
                total_size = int(response.headers.get('content-length', 0))
                total_size_kb = total_size / 1024 if total_size > 0 else 0

                # 读取内容计算大小
                content_size = 0
                last_update_time = time.time()
                last_content_size = 0
                current_speed = 0

                # 创建一个队列用于实时更新UI
                import queue
                speed_update_queue = queue.Queue()

                # 创建一个变量存储当前测试项的ID
                tree_item_id = None

                # 添加一个方法来设置树项ID，供外部调用
                def set_tree_item_id(item_id):
                    nonlocal tree_item_id
                    tree_item_id = item_id

                # 创建一个预先的树项，这样我们可以立即开始更新实时速度
                # 初始进度为0%
                progress_display = "0%"

                # 预先在树视图中插入一个项目
                item_id = self.speed_result_tree.insert('', 'end', values=(
                    test_id,
                    "下载中...",
                    f"0.00 KB",
                    "0.00 秒",
                    "0.00 KB/s",  # 初始实时速度
                    "0.00 KB/s",  # 初始平均速度
                    progress_display  # 初始进度
                ))

                # 确保滚动到当前测试项
                self.speed_result_tree.see(item_id)
                self.window.update_idletasks()

                # 设置树项ID
                tree_item_id = item_id

                # 将当前测试的信息存储到全局映射表中，包括已创建的树项ID
                self.speed_update_map[test_id] = {
                    'queue': speed_update_queue,
                    'tree_item_id': tree_item_id,  # 直接设置树项ID
                    'total_size_kb': total_size_kb,
                    'last_speed': 0,
                    'last_progress': 0,
                    'last_update_time': time.time()
                }

                # 打印调试信息
                print(f"已注册测试ID {test_id} 的速度更新队列，树项ID: {tree_item_id}")

                # 强制更新UI
                self.window.update_idletasks()

                # 记录最后一次测量的实时速度值，用于返回结果
                last_realtime_speed = 0
                # 记录速度历史，用于计算平均速度
                speed_history = []
                # 记录下载开始时间，用于计算平均速度
                download_start_time = time.time()

                for chunk in response.iter_content(chunk_size=8192):
                    if not self.speed_testing:
                        # 如果测试被停止，则中断下载
                        raise Exception("测试被用户中断")

                    if chunk:
                        chunk_size = len(chunk)
                        content_size += chunk_size

                        # 计算实时速度（每0.1秒更新一次，大幅提高更新频率）
                        current_time = time.time()
                        time_diff = current_time - last_update_time

                        if time_diff >= 0.1:  # 每0.1秒更新一次速度，提高更新频率
                            size_diff = content_size - last_content_size  # 这段时间内下载的字节数
                            current_speed = (size_diff / 1024) / time_diff  # 当前速度 KB/s

                            # 应用平滑处理，避免速度波动过大
                            if len(speed_history) > 0:
                                # 使用简单的移动平均来平滑速度显示
                                smoothed_speed = (current_speed + speed_history[-1]) / 2
                                current_speed = smoothed_speed

                            last_realtime_speed = current_speed  # 保存最后一次测量的实时速度

                            # 记录当前速度到历史记录
                            speed_history.append(current_speed)

                            # 限制历史记录长度，只保留最近的速度值
                            if len(speed_history) > 10:
                                speed_history = speed_history[-10:]

                            # 计算平均速度（使用所有历史速度的平均值）
                            avg_speed = sum(speed_history) / len(speed_history)

                            # 计算下载进度百分比
                            progress_percent = (content_size / total_size * 100) if total_size > 0 else 0

                            # 将当前速度放入队列，由UI线程处理
                            speed_update_queue.put((content_size, current_speed, progress_percent, avg_speed))

                            # 更新基准值
                            last_update_time = current_time
                            last_content_size = content_size

                # 计算总体平均速度
                elapsed_time = time.time() - start_time
                file_size_kb = content_size / 1024  # KB
                speed_kbps = file_size_kb / elapsed_time if elapsed_time > 0 else 0  # KB/s

                # 返回结果中添加最后一次测量的实时速度
                return test_id, "成功", url, file_size_kb, elapsed_time, last_realtime_speed, speed_kbps, None
            except requests.exceptions.RequestException as e:
                return test_id, "失败", url, 0, 0, 0, 0, str(e)
            except Exception as e:
                return test_id, "失败", url, 0, 0, 0, 0, str(e)

        # 运行测试的线程函数
        def run_speed_tests():
            try:
                # 测试文件URL列表
                test_urls = [
                    "https://speed.cloudflare.com/__down?bytes=10485760",  # 10MB文件
                    "https://speed.cloudflare.com/__down?bytes=10485760",  # 10MB文件
                    "https://speed.cloudflare.com/__down?bytes=10485760"   # 10MB文件
                ]

                # 创建线程池
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    # 使用nonlocal声明，使futures在update_speed_ui函数中可见
                    nonlocal futures
                    futures = []

                    # 提交所有测试任务
                    for i in range(test_count):
                        # 轮流使用不同大小的测试文件
                        url = test_urls[i % len(test_urls)]
                        future = executor.submit(test_single_download, i+1, url)
                        # 存储future对象以便后续引用
                        futures.append(future)

                    # 处理结果
                    for future in futures:
                        try:
                            # 获取测试结果
                            result = future.result()
                            # 将结果放入队列，由UI线程处理
                            speed_result_queue.put(result)

                            # 解包结果用于统计
                            test_id, status, url, size_kb, time_s, realtime_speed, speed_kbps, error = result

                            # 更新统计数据
                            self.speed_stats['total'] += 1
                            if status == "成功":
                                self.speed_stats['success'] += 1
                                self.speed_stats['total_speed'] += speed_kbps
                                self.speed_stats['speeds'].append(speed_kbps)

                                # 更新最大/最小速度
                                if speed_kbps > self.speed_stats['max_speed']:
                                    self.speed_stats['max_speed'] = speed_kbps
                                if speed_kbps < self.speed_stats['min_speed']:
                                    self.speed_stats['min_speed'] = speed_kbps
                            else:
                                self.speed_stats['failed'] += 1
                        except Exception as e:
                            speed_result_queue.put((0, "失败", "", 0, 0, 0, 0, f"执行错误: {str(e)}"))
            except Exception as e:
                print(f"下载速度测试错误: {str(e)}")
            finally:
                # 测试完成后重置状态
                self.speed_testing = False
                self.window.after(0, lambda: self.speed_test_button.config(text="开始测试", style="Primary.TButton"))
                # 确保最后一次更新UI
                self.window.after(0, self.update_speed_stats_display)

        # 启动测试线程
        speed_thread = threading.Thread(target=run_speed_tests)
        speed_thread.daemon = True
        speed_thread.start()

    # 启动全局实时速度更新函数
    def start_global_speed_updater(self):
        """启动一个全局的实时速度更新函数，处理所有测试项的速度更新"""
        def update_all_speeds():
            if not hasattr(self, 'speed_update_map'):
                return

            # 打印调试信息
            if self.speed_testing:
                print(f"全局速度更新: 当前有 {len(self.speed_update_map)} 个测试项")

            # 处理每个测试项的速度更新
            for test_id, test_info in list(self.speed_update_map.items()):
                queue = test_info.get('queue')
                tree_item_id = test_info.get('tree_item_id')

                if not queue or not tree_item_id:
                    continue

                # 检查树项是否存在
                try:
                    current_values = self.speed_result_tree.item(tree_item_id, 'values')
                    if not current_values:
                        continue
                except Exception:
                    continue

                # 处理队列中的所有更新
                updates_processed = 0
                max_updates_per_item = 3  # 每个测试项每次处理的最大更新数

                while not queue.empty() and updates_processed < max_updates_per_item:
                    try:
                        # 获取最新的速度更新
                        current_size, current_speed, progress_percent, avg_speed = queue.get_nowait()
                        updates_processed += 1

                        # 更新测试信息
                        test_info['last_speed'] = current_speed
                        test_info['last_progress'] = progress_percent
                        test_info['last_update_time'] = time.time()

                        # 创建新的值元组
                        new_values = list(current_values)
                        while len(new_values) < 7:
                            new_values.append("")

                        # 使用智能单位转换显示速度
                        formatted_speed = self.format_speed(current_speed)
                        formatted_avg = self.format_speed(avg_speed)

                        # 为实时速度添加动态指示器和动画效果
                        if current_speed > 0:
                            # 根据速度大小选择不同的指示器和颜色
                            if current_speed < 100:
                                indicator = "▲"
                                speed_color = "慢"
                            elif current_speed < 500:
                                indicator = "▲▲"
                                speed_color = "中"
                            elif current_speed < 1000:
                                indicator = "▲▲▲"
                                speed_color = "快"
                            elif current_speed < 5000:
                                indicator = "▲▲▲▲"
                                speed_color = "很快"
                            else:
                                indicator = "▲▲▲▲▲"
                                speed_color = "超快"

                            # 添加动画效果
                            animation_frame = int((time.time() * 10) % 3)
                            if animation_frame == 0:
                                animation = "⟳"
                            elif animation_frame == 1:
                                animation = "⟲"
                            else:
                                animation = "↻"

                            # 更新实时速度显示
                            new_values[4] = f"{formatted_speed} {indicator} [{speed_color}] {animation}"
                        else:
                            new_values[4] = formatted_speed

                        # 更新平均速度
                        new_values[5] = formatted_avg

                        # 更新进度列，添加进度条效果
                        progress_bar = ""
                        bar_length = int(progress_percent / 10)
                        progress_bar = "▓" * bar_length + "░" * (10 - bar_length)
                        new_values[6] = f"{progress_percent:.1f}% {progress_bar}"

                        # 更新树项
                        self.speed_result_tree.item(tree_item_id, values=tuple(new_values))

                        # 确保滚动到当前测试项
                        self.speed_result_tree.see(tree_item_id)

                        # 标记任务完成
                        queue.task_done()
                    except queue.Empty:
                        break
                    except Exception as e:
                        print(f"处理速度更新错误: {str(e)}")
                        try:
                            queue.task_done()
                        except:
                            pass

            # 无论测试是否在进行，都继续更新一段时间
            # 这确保了即使测试结束，最后的速度更新也能显示出来
            self.window.after(20, update_all_speeds)

        # 启动更新
        self.window.after(10, update_all_speeds)

    # 更新速度测试统计显示
    def update_speed_stats_display(self):
        if not hasattr(self, 'speed_stats'):
            return

        # 清空文本框
        self.speed_stats_text.config(state=tk.NORMAL)
        self.speed_stats_text.delete("1.0", tk.END)

        if self.speed_stats['total'] > 0:
            success_rate = (self.speed_stats['success'] / self.speed_stats['total']) * 100
            failed_rate = (self.speed_stats['failed'] / self.speed_stats['total']) * 100

            # 计算平均速度
            avg_speed = 0
            if self.speed_stats['success'] > 0:
                avg_speed = self.speed_stats['total_speed'] / self.speed_stats['success']

            # 计算标准差
            std_dev = 0
            if len(self.speed_stats['speeds']) > 1:
                # 使用Python内置方法计算标准差，避免依赖numpy
                speeds = self.speed_stats['speeds']
                mean = sum(speeds) / len(speeds)
                variance = sum((x - mean) ** 2 for x in speeds) / len(speeds)
                std_dev = variance ** 0.5

            # 准备统计信息文本
            stats_text = f"📊 测试统计信息\n"
            stats_text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            stats_text += f"测试总数: {self.speed_stats['total']}\n"
            stats_text += f"成功次数: {self.speed_stats['success']}\n"
            stats_text += f"失败次数: {self.speed_stats['failed']}\n"
            stats_text += f"成功率: {success_rate:.1f}%\n"
            stats_text += f"失败率: {failed_rate:.1f}%\n\n"

            if self.speed_stats['success'] > 0:
                stats_text += f"📈 速度分析\n"
                stats_text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                stats_text += f"平均速度: {self.format_speed(avg_speed)}\n"
                stats_text += f"最大速度: {self.format_speed(self.speed_stats['max_speed'])}\n"
                stats_text += f"最小速度: {self.format_speed(self.speed_stats['min_speed'])}\n"
                stats_text += f"速度波动: {self.format_speed(std_dev)}\n"

                # 添加实时速度与平均速度的对比信息
                # 从速度标签中提取当前速度值
                speed_text = self.speed_label.cget("text").split(":")[1].strip()
                # 提取数值部分
                try:
                    if "KB/s" in speed_text:
                        current_speed = float(speed_text.split(" KB/s")[0])
                    elif "MB/s" in speed_text:
                        current_speed = float(speed_text.split(" MB/s")[0]) * 1024  # 转换为KB/s进行比较
                    elif "GB/s" in speed_text:
                        current_speed = float(speed_text.split(" GB/s")[0]) * 1024 * 1024  # 转换为KB/s进行比较
                    else:
                        current_speed = 0
                except:
                    current_speed = 0

                if current_speed > 0:
                    speed_diff = ((current_speed - avg_speed) / avg_speed) * 100 if avg_speed > 0 else 0
                    stats_text += f"\n当前实时速度: {speed_text}\n"
                    if speed_diff > 0:
                        stats_text += f"较平均速度提升: {speed_diff:.1f}%\n"
                    elif speed_diff < 0:
                        stats_text += f"较平均速度下降: {abs(speed_diff):.1f}%\n"
                    else:
                        stats_text += f"与平均速度持平\n"

                # 添加速度评估 - 根据KB/s评估
                if avg_speed < 50:
                    speed_rating = "很慢 ⚠️"
                elif avg_speed < 200:
                    speed_rating = "较慢 ⚠️"
                elif avg_speed < 500:
                    speed_rating = "一般 ⚡"
                elif avg_speed < 1000:
                    speed_rating = "较快 ⚡⚡"
                elif avg_speed < 5000:  # 5MB/s
                    speed_rating = "很快 ⚡⚡⚡"
                elif avg_speed < 20000:  # 20MB/s
                    speed_rating = "超快 ⚡⚡⚡⚡"
                else:
                    speed_rating = "极速 ⚡⚡⚡⚡⚡"

                stats_text += f"速度评估: {speed_rating}\n"

                # 添加稳定性评估
                if self.speed_stats['success'] > 1:
                    stability_ratio = std_dev / avg_speed if avg_speed > 0 else 0
                    if stability_ratio < 0.1:
                        stability = "非常稳定 ✅✅"
                    elif stability_ratio < 0.3:
                        stability = "较为稳定 ✅"
                    elif stability_ratio < 0.5:
                        stability = "一般 ⚠️"
                    else:
                        stability = "不稳定 ⚠️⚠️"

                    stats_text += f"连接稳定性: {stability}\n"
        else:
            stats_text = "暂无测试数据\n\n请点击'开始测试'按钮开始下载速度测试"

        # 更新文本框
        self.speed_stats_text.insert("1.0", stats_text)
        self.speed_stats_text.config(state=tk.DISABLED)

if __name__ == '__main__':
    app = ProxySpeedTester()
    app.window.mainloop()