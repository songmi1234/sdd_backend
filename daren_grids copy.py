import json
import asyncio
import aiohttp
import os
import cv2
import numpy as np
import secrets
import string
import time
print(cv2.__version__)
# --- 数据读取 ---
SAVE_DIR = "static/photo"
SAVE_GIRDS_DIR = "static/photo/grids"


def author_home_prase():
    file = 'item.json'
    with open(file, 'r', encoding='utf-8') as f:
        item = json.load(f)

    content_list = item.get('data').get('content_list', [])

    # 提取数据
    data_list = []
    for video in content_list:
        cover = video.get('preview_pic')
        uri = video.get('title')
        # url_list = cover.get('url_list', [])
        # if uri and len(url_list) > 1:
        data_list.append({f"{uri}.jpeg": cover})
    return data_list


# --- 异步下载逻辑 ---


async def download_one(session, filename, url, sem):
    """下载单个文件的协程，受信号量限制"""
    async with sem:  # 限制同时下载的数量
        print(f"当前排队任务数: {len(sem._waiters) if sem._waiters else 0}")
        clean_name = filename.split('/')[-1]
        save_path = os.path.join(SAVE_DIR, clean_name)

        try:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    content = await response.read()
                    # 这里可以使用 aiofiles 实现全异步，但对于小图 open 足够了
                    with open(save_path, 'wb') as f:
                        f.write(content)
                    print(f"✅ 已完成: {clean_name}")
                    return save_path
                else:
                    print(f"❌ 失败 ({response.status}): {clean_name}")
        except Exception as e:
            print(f"⚠️ 异常 ({clean_name}): {e}")
        return None


async def photo_download(data_list):
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # 1. 设置信号量：限制同时最多下载 3 个
    sem = asyncio.Semaphore(3)

    async with aiohttp.ClientSession() as session:
        # 2. 创建所有待选任务
        tasks = []
        for item_dict in data_list:
            for filename, url in item_dict.items():
                tasks.append(download_one(session, filename, url, sem))

        success_results = []

        # 3. 使用 as_completed 监控完成情况
        # 只要有任务下载完，立即判断是否达到 9 个
        for next_task in asyncio.as_completed(tasks):
            result = await next_task

            if result:
                success_results.append(result)

            # 4. 达到总数 9 个立即收工
            if len(success_results) >= 9:
                print(f"\n🎯 已经成功下载 {len(success_results)} 个文件，停止后续任务。")
                break

        return success_results


def resize_letterbox(img, target_w, target_h, bg_color=(200, 200, 200)):
    """
    留白模式：等比例缩放，不足部分填充背景色，确保图片不被裁剪且不变形
    """
    h, w = img.shape[:2]

    # 1. 计算缩放比例 (取最小值，确保图片能完整放入格子)
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)

    # 2. 等比例缩放图片
    img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 3. 创建一个格子的纯色底板
    layer = np.full((target_h, target_w, 3), bg_color, dtype=np.uint8)

    # 4. 将缩放后的图片居中贴在底板上
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2
    # [纵坐标y, 横坐标x]
    layer[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = img_resized

    return layer


def create_9_grid_with_filler(image_paths, filename="final_grid.jpg"):
    save_path = os.path.join(SAVE_GIRDS_DIR, filename)

    target_w, target_h = 540, 960
    # 画布背景设为灰色
    bg_color = (200, 200, 200)
    canvas = np.full((target_h * 3, target_w * 3, 3), bg_color, dtype=np.uint8)

    for i in range(3):
        for j in range(3):
            index = i * 3 + j
            y_start, x_start = i * target_h, j * target_w

            if index < len(image_paths):
                img = cv2.imread(image_paths[index])
                if img is not None:
                    # --- 使用留白模式 ---
                    img_final = resize_letterbox(
                        img, target_w, target_h, bg_color)
                    canvas[y_start:y_start + target_h,
                           x_start:x_start + target_w] = img_final
            else:
                cv2.putText(canvas, "Missing", (x_start + 250, y_start + 500),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (150, 150, 150), 3)

    cv2.imwrite(save_path, canvas)
    print(f"✅ 留白九宫格已生成: {save_path}")

    return save_path


def generate_random_filename(extension=".jpg"):
    # 获取当前时间戳 (20260201-1152)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    # 生成 6 位随机字母和数字
    random_str = ''.join(secrets.choice(
        string.ascii_letters + string.digits) for _ in range(6))
    return f"{timestamp}-{random_str}{extension}"

# def main():


#     pass
if __name__ == "__main__":
    data_list = author_home_prase()
    if not data_list:
        print("未发现有效下载链接，请检查 item.json 结构。")
    else:
        print(f"🚀 开始异步下载（并发限制: 3, 目标总数: 9）...")
        all_paths = asyncio.run(photo_download(data_list))
        print("\n" + "="*30)
        print(f"✨ 下载结束。")
        print(f"成功列表: {all_paths}")
        print(f"成功数量: {len(all_paths)}")
    if len(all_paths) > 0:
        create_9_grid_with_filler(all_paths[0:9], generate_random_filename())
    else:
        print("🛑 成功下载的数量不足 9 个，跳过拼图步骤。")
