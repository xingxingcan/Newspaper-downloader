# -*- coding: utf-8 -*-
"""吉林日报，来源 jlrbszb.dajilin.com"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class JilinDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "http://jlrbszb.dajilin.com"
    LAYOUT_BASE = "http://jlrbszb.dajilin.com/pc/paper/layout"
    PAPER_NAME = "吉林日报"
