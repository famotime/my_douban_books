"""Markdown文件批量处理"""
import pathlib


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


if "__main__" == __name__:
    data_folder = pathlib.Path(r'./my_douban_data')

    # 将markdown文件中的图片相对路径改为绝对路径
    for md_file in [x for x in data_folder.glob('*.md') if not '_abs' in x.stem]:
        md_abs_img_path(md_file)
