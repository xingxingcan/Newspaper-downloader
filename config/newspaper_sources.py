# -*- coding: utf-8 -*-
"""
报纸源配置模块
定义预设报纸及其下载适配器，支持扩展自定义报纸源
"""

# 报纸源配置结构：
# - id: 唯一标识符
# - name: 显示名称
# - adapter: 下载适配器类名（在 downloader 模块中实现）
# - enabled: 是否可用（某些源可能因网站改版暂时失效）
# - description: 简要说明

NEWSPAPER_SOURCES = [
    {
        "id": "rmrb",
        "name": "人民日报",
        "adapter": "PeopleDailyAdapter",
        "enabled": True,
        "description": "人民网电子版，支持分页下载合并为 PDF",
    },
    {
        "id": "xinhua",
        "name": "新华每日电讯",
        "adapter": "XinhuaAdapter",
        "enabled": True,
        "description": "新华社主办，需适配其官网结构",
    },
    {
        "id": "hqsb",
        "name": "环球时报",
        "adapter": "GlobalTimesAdapter",
        "enabled": True,
        "description": "环球网电子版",
    },
    {
        "id": "gmrb",
        "name": "光明日报",
        "adapter": "GuangmingAdapter",
        "enabled": True,
        "description": "光明网电子版",
    },
    {
        "id": "jjrb",
        "name": "经济日报",
        "adapter": "EconomicDailyAdapter",
        "enabled": True,
        "description": "经济日报电子版",
    },
]
