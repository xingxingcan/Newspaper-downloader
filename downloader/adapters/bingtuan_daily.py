# -*- coding: utf-8 -*-
"""兵团日报，pc/layout/YYYYMM/DD/node_NN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class BingtuanDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "http://epaper.bingtuannet.com"
    LAYOUT_BASE = "http://epaper.bingtuannet.com/pc/layout"
    PAPER_NAME = "兵团日报"
