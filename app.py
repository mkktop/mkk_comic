import requests
import json
import os
import time
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import yaml
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
import re
from logging.handlers import TimedRotatingFileHandler

CONFIG_PATH = "./config/comic.yaml"
API_ADDER = "api.2025copy.com"
pdf_switch = 1
pdf_password=None

class Color:
    """ANSI颜色代码类"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # 文本颜色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 背景颜色
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # 亮色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 亮色背景
    BG_BRIGHT_BLACK = "\033[100m"
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"

def setup_rotating_logger():
    # 1. 创建日志器（命名为项目名，避免与其他日志器冲突）
    logger = logging.getLogger("mkk_comic")
    logger.setLevel(logging.DEBUG)  # 日志器总级别（需≤处理器级别）
    logger.propagate = False  # 防止日志向上传播（避免重复输出）

    # 清空已有Handler（防止重复配置）
    if logger.handlers:
        logger.handlers.clear()

    # 2. 确保日志目录存在
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'data_{datetime.now().strftime("%Y-%m-%d")}.log')

    # 3. 创建按时间轮转的文件Handler（核心配置）
    # when='D'：按天轮转；interval=1：每1天轮转一次；backupCount=7：保留7个备份（即7天日志）
    file_handler = TimedRotatingFileHandler(
        filename=log_file,          # 基础日志文件名
        when='D',                   # 轮转单位：D(天)、H(小时)、M(分钟)、S(秒)
        interval=1,                 # 每1天轮转一次
        backupCount=7,              # 保留7个备份文件（超过自动删除）
        encoding='utf-8',           # 中文编码，避免乱码
        delay=False,                # 立即创建日志文件
        utc=True                   # 使用本地时间（True则用UTC时间）
    )

    # 可选：自定义轮转文件名（默认格式：app.log.2025-12-17）
    file_handler.suffix = "%Y-%m-%d"  # 轮转文件后缀（按日期命名）
    # 过滤非日期后缀的文件（避免删除其他文件）
    file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}(\.\w+)?$")

    # 4. 创建控制台Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台只输出INFO及以上

    # 5. 定义日志格式（包含时间、模块、行号等关键信息）
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(log_formatter)
    console_handler.setFormatter(log_formatter)

    # 6. 将Handler添加到日志器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def clear_terminal():
    """清除终端屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_terminal_width():
    """获取终端宽度"""
    try:
        return os.get_terminal_size().columns
    except:
        return 80  # 默认宽度

def is_running_in_github_actions() -> bool:
    """判断程序是否在 GitHub Actions 中运行"""
    # 检测 GitHub Actions 专属环境变量
    return os.getenv("GITHUB_ACTIONS", "false").lower() == "true"

def print_title_style():
    """渐变色彩标题"""
    clear_terminal()
    width = get_terminal_width()
    title = "MKK COMIC"

    # 渐变色彩列表
    colors = [
        Color.BRIGHT_RED,
        Color.BRIGHT_YELLOW,
        Color.BRIGHT_GREEN,
        Color.BRIGHT_CYAN,
        Color.BRIGHT_BLUE,
        Color.BRIGHT_MAGENTA
    ]
    # 生成渐变标题
    gradient_title = ""
    color_index = 0
    step = len(colors) / len(title)

    for char in title:
        gradient_title += colors[int(color_index)] + Color.BOLD + char + Color.RESET
        color_index += step
    # 添加装饰
    padding = (width - len(title) - 4) // 2
    print(" " * padding + "✨ " + gradient_title + " ✨")
    print("=" * width)

def print_separate():
    width = get_terminal_width()
    print("=" * width)

def search_copy_manga(keyword, page_num=1):
    """
    使用CopyManga客户端的请求头搜索漫画
    参数:
        keyword (str): 搜索关键词
        page_num (int): 页码，默认第1页
    返回:
        dict: 解析后的JSON响应数据
    """
    # 定义请求头（与CopyManga客户端完全一致）
    headers = {
        "User-Agent": "COPY/3.0.0",
        "Accept": "application/json",
        "version": "2025.08.15",
        "platform": "1",
        "webp": "1",
        "region": "1"
    }

    # 定义请求参数
    limit = 5 #每次获取n个
    offset = (page_num - 1) * limit #偏移量
    params = {
        "limit": limit,
        "offset": offset,
        "q": keyword,
        "q_type": "",
        "platform": 1
    }
    # API地址
    api_url = "https://" + API_ADDER + "/api/v3/search/comic"
    try:
        # 发送GET请求
        response = requests.get(api_url, headers=headers, params=params)
        # 检查响应状态码
        response.raise_for_status()
        # 解析JSON响应
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        logger.warning(f"请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析错误: {e}")
        return None

