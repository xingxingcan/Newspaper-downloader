# -*- coding: utf-8 -*-
"""陕西日报，pc/layout/YYYYMM/DD/node_NN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class ShaanxiDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "http://esb.sxdaily.com.cn"
    LAYOUT_BASE = "http://esb.sxdaily.com.cn/pc/layout"
    PAPER_NAME = "陕西日报"
