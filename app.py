import requests
import json
import os
import time
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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

def clear_terminal():
    """清除终端屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_terminal_width():
    """获取终端宽度"""
    try:
        return os.get_terminal_size().columns
    except:
        return 80  # 默认宽度

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
        print(f"请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None

def print_search_results(results):
    """打印搜索结果"""
    if not results:
        print("没有获取到结果")
        return

    if results.get("code") != 200:
        print(f"搜索失败: {results.get('message', '未知错误')}")
        return
    #获取结果
    results_data = results.get("results", {})
    total = results_data.get("total", 0)
    limit = results_data.get("limit", 20)
    offset = results_data.get("offset", 0)
    comic_list = results_data.get("list", [])

    print(f"\n搜索结果: 共找到 {total} 本漫画")
    print(f"当前显示第 {offset // limit + 1} 页，每页 {limit} 本")

    print_separate()
    for index, comic in enumerate(comic_list, start=offset + 1):
        print(f"\n{index}. {comic.get('name', '未知标题')}")
        author = comic.get("author", [])
        for i,a in enumerate(author, start=1):
            print(f"   作者: {a.get('name', '未知作者')}")
        print(f"   分类: {comic.get('alias', '未知分类')}")
        print(f"   路径: {comic.get('path_word', '无路径')}")
        print(f"   封面: {comic.get('cover', '无路径')}")
        print_separate()

def print_full_json(json_data):
    """打印完整的JSON响应"""
    if json_data:
        print("\n=== 完整JSON响应 ===")
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
        print("=== JSON响应结束 ===")
    else:
        print("没有JSON数据可打印")

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
        print(f"请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None

def print_comic_results(results):
    if not results:
        print("没有获取到结果")
        return

    if results.get("code") != 200:
        print(f"搜索失败: {results.get('message', '未知错误')}")
        return
    results_data = results.get("results", {})
    comic = results_data.get("comic", {})
    print(f"   名称: {comic.get('name', '未知作品')}")
    print(f"   标签: {comic.get('alias', '未知标签')}")
    print(f"   简介: {comic.get('brief', '未知简介')}")
    print(f"   最后更新时间: {comic.get('datetime_updated', '未知简介')}")
    new_chapter = comic.get("last_chapter", {})
    print(f"   最新章节: {new_chapter.get('name', '未知章节')}")

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
        print(f"请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None

def print_chapters_results(results):
    if not results:
        print("没有获取到结果")
        return 0
    if results.get("code") != 200:
        print(f"搜索失败: {results.get('message', '未知错误')}")
        return 0
    results_data = results.get("results", {})
    total = results_data.get("total", 0)
    limit = results_data.get("limit", 50)
    offset = results_data.get("offset", 0)
    comic_list = results_data.get("list", [])
    print(f"\n搜索结果: 共找到 {total} 个章节")
    print(f"当前显示第 {offset // limit + 1} 页，每页 {limit} 章节")
    for index, comic in enumerate(comic_list, start=offset + 1):
        print(f"\n第{index}章: {comic.get('name', '未知章节')}    大小:{comic.get('size', '未知大小')}  日期:{comic.get('datetime_created', '未知日期')}")
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
        print(f"请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
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
            print(f"警告: 图片 {image_path} 不存在，跳过.")
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
            print(f"恭喜:图片 {image_name} 添加成功。")
        except Exception as e:
            print(f"错误: 处理图片 {image_path} 时出错: {e}")

    c.save()
    print(f"PDF 文件已生成: {output_pdf}")

def make_pdf(path, number, password=None):

    # 确保传入的路径是绝对路径
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    print(f"指定的图片目录: {path}")

    # 获取当前目录名称
    current_dir_name = os.path.basename(path.rstrip('/\\'))
    print(f"当前目录名称: {current_dir_name}")

    # 获取上一级目录路径
    parent_dir = os.path.dirname(path)
    print(f"上一级目录: {parent_dir}")

    # 构建输出PDF路径（在上一级目录）
    output_pdf_file = os.path.join(parent_dir, f"{current_dir_name}.pdf")
    print(f"输出PDF文件: {output_pdf_file}")

    # 确保图片目录存在
    if not os.path.exists(path):
        print(f"错误: 目录 {path} 不存在.")
        return

    # 确保上一级目录存在（用于保存PDF）
    if not os.path.exists(parent_dir):
        print(f"错误: 上一级目录 {parent_dir} 不存在.")
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
        print(f"警告: 目录 {path} 中没有找到图片文件")
        return

    print(f"找到 {len(image_files)} 张图片")

    # 调用图片转PDF函数
    images_to_pdf(path, output_pdf_file, number, password)

def handle_chapters_results(results,start_num,end_num,path):
    if not results:
        print("没有获取到结果")
        return
    if results.get("code") != 200:
        print(f"搜索失败: {results.get('message', '未知错误')}")
        return
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
            print(f"\n正在下载第{index}章: {comic.get('name', '未知章节')}    UUID:{comic.get('uuid', '')}")
            data =  get_comic_image(path, comic.get("uuid"))
            chapter = data["results"]["chapter"]
            comic_name = data["results"]["comic"]["name"]
            chapter_name = chapter["name"]
            output_dir = "./out/" + comic_name +"/" + chapter_name
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"创建目录: {output_dir}")
            contents = chapter["contents"]  # 所有图片信息
            words = chapter["words"]
            print(f"开始下载: {comic_name} - {chapter_name}")
            print(f"总页数: {len(contents)}")
            # 下载计数器
            success_count = 0
            failed_pages = []
            for i, word_index in enumerate(words):
                page_num = i + 1  # 当前页码（从1开始）
                filename = f"{page_num:03d}.jpg"  # 格式化为三位数
                filepath = os.path.join(output_dir, filename)
                retry_count = 0
                max_retries = 5
                success = False
                
                while retry_count < max_retries and not success:
                    try:
                        img_url = contents[word_index]["url"]
                        print(f"正在下载第 {page_num:03d}/{len(contents):03d} 页...", end=" ")
                        response = requests.get(img_url, headers=headers, timeout=30)
                        if response.status_code == 200:
                            # 保存图片
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            success_count += 1
                            print("✓ 成功")
                            success = True
                        else:
                            retry_count += 1
                            if retry_count < max_retries:
                                print(f"✗ 失败 (HTTP {response.status_code})，正在尝试第 {retry_count+1}/{max_retries} 次重试...")
                                time.sleep(1)
                            else:
                                print(f"✗ 失败 (HTTP {response.status_code})，已达到最大重试次数")
                                failed_pages.append(page_num)
                    except requests.exceptions.Timeout:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"✗ 失败 (请求超时)，正在尝试第 {retry_count+1}/{max_retries} 次重试...")
                            time.sleep(1)
                        else:
                            print(f"✗ 失败 (请求超时)，已达到最大重试次数")
                            failed_pages.append(page_num)
                    except requests.exceptions.ConnectionError:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"✗ 失败 (连接错误)，正在尝试第 {retry_count+1}/{max_retries} 次重试...")
                            time.sleep(0.1)
                        else:
                            print(f"✗ 失败 (连接错误)，已达到最大重试次数")
                            failed_pages.append(page_num)
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"✗ 失败 ({str(e)})，正在尝试第 {retry_count+1}/{max_retries} 次重试...")
                            time.sleep(1)
                        else:
                            print(f"✗ 失败 ({str(e)})，已达到最大重试次数")
                            failed_pages.append(page_num)
                
                if not success:
                    failed_pages.append(page_num)
                time.sleep(0.5)

            print("下载完成!")
            print(f"成功下载: {success_count}/{len(contents)} 页")
            if pdf_switch == 1:
                if pdf_password is None:
                    make_pdf(output_dir,len(contents))
                else:
                    make_pdf(output_dir,len(contents),pdf_password)

def download_comic_image(start, end, path):
    print("开始下载")
    while True:
        # 首先获取章节信息,根据start计算页码
        page = int((start-1 )/ 50 + 1)
        results = get_chapters(path, page)
        handle_chapters_results(results,start,end,path)
        if page*50 > end:
            break
        start += 50

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
    print("   5. 使用说明")
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
    print(f"   5. 说明书")
    print(f"   如果需要下载漫画，需要先进行搜索，获取漫画对应的地址")
    print(f"   下载漫画前需要获取一下章节")
    print(f"   程序默认不转换PDF，如有需要请打开开关")
    input("回车继续...")

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

def git_action_main():
    #github_action测试
    comic = "haizeiwang"
    download_comic_image(372,372,comic)


if __name__ == "__main__":
    #window_main()
    git_action_main()