def print_search_results(results):
    """打印搜索结果"""
    if not results:
        logger.warning("没有获取到结果")
        return

    if results.get("code") != 200:
        logger.warning(f"搜索失败: {results.get('message', '未知错误')}")
        return
    #获取结果
    results_data = results.get("results", {})
    total = results_data.get("total", 0)
    limit = results_data.get("limit", 20)
    offset = results_data.get("offset", 0)
    comic_list = results_data.get("list", [])

    logger.info(f"\n搜索结果: 共找到 {total} 本漫画")
    logger.info(f"当前显示第 {offset // limit + 1} 页，每页 {limit} 本")

    print_separate()
    for index, comic in enumerate(comic_list, start=offset + 1):
        logger.info(f"\n{index}. {comic.get('name', '未知标题')}")
        author = comic.get("author", [])
        for i,a in enumerate(author, start=1):
            logger.info(f"   作者: {a.get('name', '未知作者')}")
        logger.info(f"   分类: {comic.get('alias', '未知分类')}")
        logger.info(f"   路径: {comic.get('path_word', '无路径')}")
        logger.info(f"   封面: {comic.get('cover', '无路径')}")
        print_separate()

def print_full_json(json_data):
    """打印完整的JSON响应"""
    if json_data:
        logger.info("\n=== 完整JSON响应 ===")
        logger.info(json.dumps(json_data, indent=2, ensure_ascii=False))
        logger.info("=== JSON响应结束 ===")
    else:
        logger.info("没有JSON数据可打印")

def get_comic(comic_path_word):
    headers = {
        "User-Agent": "COPY/3.0.0",
        "Accept": "application/json",
        "version": "2025.08.15",
        "platform": "1",
        "webp": "1",
        "region": "1"
    }
    params = {
        "platform": 1
    }
    # API地址
    api_url = "https://" + API_ADDER + "/api/v3/comic2/" + comic_path_word
    try:
        # 发送GET请求
        response = requests.get(api_url, headers=headers,params=params)

        # 检查响应状态码
        response.raise_for_status()

        # 解析JSON响应
        data = response.json()

        return data

    except requests.exceptions.RequestException as e:
        logger.warning(f"请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析错误: {e}")
        return None

def print_comic_results(results):
    if not results:
        logger.warning("没有获取到结果")
        return

    if results.get("code") != 200:
        logger.warning(f"搜索失败: {results.get('message', '未知错误')}")
        return
    results_data = results.get("results", {})
    comic = results_data.get("comic", {})
    logger.info(f"   名称: {comic.get('name', '未知作品')}")
    logger.info(f"   标签: {comic.get('alias', '未知标签')}")
    logger.info(f"   简介: {comic.get('brief', '未知简介')}")
    logger.info(f"   最后更新时间: {comic.get('datetime_updated', '未知简介')}")
    new_chapter = comic.get("last_chapter", {})
    logger.info(f"   最新章节: {new_chapter.get('name', '未知章节')}")

def get_chapters(comic_path_word,page_num=1):
    headers = {
        "User-Agent": "COPY/3.0.0",
        "Accept": "application/json",
        "version": "2025.08.15",
        "platform": "1",
        "webp": "1",
        "region": "1"
    }
    limit = 50 #每次获取n个
    offset = (page_num - 1) * limit #偏移量
    params = {
        "limit": limit,
        "offset": offset,
    }
    api_url = "https://" + API_ADDER + "/api/v3/comic/" + comic_path_word + "/group/default/chapters"
    try:
        # 发送GET请求
        response = requests.get(api_url, headers=headers,params=params)

        # 检查响应状态码
        response.raise_for_status()

        # 解析JSON响应
        data = response.json()

        return data

    except requests.exceptions.RequestException as e:
        logger.warning(f"请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析错误: {e}")
        return None

