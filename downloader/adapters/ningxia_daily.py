# -*- coding: utf-8 -*-
"""宁夏日报，pc/layout/YYYYMM/DD/node_NN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class NingxiaDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "https://szb.nxrb.cn"
    LAYOUT_BASE = "https://szb.nxrb.cn/nxrb/pc/layout"
    PAPER_NAME = "宁夏日报"
