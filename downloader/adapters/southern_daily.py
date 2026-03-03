# -*- coding: utf-8 -*-
"""南方日报，epaper.nfnews.com/nfdaily/html/YYYYMM/DD/node_A01.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class SouthernDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "https://epaper.nfnews.com"
    LAYOUT_BASE = "https://epaper.nfnews.com/nfdaily/html"
    PAPER_NAME = "南方日报"