def print_chapters_results(results):
    if not results:
        logger.warning("没有获取到结果")
        return 0
    if results.get("code") != 200:
        logger.warning(f"搜索失败: {results.get('message', '未知错误')}")
        return 0
    results_data = results.get("results", {})
    total = results_data.get("total", 0)
    limit = results_data.get("limit", 50)
    offset = results_data.get("offset", 0)
    comic_list = results_data.get("list", [])
    logger.info(f"\n搜索结果: 共找到 {total} 个章节")
    logger.info(f"当前显示第 {offset // limit + 1} 页，每页 {limit} 章节")
    for index, comic in enumerate(comic_list, start=offset + 1):
        logger.info(f"\n第{index}章: {comic.get('name', '未知章节')}    大小:{comic.get('size', '未知大小')}  日期:{comic.get('datetime_created', '未知日期')}")
    return total


def get_comic_image(comic_path_word,uuid):
    headers = {
        "User-Agent": "COPY/3.0.0",
        "Accept": "application/json",
        "version": "2025.08.15",
        "platform": "1",
        "webp": "1",
        "region": "1"
    }
    api_url = "https://" + API_ADDER + "/api/v3/comic/" + comic_path_word + "/chapter2/" + uuid
    try:
        # 发送GET请求
        response = requests.get(api_url, headers=headers)

        # 检查响应状态码
        response.raise_for_status()

        # 解析JSON响应
        data = response.json()

        return data

    except requests.exceptions.RequestException as e:
        logger.warning(f"请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析错误: {e}")
        return None

def images_to_pdf(image_dir, output_pdf, number, password=None):


    c = canvas.Canvas(output_pdf, pagesize=letter)  # 创建 PDF 画布
    width, height = letter  # 获取页面尺寸
    if password:

        c.setEncrypt(password)

    for i in range(1, number):
        image_name = f"{i:03d}.jpg"  # 生成图片文件名，如 001.jpg, 002.jpg ...
        image_path = os.path.join(image_dir, image_name)

        if not os.path.exists(image_path):
            logger.warning(f"警告: 图片 {image_path} 不存在，跳过.")
            continue

        try:
            img = Image.open(image_path)
            img_width, img_height = img.size

            # 按比例缩放图片以适应页面
            scale_x = width / img_width
            scale_y = height / img_height
            scale = min(scale_x, scale_y)
            new_width = img_width * scale
            new_height = img_height * scale

            x = (width - new_width) / 2
            y = (height - new_height) / 2

            c.drawImage(image_path, x, y, width=new_width, height=new_height)
            c.showPage() # 添加新页面
            logger.info(f"恭喜:图片 {image_name} 添加成功。")
        except Exception as e:
            logger.warning(f"错误: 处理图片 {image_path} 时出错: {e}")

    c.save()
    logger.info(f"PDF 文件已生成: {output_pdf}")

def make_pdf(path, number, password=None):

    # 确保传入的路径是绝对路径
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    logger.info(f"指定的图片目录: {path}")

    # 获取当前目录名称
    current_dir_name = os.path.basename(path.rstrip('/\\'))
    logger.info(f"当前目录名称: {current_dir_name}")

    # 获取上一级目录路径
    parent_dir = os.path.dirname(path)
    logger.info(f"上一级目录: {parent_dir}")

    # 构建输出PDF路径（在上一级目录）
    output_pdf_file = os.path.join(parent_dir, f"{current_dir_name}.pdf")
    logger.info(f"输出PDF文件: {output_pdf_file}")

    # 确保图片目录存在
    if not os.path.exists(path):
        logger.warning(f"错误: 目录 {path} 不存在.")
        return

    # 确保上一级目录存在（用于保存PDF）
    if not os.path.exists(parent_dir):
        logger.warning(f"错误: 上一级目录 {parent_dir} 不存在.")
        return

    # 检查目录中是否有图片文件
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
    image_files = []

    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                image_files.append(file_path)

    if not image_files:
        logger.warning(f"警告: 目录 {path} 中没有找到图片文件")
        return

    logger.info(f"找到 {len(image_files)} 张图片")

    # 调用图片转PDF函数
    images_to_pdf(path, output_pdf_file, number, password)

