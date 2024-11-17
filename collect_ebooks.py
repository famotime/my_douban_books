"""
在本地硬盘上查找一个清单文件中的所有电子书，并复制到一个新的目录中。

功能说明：
1. 清单文件支持两种格式：
   - 使用《》包裹的书名
   - 直接写书名（每行一个）
2. 搜索规则：
   - 文件名必须以搜索词开头（忽略标点符号和大小写）
   - 支持中文、英文和数字
   - 文件类型优先级：epub > pdf > txt
3. 处理流程：
   - 首次运行时生成搜索目录下的文件列表（_file_list.txt）
   - 跳过已经存在于输出目录中的文件
   - 生成处理结果文件（清单文件名_结果.txt）
   - 复制找到的文件到输出目录
4. 输出报告：
   - 总文件数统计
   - 已存在文件数
   - 新找到文件数
   - 成功复制数
   - 未找到文件清单
   - 复制失败文件列表

注意事项：
- 跳过系统目录和特殊文件夹的扫描
- 不验证文件是否真实存在
- 使用文件缓存提升搜索性能
"""

from pathlib import Path
import shutil
import re
import time

def generate_file_list(search_dir):
    """
    生成目录下所有文件的路径列表文件
    Args:
        search_dir: 搜索目录路径
    Returns:
        文件列表文件的路径
    """
    search_path = Path(search_dir)
    file_list_path = search_path / '_file_list.txt'

    print(f"正在生成文件列表：{file_list_path}")

    # 收集所有epub、pdf和txt文件
    files = []
    for ext in ['.epub', '.pdf', '.txt']:
        try:
            for p in search_path.rglob(f'*{ext}'):
                try:
                    # 跳过系统目录和无法访问的文件
                    # 要跳过的系统目录和文件名列表
                    SKIP_DIRS = {
                        'System Volume Information',
                        '$Recycle.Bin',
                        '$RECYCLE.BIN',
                        'Config.Msi',
                        'Recovery',
                        'Documents and Settings',
                        'PerfLogs',
                        'Program Files',
                        'Program Files (x86)',
                        'Windows'
                    }
                    if p.is_file() and not any(x.startswith('$') or x in SKIP_DIRS for x in p.parts):
                        files.append(str(p))
                except (PermissionError, OSError):
                    continue
        except Exception as e:
            print(f"搜索{ext}文件时出错: {e}")
            continue

    # 将文件列表写入文件
    with file_list_path.open('w', encoding='utf-8') as f:
        f.write('\n'.join(files))

    print(f"文件列表生成完成，共 {len(files)} 个文件")
    return file_list_path

def clean_filename(filename):
    """
    清理文件名中的标点符号和空格，只保留中文、英文和数字
    """
    # 使用正则表达式保留中文字符、英文字母和数字
    cleaned = re.sub(r'[^\u4e00-\u9fff\w]', '', filename)
    return cleaned.lower()  # 转换为小写

def search_file(filename, search_dir):
    """
    在文件列表中搜索文件
    Args:
        filename: 要搜索的文件名
        search_dir: 搜索目录路径
    """
    search_path = Path(search_dir)
    file_list_path = search_path / '_file_list.txt'
    name = clean_filename(filename)
    if not name:
        name = filename.lower()

    print(f"正在搜索：{filename}（清理后的搜索词：{name}）")

    # 如果文件列表不存在或为空，则生成
    if not file_list_path.exists() or file_list_path.stat().st_size == 0:
        file_list_path = generate_file_list(search_dir)

    # 优化1：使用全局缓存，避免重复读取文件列表
    if not hasattr(search_file, '_file_cache'):
        search_file._file_cache = {'.epub': [], '.pdf': [], '.txt': []}
        with file_list_path.open('r', encoding='utf-8') as f:
            for line in f:
                path = Path(line.strip())
                ext = path.suffix.lower()
                if ext in search_file._file_cache:
                    # 预处理文件名，避免重复清理
                    search_file._file_cache[ext].append((str(path), clean_filename(path.stem)))

    # 使用缓存搜索
    for ext in ['.epub', '.pdf', '.txt']:
        for file_path, clean_stem in search_file._file_cache[ext]:
            if clean_stem.startswith(name):
                return file_path

    print(f"未找到：{filename}")
    return "未找到"

