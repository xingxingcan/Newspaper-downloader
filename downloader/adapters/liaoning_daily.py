# -*- coding: utf-8 -*-
"""辽宁日报，来源 epaper.lnd.com.cn"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class LiaoningDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "https://epaper.lnd.com.cn"
    LAYOUT_BASE = "https://epaper.lnd.com.cn/lnrbepaper/pc/layout"
    PAPER_NAME = "辽宁日报"
