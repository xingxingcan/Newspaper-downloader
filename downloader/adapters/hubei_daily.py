# -*- coding: utf-8 -*-
"""湖北日报，pc/column/YYYYMM/DD/node_NN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class HubeiDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "https://epaper.hubeidaily.net"
    LAYOUT_BASE = "https://epaper.hubeidaily.net/pc/column"
    PAPER_NAME = "湖北日报"
