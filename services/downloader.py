from config import Config
import requests
from concurrent.futures import ThreadPoolExecutor
import os
import time


class Downloader:
    def __init__(self):
        self._executor = ThreadPoolExecutor(
            max_workers=Config.get_max_concurrent_downloads()
        )
        self._active_downloads = 0
        self._speed_limit = (
            Config.get_download_speed_limit() * 1024 * 1024
        )  # 转换为字节/秒

    def download_segment(self, url, save_path):
        verify = Config.get_ssl_verify()

        # 应用下载速度限制
        if self._speed_limit > 0:
            response = requests.get(url, verify=verify, stream=True)
            chunk_size = min(8192, self._speed_limit)  # 每次读取的块大小
            start_time = time.time()
            downloaded = 0

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 计算需要的延迟来达到速度限制
                        elapsed = time.time() - start_time
                        expected_time = downloaded / self._speed_limit
                        if expected_time > elapsed:
                            time.sleep(expected_time - elapsed)
        else:
            # 无速度限制的下载
            response = requests.get(url, verify=verify)
            with open(save_path, "wb") as f:
                f.write(response.content)
