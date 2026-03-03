# -*- coding: utf-8 -*-
"""临时脚本：爬取求是网党报党刊页面，导出报纸名称和链接到控制台"""

import re
import sys
import requests

# 确保 Windows 控制台正确显示中文
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

URL = "https://www.qstheory.cn/v9zhuanqu/resource/dbdk/index.htm"


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(URL, headers=headers, timeout=15)
    resp.encoding = resp.apparent_encoding or "utf-8"
    html = resp.text

    # 匹配 <a href="链接">报纸名</a>，链接可能是相对或绝对路径
    # 求是网页面内链接通常形如 /v9zhuanqu/resource/dbdk/xxx.htm 或完整 URL
    pattern = re.compile(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>',
        re.IGNORECASE
    )

    results = []
    seen_names = set()
    base = "https://www.qstheory.cn"

    for m in pattern.finditer(html):
        href, name = m.group(1).strip(), m.group(2).strip()
        # 过滤掉导航、菜单等无关链接，只保留党报党刊列表
        if not name or len(name) < 2:
            continue
        # 排除明显非报纸的链接
        if name in ("首页", "返回", "更多", "下一页", "上一页"):
            continue
        if name in seen_names:
            continue
        seen_names.add(name)
        if href.startswith("/"):
            href = base + href
        elif href.startswith("http"):
            pass
        else:
            href = base + "/" + href
        results.append((name, href))

    # 过滤：只保留看起来像报纸/期刊/网站名的（通常是2-15个汉字或带"报/网/刊"等）
    def is_newspaper_like(s):
        if not re.match(r"^[\u4e00-\u9fff\s·\-]+$", s):
            return False
        return 2 <= len(s) <= 20

    filtered = [(n, u) for n, u in results if is_newspaper_like(n)]

    print(f"共找到 {len(filtered)} 个报纸/期刊/网站：\n")
    for name, url in filtered:
        print(f"{name}\t{url}")


if __name__ == "__main__":
    main()