def handle_chapters_results(results,start_num,end_num,path):
    if not results:
        logger.warning("没有获取到结果")
        return 0
    if results.get("code") != 200:
        logger.warning(f"搜索失败: {results.get('message', '未知错误')}")
        return 0
    results_data = results.get("results", {})
    comic_list = results_data.get("list", [])
    offset = results_data.get("offset", 0)
    headers = {
        "User-Agent": "COPY/3.0.0",
        "Accept": "application/json",
        "version": "2025.08.15",
        "platform": "1",
        "webp": "1",
        "region": "1"
    }
    for index, comic in enumerate(comic_list, start=offset + 1):
        if start_num <= index <= end_num:
            logger.info(f"正在下载第{index}章: {comic.get('name', '未知章节')}    UUID:{comic.get('uuid', '')}")
            data =  get_comic_image(path, comic.get("uuid"))
            chapter = data["results"]["chapter"]
            comic_name = data["results"]["comic"]["name"]
            chapter_name = chapter["name"]
            output_dir = "./out/" + comic_name +"/" + chapter_name
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建目录: {output_dir}")
            contents = chapter["contents"]  # 所有图片信息
            words = chapter["words"]
            logger.info(f"开始下载: {comic_name} - {chapter_name}")
            logger.info(f"总页数: {len(contents)}")
            
            # 使用多线程下载图片
            success_count = download_images_multithreaded(contents, words, output_dir, headers)
            
            logger.info("下载完成!")
            logger.info(f"成功下载: {success_count}/{len(contents)} 页")
            if success_count < len(contents):
                return 0
            if pdf_switch == 1:
                if pdf_password is None:
                    make_pdf(output_dir,len(contents))
                else:
                    make_pdf(output_dir,len(contents),pdf_password)
            return 1

def download_images_multithreaded(contents, words, output_dir, headers, max_workers=5):
    """
    使用多线程下载图片
    :param contents: 图片信息列表
    :param words: 图片索引列表
    :param output_dir: 输出目录
    :param headers: 请求头
    :param max_workers: 最大线程数
    :return: 成功下载的图片数量
    """
    success_count = 0
    failed_pages = []
    
    # 创建线程池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交下载任务
        future_to_page = {}
        for i, word_index in enumerate(words):
            page_num = i + 1
            filename = f"{page_num:03d}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            future = executor.submit(download_single_image, contents[word_index]["url"], filepath, headers, page_num, len(contents))
            future_to_page[future] = page_num
    
        # 处理完成的任务
        for future in as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    failed_pages.append(page_num)
            except Exception as e:
                logger.warning(f"下载第 {page_num} 页时发生异常: {e}")
                failed_pages.append(page_num)
    
    if failed_pages:
        logger.warning(f"以下页面下载失败: {failed_pages}")
    
    return success_count


def download_single_image(img_url, filepath, headers, page_num, total_pages):
    """
    下载单张图片
    :param img_url: 图片URL
    :param filepath: 保存路径
    :param headers: 请求头
    :param page_num: 页码
    :param total_pages: 总页数
    :return: 是否下载成功
    """
    retry_count = 0
    max_retries = 5
    success = False
    
    while retry_count < max_retries and not success:
        try:
            logger.info(f"正在下载第 {page_num:03d}/{total_pages:03d} 页...",)
            response = requests.get(img_url, headers=headers, timeout=30)
            if response.status_code == 200:
                # 保存图片
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                #logger.info("✓ 成功")
                success = True
            else:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"✗ 失败 (HTTP {response.status_code})，正在尝试第 {retry_count+1}/{max_retries} 次重试...")
                    time.sleep(1)
                else:
                    logger.warning(f"✗ 失败 (HTTP {response.status_code})，已达到最大重试次数")
        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"✗ 失败 (请求超时)，正在尝试第 {retry_count+1}/{max_retries} 次重试...")
                time.sleep(1)
            else:
                logger.warning(f"✗ 失败 (请求超时)，已达到最大重试次数")
        except requests.exceptions.ConnectionError:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"✗ 失败 (连接错误)，正在尝试第 {retry_count+1}/{max_retries} 次重试...")
                time.sleep(0.1)
            else:
                logger.warning(f"✗ 失败 (连接错误)，已达到最大重试次数")
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"✗ 失败 ({str(e)})，正在尝试第 {retry_count+1}/{max_retries} 次重试...")
                time.sleep(1)
            else:
                logger.warning(f"✗ 失败 ({str(e)})，已达到最大重试次数")
        
        if not success:
            time.sleep(0.5)  # 每次重试后稍作延迟
    
    return success


