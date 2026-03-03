# -*- coding: utf-8 -*-
"""贵州日报，pc/layout/YYYYMM/DD/node_NN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class GuizhouDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "http://szb.eyesnews.cn"
    LAYOUT_BASE = "http://szb.eyesnews.cn/pc/layout"
    PAPER_NAME = "贵州日报"
