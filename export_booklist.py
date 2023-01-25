"""根据excel表书单，提取豆瓣读书记录（已读、在读、想读）中已输出内容，并保存为markdown文件"""
import pathlib
import datetime
import re
import pandas as pd


def extract_reading_records(data_folder):
    """抽取豆瓣读书记录中的书籍信息"""
    today = datetime.date.today()
    # 合并“想读、在读、已读”读书记录
    md_files = [i for i in data_folder.glob(f'*.md') if re.search(r'想读|在读|已读', i.stem) and 'abs' not in i.stem]
    content = ''
    for md_file in md_files:
        with open(md_file, encoding='utf-8') as f:
            content += f.read()

    with open(data_folder / f'豆瓣读书记录{today}.md', 'w', encoding='utf-8') as f:
        f.write(content)

    # 将每本书的记录提取出来
    books = {}
    with open(data_folder / f'豆瓣读书记录{today}.md', encoding='utf-8') as f:
        last_title = block = ''
        for line in f:
            if line.startswith('### '):
                if last_title:
                    books[last_title] = block
                block = line
                last_title = re.search(r'\[(.*?)\]', line).group(1)
            elif line.startswith('# '):
                pass
            else:
                block += line

    # i = 1
    # for k, v in books.items():
    #     if i < 3:
    #         print(k, v, sep='\n')
    #         i += 1

    return books


def export_booklist(df_books, douban_books):
    """根据书单信息，将豆瓣读书记录中的书籍信息分类组合输出markdown文件"""
    for category in df_books['分类'].unique():
        titles = df_books.query("分类 == @category")['备注']    # 备注列为修正后的书名
        content = f'## {category}\n'
        count = 0
        for title in titles:
            if title in douban_books:
                content += douban_books[title]
                count += 1
            elif title.replace(' : ', ': ') in douban_books:
                content += douban_books[title.replace(' : ', ': ')]
                count += 1
            else:
                print(f"未找到《{title}》。")

        with open(data_folder / f'书单：{category}.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已输出《书单：{category}.md》，包含{count}本书。")


if "__main__" == __name__:
    data_folder = pathlib.Path.cwd() / 'my_douban_data'
    book_list = data_folder / '用200本书构建知识体系.xlsx'      # 含多个书单，用“分类”字段区分

    df_books = pd.read_excel(book_list)
    douban_books = extract_reading_records(data_folder)
    export_booklist(df_books, douban_books)
