"""Markdown文件批量处理"""
import pathlib
import re


def md_abs_img_path(md_file):
    """将markdown文件中的图片相对路径改为绝对路径"""
    with open(md_file, encoding='utf-8') as f:
        content = f.read()
    if '![' in content:
        content = re.sub(r'!\[\]\((.*?)\)', lambda x: f"![]({md_file.absolute().parent / x.group(1)})", content)
        md_file_abs = md_file.with_name(md_file.stem + '_abs.md')
        with open(md_file_abs, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已保存文件{md_file_abs.absolute()}。")
    else:
        print(f"在{md_file.absolute()}未发现图片链接，跳过……")


def replace_star_mark(md_file):
    """将emoji表示的星号转换为html格式"""
    md_file_new = md_file.with_name(md_file.stem + "_new.md")
    with open(md_file, encoding='utf-8') as f1:
        content = f1.read()
        if ':star:' in content:
            with open(md_file_new, 'w', encoding='utf-8') as f2:
                content_new = content.replace(':star:', '★')
                content_new = re.sub(r'(★+)', r'<font color=#FF0000 size=6> \1</font>', content_new)
                f2.write(content_new)
                print(f"已保存{md_file_new}……")


def copy_md_file(md_file):
    """将md文件及内容中包含的图片文件拷贝到指定目录"""
    dest_folder = md_file.parent / "export"
    dest_folder.mkdir(exist_ok=True)

    with open(md_file, encoding='utf-8') as f:
        content = f.read()
    img_list = re.findall(r'!\[.*?\]\((.*?)\)', content)

    (dest_folder / md_file.name).write_text(content, encoding='utf-8')
    for img in img_list:
        data = (md_file.parent / img).read_bytes()
        img_folder = dest_folder / img
        img_folder.parent.mkdir(exist_ok=True)
        img_folder.write_bytes(data)


if "__main__" == __name__:
    data_folder = pathlib.Path(r'./my_douban_data')

    # 将markdown文件中的图片相对路径改为绝对路径
    for md_file in [x for x in data_folder.glob('*.md') if '_abs' not in x.stem]:
        md_abs_img_path(md_file)

    # for md_file in [x for x in data_folder.glob('*.md')]:
    #     replace_star_mark(md_file)

    # md_file = pathlib.Path(r"c:\QMDownload\Python Programming\Python_Work\Web Spider\豆瓣\逻辑学、统计学、数学、物理学、复杂科学、科学哲学.md")
    # copy_md_file(md_file)
