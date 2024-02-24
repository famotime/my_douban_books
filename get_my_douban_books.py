"""批量获取我的豆瓣读书清单及书评（已读、在读、想读），生成Markdown文件"""
import json
import pathlib
import random
import re
import time
from datetime import date

import requests
from lxml import etree


def get_account_info(account_file):
    """获取豆瓣账号信息"""
    with open(account_file, encoding='utf-8') as f:
        content = json.load(f)
        user = content['douban']['user']
        password = content['douban']['password']
    return user, password


def login_douban(s, name, password):
    """登录豆瓣"""
    login_url = 'https://accounts.douban.com/j/mobile/login/basic'
    headers = {'user-agent': 'Mozilla/5.0', 'Referer': 'https://accounts.douban.com/passport/login?source=main'}
    data = {'name': name,
            'password': password,
            'remember': 'false'}
    try:
        r = s.post(login_url, headers=headers, data=data)
        r.raise_for_status()
    except Exception as e:
        print(e)
        return 0
    # 打印请求结果
    print(r.text)
    return 1


def download_webpage(url, html_file, s):
    """下载网页到本地html文件"""
    content = s.get(url, headers=headers).text
    # print(content)
    with open(html_file, 'w', encoding='utf-8') as f:
        if content:
            f.write(content)
    # print(f"已保存{html_file.absolute()}……")


def get_book_amount(user_id, category, session):
    """获取我的豆瓣分类（已读、想读、在读）书本数量"""
    num = 0
    if category == '已读':
        url = f"https://book.douban.com/people/{user_id}/collect?start={num}&sort=time&rating=all&filter=all&mode=grid"   # 已读
    elif category == '在读':
        url = f"https://book.douban.com/people/{user_id}/do?start={num}&sort=time&rating=all&filter=all&mode=grid"    # 在读
    elif category == '想读':
        url = f"https://book.douban.com/people/{user_id}/wish?start={num}&sort=time&rating=all&filter=all&mode=grid"   # 想读
    content = session.get(url, headers=headers).text
    html = etree.HTML(content)
    book_amount = int(re.search(r'\d+', html.xpath('//h1')[0].text).group())
    print(f"发现“{category}”书籍{book_amount}本，正在下载网页文件……")
    return book_amount