def download_comic_image(start, end, path):
    while True:
        # 首先获取章节信息,根据start计算页码
        page = int((start-1 )/ 50 + 1)
        results = get_chapters(path, page)
        res = handle_chapters_results(results,start,end,path)
        if page*50 > end:
            break
        start += 50
    return res

def print_main_menu():
    """
    打印主菜单
    """
    # 打印标题
    print_title_style()
    # 选择功能
    print("   1. 搜索漫画")
    print("   2. 查看漫画详情")
    print("   3. 下载漫画")
    print("   4. PDF设置")
    print("   5. 自动更新")
    print("   6. 退出程序")
    while True:
        select = input("请输入需要的功能 (1-6): ")
        # 检查输入是否为数字
        if not select.isdigit():
            print("输入错误，请输入数字 1-6")
            continue
        select_num = int(select)
        # 检查数字范围
        if select_num < 1 or select_num > 6:
            print("输入错误，请输入数字 1-6")
        else:
            return select_num

def search_comic_function():
    print("   1. 搜索漫画功能")
    keyword = input("请输入要搜索的漫画名称: ")
    page = int(input("请输入要搜索的页码(默认1)，每页5条数据: ") or "1")
    print(f"\n正在搜索: '{keyword}' (第{page}页)...")
    results = search_copy_manga(keyword, page)
    print_search_results(results)
    print("   如需查看漫画详情请复制漫画路径")
    input("回车返回首页: ")

def view_comic_detail_function():
    print("   2. 查看漫画详情功能")
    path = input("请输入要获取的漫画路径: ")
    results = get_comic(path)
    print_comic_results(results)
    input("回车返回首页: ")

def get_latest_chapter(path):
    """获取最新章节数量"""
    results = get_chapters(path,1)
    if not results:
        logger.warning("没有获取到结果")
        return 0
    if results.get("code") != 200:
        logger.warning(f"搜索失败: {results.get('message', '未知错误')}")
        return 0
    results_data = results.get("results", {})
    total = results_data.get("total", 0)
    return total

def download_comic_function():
    print("   3. 下载漫画功能")
    path = input("请输入要下载的漫画路径: ")
    page = int(input("请输入要查看的章节页码(默认1)，每页50条数据: ") or "1")
    results = get_chapters(path,page)
    total = print_chapters_results(results)
    while True:
        is_obtain = input("是否继续获取章节(y/n): ")
        if is_obtain.lower() == "y":
            page = int(input("请输入要查看的章节页码(默认1)，每页50条数据: ") or "1")
            results = get_chapters(path, page)
            print_chapters_results(results)
        elif is_obtain.lower() == "n":
            break

    while True:
        is_obtain = input("是否需要下载章节(y/n): ")
        if is_obtain.lower() == "y":
            start = input(f"请输入起始章节:(MAX:{total})")
            # 检查输入是否为数字
            if not start.isdigit():
                print("输入错误，请输入数字")
                continue
            start_num = int(start)
            if start_num >total or start_num < 1:
                print("输入错误，请输入最大章节内的数字")
                continue
            end = input(f"请输入结束章节:(MAX:{total})")
            if not end.isdigit():
                print("输入错误，请输入数字")
                continue
            end_num = int(end)
            if end_num > total or end_num < start_num:
                print("输入错误，请输入最大章节内的数字,并大于起始章节数")
                continue
            download_comic_image(start_num, end_num,path)
        elif is_obtain.lower() == "n":
            break
    input("回车返回首页: ")


