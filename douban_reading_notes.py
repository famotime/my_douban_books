"""获取豆瓣网上某本书的摘录笔记（无须登录）"""
import pathlib
import requests
from lxml import etree


def login_douban(user, password):
    """登录豆瓣"""
    login_url = 'https://accounts.douban.com/j/mobile/login/basic'

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36', 'Referer': 'https://accounts.douban.com/passport/login?source=main'}

    # 传递用户名和密码
    data = {'name': user,
            'password': password,
            'remember': 'false'}
    try:
        r = s.post(login_url, headers=headers, data=data)
        r.raise_for_status()
    except Exception as e:
        print(f'登录请求失败：{e}')
        return 0
    # 打印请求结果
    print(r.text)
    return 1


def url_constructor(bookid):
    urls = []
    nums = [i*20 for i in range(9)]
    for num in nums:
        url = f'https://book.douban.com/subject/{bookid}/blockquotes?sort=page_num&start={num}'
        urls.append(url)
    return urls


def get_reading_notes(urls, headers):
    notes = ''
    title = None
    for url in urls:
        content = s.get(url, headers=headers).text
        tree = etree.HTML(content)
        if not title:
            title = tree.xpath('//h1')[0].text
            notes += '# ' + title + '\n\n'
        nodes = tree.xpath('//figure')
        for node in nodes:
            notes += node.text.strip('( \n') + '\n\n'

    with open(data_folder / f'{title}.md', 'w', encoding='utf-8') as f:
        f.write(notes)
    print(f'已保存到文件：{title}.md，请查看。')

    return title, notes


if __name__ == "__main__":
    bookid = '26838557'
    data_folder = pathlib.Path('my_douban_data')

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}

    s = requests.Session()

    # user = 'XXX'
    # password = 'XXX'
    # login_douban(user, password)

    urls = url_constructor(bookid)
    title, notes = get_reading_notes(urls, headers)
