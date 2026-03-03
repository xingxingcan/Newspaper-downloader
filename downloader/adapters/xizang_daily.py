# -*- coding: utf-8 -*-
"""西藏日报，e.xzxw.com/xzrb/YYYYMM/DD/node_NN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class XizangDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "https://e.xzxw.com"
    LAYOUT_BASE = "https://e.xzxw.com/xzrb"
    PAPER_NAME = "西藏日报"