def pdf_set_function():
    global pdf_switch  # 声明使用全局变量
    global pdf_password
    print("   4. PDF设置功能")
    if pdf_switch == 0:
        print("PDF输出关闭状态")
    else:
        print("PDF输出开启状态")
        print(f"密码为{pdf_password}")
    is_switch = input("是否修改状态(y/n): ")
    if is_switch.lower() == "y":
        if pdf_switch == 0:
            print("切换状态: 关闭 -> 开启")
            pdf_switch = 1
        else:
            print("切换状态: 开启 -> 关闭")
            pdf_switch = 0

    print(f"当前PDF开关状态: {'开启' if pdf_switch == 1 else '关闭'}")
    if pdf_switch == 1:
        is_password = input("是否修改密码(y/n): ")
        if is_password.lower() == "y":
            password = input("输入密码(无密码输入:None)")
            if password == "None":
                pdf_password = None
            else:
                pdf_password = password
    input("回车继续...")

    return pdf_switch

def instructions_function():
    print(f"   5. 自动更新")
    check_and_download_comics()
def select_function(function_unm):
    print_title_style()
    if function_unm == 1:
        search_comic_function()
    elif function_unm == 2:
        view_comic_detail_function()
    elif function_unm == 3:
        download_comic_function()
    elif function_unm == 4:
        pdf_set_function()
    elif function_unm == 5:
        instructions_function()

def window_main():
    while True:
        function = print_main_menu()
        if function == 6:
            break
        #选择功能
        select_function(function)

def generate_default_config():
    """生成默认配置文件（初次运行时自动创建）"""
    default_config = {
        "global": {
            "pdf_switch": 0,
            "pdf_password": "None"
        },
        "comics": []
    }
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(default_config, f, indent=2, allow_unicode=True,sort_keys=False)
    logger.info(f"【首次运行】已自动生成默认配置文件 → {CONFIG_PATH}")
    logger.info("请修改配置文件中的漫画URL、名称等信息后重新运行！")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        generate_default_config()
        # 生成默认配置后，提示用户修改并退出（避免直接运行示例配置报错）
        exit(0)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(config):
    """更新YAML配置/状态文件（覆盖写入）"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, indent=2, allow_unicode=True,sort_keys=False)

def check_and_download_comics():
    """检查所有漫画更新，有更新则下载"""
    global pdf_switch  # 声明使用全局变量
    global pdf_password
    logger.info(f"===== 开始检查更新=====")
    #读取配置
    config = load_config()
    global_config = config["global"]
    pdf_switch = global_config["pdf_switch"]
    pdf_password = global_config["pdf_password"]
    comics = config["comics"]
    # 检测是否有有效漫画配置
    if not comics:
        logger.info("配置文件中未添加任何漫画，请修改 comic.yaml 后重新运行！")
        return

    for idx, comic in enumerate(comics):
        comic_name = comic["name"]
        comic_path = comic["path"]
        comic_last_chapter = comic["last_chapter"]
        comic_last_check_time = comic["last_check_time"]
        download_limit = comic["download_limit"]
        logger.info(f"【{comic_name}】上次下载至第{comic_last_chapter}章")
        total = get_latest_chapter(comic_path)
        if total<= comic_last_chapter:
            logger.info(f"该漫画更新至{total}章，不需要更新")
            comics[idx]["last_check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_config(config)
            continue
        logger.info(f"【{comic_name}】检测到更新！最新：{total}章")
        if comic_last_chapter + download_limit < total:
            total = comic_last_chapter + download_limit
        logger.info(f"【{comic_name}】最大下载限制为{download_limit}章-需下载{comic_last_chapter + 1}~{total}章）")
        for chapter in range(comic_last_chapter + 1, total + 1):
            if download_comic_image(chapter, chapter,comic_path):
                comics[idx]["last_chapter"] = chapter
                save_config(config)
            else:
                logger.info(f"【{comic_name}】第{chapter}章下载失败，终止后续章节下载")
                break
        comics[idx]["last_check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_config(config)
    logger.info(f"===== 检查更新完成 =====\n")

if __name__ == "__main__":
    logger = setup_rotating_logger()
    if is_running_in_github_actions():
        logger.info("运行环境：GitHub Actions（自动化模式）")
        check_and_download_comics()
    else:
        window_main()
