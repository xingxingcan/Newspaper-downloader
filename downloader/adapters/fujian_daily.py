# -*- coding: utf-8 -*-
"""福建日报，pc/col/YYYYMM/DD/node_NN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class FujianDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "https://fjrb.fjdaily.com"
    LAYOUT_BASE = "https://fjrb.fjdaily.com/pc/col"
    PAPER_NAME = "福建日报"
