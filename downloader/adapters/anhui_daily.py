# -*- coding: utf-8 -*-
"""安徽日报，来源 szb.ahnews.com.cn"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class AnhuiDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "https://szb.ahnews.com.cn"
    LAYOUT_BASE = "https://szb.ahnews.com.cn/ahrb/layout"
    PAPER_NAME = "安徽日报"