def check_file_list_update(search_dir):
    """
    检查文件列表是否需要更新
    Args:
        search_dir: 搜索目录路径
    Returns:
        bool: 是否需要更新
    """
    search_path = Path(search_dir)
    file_list_path = search_path / '_file_list.txt'

    # 如果文件列表不存在或为空，需要生成
    if not file_list_path.exists() or file_list_path.stat().st_size == 0:
        print(f"文件列表{file_list_path}不存在或为空，需要生成。")
        return True

    # 如果文件列表超过24小时未更新，建议更新
    # file_age = time.time() - file_list_path.stat().st_mtime
    # if file_age > 24 * 3600:  # 24小时
    #     user_input = input("文件列表已超过24小时未更新，是否重新生成？(y/n): ")
    #     return user_input.lower() == 'y'

    return False

def extract_book_names(line):
    """
    从一行文本中提取书名，支持两种格式：
    1. 使用《》包裹的书名
    2. 不包含《》的整行文本
    """
    pattern = r'《([^》]+)》'
    matches = re.findall(pattern, line)
    if matches:
        return matches
    else:
        # 如果没有《》，返回整行文本（去除首尾空白）
        line = line.strip()
        return [line] if line else []

def process_book_list(list_file, search_dir):
    """
    处理书籍清单文件
    Args:
        list_file: 清单文件路径
        search_dir: 搜索目录路径
    """
    list_path = Path(list_file)
    search_path = Path(search_dir)

    if not list_path.exists():
        raise FileNotFoundError(f"清单文件不存在: {list_file}")
    if not search_path.exists():
        raise FileNotFoundError(f"搜索目录不存在: {search_dir}")

    # 创建输出目录
    output_dir = list_path.parent / list_path.stem
    output_dir.mkdir(exist_ok=True)

    # 获取输出目录中已存在的文件
    existing_files = {clean_filename(f.stem): f.stem for f in output_dir.glob('*.*')}

    # 优化3：批量读取清单文件
    with list_path.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    # 添加统计变量
    stats = {
        'total': 0,          # 总文件数
        'found': 0,          # 找到的文件数
        'copied': 0,         # 成功复制的文件数
        'existing': 0,       # 已存在的文件数
        'not_found': [],     # 未找到的文件列表
        'copy_failed': []    # 复制失败的文件列表
    }

    # 优化4：使用列表推导式处理结果
    results = []
    for line in lines:
        if not (line := line.strip()):
            continue
        book_names = extract_book_names(line)
        if not book_names:
            continue

        line_results = []
        for book_name in book_names:
            stats['total'] += 1
            clean_name = clean_filename(book_name)

            # 修改输出信息，添加跳过原因
            if clean_name in existing_files:
                stats['existing'] += 1
                result = (f"《{book_name}》: 跳过（输出目录已存在：{existing_files[clean_name]}）"
                         if '《' in line
                         else f"{book_name}: 跳过（输出目录已存在：{existing_files[clean_name]}）")
                line_results.append(result)
                continue

            file_path = search_file(book_name, search_path)
            if file_path == "未找到":
                stats['not_found'].append(book_name)
            else:
                stats['found'] += 1
                try:
                    shutil.copy2(file_path, output_dir)
                    stats['copied'] += 1
                except Exception as e:
                    stats['copy_failed'].append((book_name, str(e)))

            result = f"《{book_name}》: {file_path}" if '《' in line else f"{book_name}: {file_path}"
            line_results.append(result)

        results.append(f"{line}\t=>\t{' | '.join(line_results)}")

    # 将结果写回文件
    result_file = list_path.parent / f"{list_path.stem}_结果.txt"
    with result_file.open('w', encoding='utf-8') as f:
        f.write('\n'.join(results))

    # 打印处理总结
    print("\n" + "="*50)
    print("处理总结：")
    print(f"总共需要处理的文件数：{stats['total']}")
    print(f"已存在的文件数：{stats['existing']}")
    print(f"新找到的文件数：{stats['found']}")
    print(f"成功复制的文件数：{stats['copied']}")
    print(f"未找到的文件数：{len(stats['not_found'])}")

    if stats['not_found']:
        print("\n未找到的文件清单：")
        for book in stats['not_found']:
            print(f"- {book}")

    if stats['copy_failed']:
        print("\n复制失败的文件：")
        for book, error in stats['copy_failed']:
            print(f"- {book}: {error}")

    print("="*50)


if __name__ == "__main__":
    list_file = r"C:\Users\Administrator\Desktop\超人书单.md"
    search_dir = r"J:"

    try:
        # 检查是否需要更新文件列表
        if check_file_list_update(search_dir):
            generate_file_list(search_dir)

        process_book_list(list_file, search_dir)
        print("处理完成！")
    except Exception as e:
        print(f"处理失败: {e}")
