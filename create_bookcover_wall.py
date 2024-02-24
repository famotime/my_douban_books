"""基于读书记录Markdown文件，生成书籍封面图片墙（书籍封面缩略图拼接）"""
import re
import pathlib
from PIL import Image, ImageDraw, ImageFont


def get_images_and_stars(records, sort_flag=True):
    """从Markdown文件获取图片链接和评分信息"""
    with open(records, encoding='utf-8') as f:
        content = f.read()

    img_links = [records.parent / i for i in re.findall("!\[\]\((.*?)\)", content)]
    stars = re.findall(r'>(.*?)</font>', content)

    if sort_flag:
        combined = sorted(zip(img_links, stars), key=lambda x: len(x[1]), reverse=True)
        img_links = [i[0] for i in combined]
        stars = [i[1] for i in combined]

    return img_links, stars


def combine_pics(img_links, width, height, col_num, pic_path):
    """拼接图片缩略图"""
    imgs = [Image.open(i).resize((width, height)) for i in img_links]
    rows = height * (len(imgs) // col_num + 1) if len(imgs) % col_num != 0 else height * (len(imgs) // col_num)
    big_pic = Image.new('RGBA', (width * col_num, rows), 'white')

    for num, img in enumerate(imgs):
        x = num % col_num * width
        y = num // col_num * height
        big_pic.paste(img, (x, y))

    # big_pic.show()
    # plt.imshow(big_pic)
    # plt.show()
    big_pic.save(pic_path)


def add_stars(stars, width, height, col_num, pic_path, font_path):
    """添加书本评价星标"""
    big_pic = Image.open(pic_path)
    draw = ImageDraw.Draw(big_pic)
    font = ImageFont.truetype(font_path, 32)

    for num, star in enumerate(stars):
        x = num % col_num * width
        y = num // col_num * height
        # draw.rectangle((x, y+col_num, x+width, int(y+40)), fill=(23, 103, 224, 255))
        draw.rectangle((x, y+col_num, x+width, int(y+40)), fill=(226, 221, 70, 255))
        # draw.text((x, y), star, fill='darkred', font=font)
        draw.text((x, y), star, fill=(204, 48, 67, 255), font=font)

    # big_pic.show()
    # plt.imshow(big_pic)
    # plt.show()
    big_pic.save(pic_path)


if "__main__" == __name__:
    records = pathlib.Path(r".\my_douban_data\豆瓣读书记录_2023.md")
    sort_flag = True    # 是否按评价排序
    img_links, stars = get_images_and_stars(records, sort_flag)

    width, height = 270, 400    # 单幅缩略图尺寸
    col_num = 10    # 每行包含的图片数
    pic_path = pathlib.Path(r".\书籍封面图集合.png")     # 拼接图保存路径
    font_path = r'.\msyh.ttf'  # 字体文件

    combine_pics(img_links, width, height, col_num, pic_path)
    add_stars(stars, width, height, col_num, pic_path, font_path)

    # 生成部分书籍封面图片墙
    # top = 7
    # img_links_top = img_links[:top]
    # pic_path = "五星书籍封面图集合.png"     # 拼接图保存路径
    # col_num = 4    # 每行包含的图片数
    # combine_pics(img_links_top, width, height, col_num, pic_path)

    print(f"拼接图片已保存到‘{pic_path.absolute()}’。")
