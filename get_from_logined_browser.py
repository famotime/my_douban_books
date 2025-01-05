"""
使用Selenium控制已经打开的Edge浏览器
手工登录网站
从剪贴板中读取网址（一行一个），并下载为html文件
"""

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import time
import json
import pyperclip
from pathlib import Path
import time

def attach_to_browser():
    """连接到已打开的Edge浏览器"""
    try:
        print("正在尝试连接到Edge浏览器...")
        options = webdriver.EdgeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        browser = webdriver.Edge(options=options)
        print("成功连接到Edge浏览器！")
        return browser
    except Exception as e:
        print(f"连接浏览器失败: {e}")

def create_valid_filename(url, html_content):
    """从URL和HTML内容创建有效的文件名"""
    try:
        html = etree.HTML(html_content)

        # 首先尝试获取 title
        title = html.xpath('//title/text()')

        if title and title[0].strip():
            title = title[0].strip()
        else:
            # 如果没有 title，依次尝试 h1 到 h6 标签
            for h_level in range(1, 7):
                heading = html.xpath(f'//h{h_level}/text()')
                if heading and heading[0].strip():
                    title = heading[0].strip()
                    break
            else:  # 如果所有标题标签都没找到
                parsed = urlparse(url)
                title = parsed.netloc + parsed.path

        # 移除非法字符
        title = re.sub(r'[<>:"/\\|?*\n\r]', '_', title)
        # 确保文件名不会太长
        if len(title) > 200:
            title = title[:200]
        return title + '.html'
    except Exception as e:
        # 如果解析出错，回退到使用URL作为文件名
        parsed = urlparse(url)
        filename = parsed.netloc + parsed.path
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 200:
            filename = filename[:200]
        return filename + '.html'

def save_webpage(browser, save_dir):
    """保存当前网页内容"""
    url = browser.current_url
    filename = create_valid_filename(url, browser.page_source)
    save_path = save_dir / filename
    with save_path.open('w', encoding='utf-8') as f:
        f.write(browser.page_source)
    return save_path

def process_clipboard_urls(save_dir: Path):
    """处理剪贴板中的URL（支持多行）"""
    browser = attach_to_browser()
    # 从剪贴板获取内容，处理不同的换行符
    clipboard_content = pyperclip.paste().strip()
    # 先将所有的 \r\n 替换为 \n，再分割
    urls = clipboard_content.replace('\r\n', '\n').split('\n')

    if not any(urls):
        print("剪贴板为空，请重新复制链接")
        return

    print(f"检测到 {len(urls)} 个链接")

    # 处理每个URL
    for i, url in enumerate(urls, 1):
        url = url.strip()
        if not url:
            continue
        try:
            print(f"\n正在处理: [{i}/{len(urls)}] {url}")
            browser.get(url)
            time.sleep(2)  # 等待页面加载
            save_path = save_webpage(browser, save_dir)
            print(f"已保存网页到：{save_path}")
        except Exception as e:
            print(f"保存页面时出错：{e}")

    print("\n本批URL处理完成")


if __name__ == "__main__":
    # 设置保存目录
    save_dir = Path(r"D:\Python_Work\Wiznotes_tools\wiznotes\兴趣爱好\读书观影\新书单")
    save_dir.mkdir(exist_ok=True)

    # 启动Edge浏览器的调试模式命令：
    # msedge.exe --remote-debugging-port=9222
    print("请确保已经用调试模式启动Edge浏览器并手动登录豆瓣")
    process_clipboard_urls(save_dir)
