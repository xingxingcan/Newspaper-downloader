# -*- coding: utf-8 -*-
"""新华日报（江苏），xh.xhby.net/pc/layout/YYYYMM/DD/node_NN.html"""
from downloader.adapters.layout_node_base import LayoutNodeAdapterBase


class XinhuaJiangsuDailyAdapter(LayoutNodeAdapterBase):
    BASE_URL = "http://xh.xhby.net"
    LAYOUT_BASE = "http://xh.xhby.net/pc/layout"
    PAPER_NAME = "新华日报"
