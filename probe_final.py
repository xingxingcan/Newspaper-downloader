# -*- coding: utf-8 -*-
import re, requests
def get(u, t=12):
    try:
        r = requests.get(u, timeout=t, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"})
        r.encoding = r.encoding or "utf-8"
        return r.status_code, r.text or ""
    except Exception as e:
        return -1, str(e)[:50]

# Yunnan - try yndaily epaper paths
print("=== Yunnan ===")
for path in ["epaper/", "epaper/ynrb/", "epaper/ynrb/html/", "ynrb/", "html/2026/01/10/", ""]:
    code, text = get("https://www.yndaily.com/" + path)
    print(path or "(root)", "code=%d len=%d" % (code, len(text)))
    if code == 200 and len(text) > 200:
        nodes = re.findall(r'node_(\d+)\.htm', text)
        pdfs = re.findall(r'["\']([^"\']+\.pdf)["\']', text, re.I)
        print(path, "nodes=%s pdfs=%d" % (nodes[:5], len(pdfs)))
        if "ynrb" in path or (nodes and not path.startswith("html")):
            break

# Xinhua Jiangsu - try xhby.net paths
print("\n=== Xinhua Jiangsu ===")
for base in ["http://xh.xhby.net", "https://newspaper.xhby.net"]:
    for path in ["", "/xhrb/", "/xhbypc/", "/pc/layout/202506/13/"]:
        u = base + path
        code, text = get(u, 15)
        if code == 200:
            has_node = "node_" in text
            has_layout = "layout" in text
            if has_node or has_layout:
                print(u[:55], "layout=%s node=%s" % (has_layout, has_node))

# Qinghai tibet3 - try different structures
print("\n=== Qinghai ===")
for path in ["qhrb/", "qhrb/pc/", "pc/", "qhrb/pc/layout/"]:
    code, text = get("http://epaper.tibet3.com/" + path)
    print(path, "code=%d len=%d" % (code, len(text)))
code2, text2 = get("http://epaper.tibet3.com/m/qhrb/20250925/243072")
print("m/qhrb/date:", code2, len(text2))
if code2 == 200 and len(text2) > 100:
    nodes = re.findall(r"node_(\d+)\.html", text2)
    print("  nodes:", nodes[:5])

# Yunnan - parse root to find node URLs
print("\n=== Yunnan node URLs ===")
code, text = get("https://www.yndaily.com/")
import re
node_urls = re.findall(r'href=["\']([^"\']*node_?\d+[^"\']*)["\']', text)
for u in node_urls[:8]:
    print(" ", u[:90])

# Try yndaily.yunnan.cn
print("\n=== yndaily.yunnan.cn ===")
code2, text2 = get("http://yndaily.yunnan.cn/")
print("code=%d len=%d" % (code2, len(text2)))
if "epaper" in (text2 or "") or "ynrb" in (text2 or ""):
    print("has epaper/ynrb")

# Xinjiang - try more patterns
print("\n=== Xinjiang ===")
base = "https://xjrb.ts.cn"
for path in ["/xjrb/20260210/", "/att/202602/10/", "/pdf/20260210/"]:
    for ext in ["1.pdf", "01.pdf", "A01.pdf"]:
        u = base + path + ext
        try:
            r = requests.head(u, timeout=8)
            if r.status_code == 200:
                print("OK:", u)
        except: pass