def save_webpages(user_id, category, book_amount, session):
    """保存我的豆瓣分类（已读、想读、在读）网页到本地html文件"""
    html_folder = pathlib.Path(data_folder / f"html_{category}")
    if not html_folder.exists():
        html_folder.mkdir()

    for num in range(0, (book_amount//15)*15+1, 15):
        if category == '已读':
            url = f"https://book.douban.com/people/{user_id}/collect?start={num}&sort=time&rating=all&filter=all&mode=grid"   # 已读
        elif category == '在读':
            url = f"https://book.douban.com/people/{user_id}/do?start={num}&sort=time&rating=all&filter=all&mode=grid"    # 在读
        elif category == '想读':
            url = f"https://book.douban.com/people/{user_id}/wish?start={num}&sort=time&rating=all&filter=all&mode=grid"   # 想读

        html_file = html_folder / f'content_{num:03.0f}.html'

        download_webpage(url, html_file, session)
        print(f"已下{num+1}/{(book_amount//15)*15}：{url}……")
        time.sleep(random.randint(1, 3))
    print(f"已完成{book_amount//15 + 1}个html文件下载，并保存到目录：{html_folder.absolute()}。")
    return html_folder


def parse_html_file(html_file, category):
    """解析本地html文件，生成markdown文本"""
    with open(html_file, encoding='utf-8') as f:
        content = f.read()
    html = etree.HTML(content)
    nodes = html.xpath('//li[@class="subject-item"]')

    text = ''
    for node in nodes:
        title = ''.join([x.strip() for x in node.xpath('.//a[@title]//text()')])
        print(f"正在处理书籍《{title}》的信息……")
        link, stars, pub, tags, comment = [''] * 5
        try:
            link = node.xpath('.//a[@title]/@href')[0]
            pub = node.xpath('.//div[@class="pub"]')[0].text.strip()
            tags = '；'.join(node.xpath('.//div[@class="short-note"]//span//text()')).replace('\n      ', ' ')
            # stars = ':star:' * int(node.xpath('.//span[starts-with(@class,"rating")]/@class')[0].strip('rating-t'))
            stars = '<font color=#FF0000 size=6>' + '★' * int(node.xpath('.//span[starts-with(@class,"rating")]/@class')[0].strip('rating-t')) + '</font>'
            comment = node.xpath('.//p[@class="comment comment-item"]')[0].text.strip()
        except Exception as e:
            # print(e)
            pass

        # 下载图片到本地
        img_folder = pathlib.Path(data_folder / f'html_{category}')
        if not img_folder.exists():
            img_folder.mkdir()
        img_url = node.xpath('.//div[@class="pic"]//img/@src')[0]
        img_name = img_url.split('/')[-1]
        if not (img_folder / img_name).exists():
            img_path = download_image(img_url, img_folder)
            print(f"已下载{img_path.absolute()}……")
        else:
            img_path = img_folder / img_name

        # print(title, stars, link, pub, tags, img, comment, sep='\n')
        # print('\n')

        text += f"### [{title}]({link}) {stars}\n> {pub}\n> {tags}\n\n![]({img_path.relative_to(data_folder)})\n{comment}\n\n"
    return text


def download_image(img_url, folder):
    """下载图片到本地"""
    img = requests.get(img_url, headers=headers).content
    img_name = img_url.split('/')[-1]
    img_path = folder / img_name
    with open(img_path, 'wb') as f:
        f.write(img)
    return img_path


def make_mdfile(html_folder, category, book_amount):
    """创建分类读书记录的markdown文件"""
    md_file = pathlib.Path(data_folder / f'豆瓣读书记录_{category}{book_amount}_{date.today()}.md')
    html_files = html_folder.glob('content*.html')
    text = f'# {md_file.stem}\n'
    for html_file in html_files:
        print(f"{'-'*25}正在解析{html_file.absolute()}{'-'*25}")
        text += parse_html_file(html_file, category)
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"已生成文件{md_file.absolute()}。")


def save_progress(book_amounts):
    """保存进度（书籍数量）"""
    with open(data_folder / "progress.json", 'w', encoding='utf-8') as f:
        progress = {key: value for key, value in zip(['想读', '在读', '已读'], book_amounts)}
        json.dump(progress, f, ensure_ascii=False)


def load_progress(progress_file):
    """加载进度（书籍数量）"""
    try:
        with open(progress_file, encoding='utf-8') as f:
            progress = json.load(f)
        return progress
    except Exception as e:
        print("未发现历史下载记录。")
        print(e)
        return None


if __name__ == '__main__':
    account_file = pathlib.Path("../../account/web_accounts.json")
    user_id = 2180307
    data_folder = pathlib.Path('./my_douban_data')
    progress_file = data_folder / 'progress.json'
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}

    # 登录不成功但仍须执行，否则后续下载网页不成功
    user, password = get_account_info(account_file)
    s = requests.Session()
    login_douban(s, user, password)

    # 读取上次处理记录
    progress = load_progress(progress_file)

    # 下载豆瓣读书记录html文件到本地
    book_amounts = []
    for category in ['想读', '在读', '已读']:
        book_amount = get_book_amount(user_id, category, s)
        book_amounts.append(book_amount)
        if not progress or book_amount != progress[category]:
            save_webpages(user_id, category, book_amount, s)
        else:
            print(f"{category}书籍相比上次查询结果无变化，跳过未处理！")
    save_progress(book_amounts)     # 保存进度

    # 从html文件中解析信息并生成读书记录markdown文件
    categories = ['想读', '在读', '已读']
    html_folders = [pathlib.Path(data_folder / f"html_{i}") for i in categories]
    for html_folder, category, book_amount in zip(html_folders, categories, book_amounts):
        make_mdfile(html_folder, category, book_amount)
