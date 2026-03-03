# -*- coding: utf-8 -*-
"""
HTTP 客户端
模拟真实浏览器请求，降低被识别为爬虫的风险
"""

import random
import time
import requests

# 模拟常见浏览器 User-Agent（定期更新以贴近真实用户）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
]


def get_browser_headers(referer: str = None, include_ua: bool = True) -> dict:
    """
    获取模拟浏览器的请求头。
    include_ua=False 时仅返回 Referer 等可变头，便于与 Session 共用同一 User-Agent。
    """
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none" if not referer else "same-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    if include_ua:
        headers["User-Agent"] = random.choice(USER_AGENTS)
    if referer:
        headers["Referer"] = referer
    return headers


def random_delay(min_sec: float = 0.3, max_sec: float = 0.9) -> None:
    """随机延迟，模拟人工操作间隔"""
    time.sleep(random.uniform(min_sec, max_sec))


def create_session(base_url: str = None) -> requests.Session:
    """创建带浏览器特征的 Session，固定 User-Agent，维持连接池与 Cookie"""
    session = requests.Session()
    session.headers.update(get_browser_headers(base_url, include_ua=True))
    return session
