# -*- coding: utf-8 -*-
"""
报纸下载适配器
根据报纸 ID 返回对应的适配器实例
"""

from config.newspaper_sources import NEWSPAPER_SOURCES
from .people_daily import PeopleDailyAdapter
from .stub import StubAdapter

# 适配器类映射
ADAPTER_MAP = {
    "PeopleDailyAdapter": PeopleDailyAdapter,
    "XinhuaAdapter": StubAdapter,
    "GlobalTimesAdapter": StubAdapter,
    "GuangmingAdapter": StubAdapter,
    "EconomicDailyAdapter": StubAdapter,
}


def get_adapter(newspaper_id: str, newspaper_name: str, adapter_class: str):
    """
    获取报纸下载适配器实例
    :param newspaper_id: 报纸 ID
    :param newspaper_name: 报纸名称
    :param adapter_class: 适配器类名
    :return: 适配器实例
    """
    cls = ADAPTER_MAP.get(adapter_class, StubAdapter)
    return cls(newspaper_id, newspaper_name)
