# -*- coding: utf-8 -*-
"""甘肃日报，pc/layout/YYYYMM/DD/colNN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class GansuDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "https://szb.gansudaily.com.cn"
    LAYOUT_BASE = "https://szb.gansudaily.com.cn/gsrb/pc/layout"
    PAPER_NAME = "甘肃日报"
