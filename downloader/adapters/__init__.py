# -*- coding: utf-8 -*-
"""
报纸下载适配器
根据报纸 ID 返回对应的适配器实例
"""

from config.newspaper_sources import NEWSPAPER_SOURCES
from .people_daily import PeopleDailyAdapter
from .economic_daily import EconomicDailyAdapter
from .cet_times import CETimesAdapter
from .ctnews import CTNewsAdapter
from .ccmapp import CCMAppAdapter
from .guangming import GuangmingAdapter
from .xinhua import XinhuaAdapter
from .beijing_daily import BeijingDailyAdapter
from .tianjin_daily import TianjinDailyAdapter
from .chongqing_daily import ChongqingDailyAdapter
from .hebei_daily import HebeiDailyAdapter
from .shanxi_daily import ShanxiDailyAdapter
from .inner_mongolia_daily import InnerMongoliaDailyAdapter
from .dazhong_daily import DazhongDailyAdapter
from .heilongjiang_daily import HeilongjiangDailyAdapter
from .jilin_daily import JilinDailyAdapter
from .liaoning_daily import LiaoningDailyAdapter
from .anhui_daily import AnhuiDailyAdapter
from .henan_daily import HenanDailyAdapter
from .hubei_daily import HubeiDailyAdapter
from .zhejiang_daily import ZhejiangDailyAdapter
from .southern_daily import SouthernDailyAdapter
from .fujian_daily import FujianDailyAdapter
from .gansu_daily import GansuDailyAdapter
from .ningxia_daily import NingxiaDailyAdapter
from .hunan_daily import HunanDailyAdapter
from .guizhou_daily import GuizhouDailyAdapter
from .shaanxi_daily import ShaanxiDailyAdapter
from .jiangxi_daily import JiangxiDailyAdapter
from .xizang_daily import XizangDailyAdapter
from .sichuan_daily import SichuanDailyAdapter
from .hainan_daily import HainanDailyAdapter
from .bingtuan_daily import BingtuanDailyAdapter
from .guangxi_daily import GuangxiDailyAdapter
from .xinhua_jiangsu_daily import XinhuaJiangsuDailyAdapter
from .wenhui_daily import WenhuiDailyAdapter
from .qinghai_daily import QinghaiDailyAdapter
from .yunnan_daily import YunnanDailyAdapter
from .xinjiang_daily import XinjiangDailyAdapter
from .stub import StubAdapter

# 适配器类映射
ADAPTER_MAP = {
    "PeopleDailyAdapter": PeopleDailyAdapter,
    "EconomicDailyAdapter": EconomicDailyAdapter,
    "CETimesAdapter": CETimesAdapter,
    "CTNewsAdapter": CTNewsAdapter,
    "CCMAppAdapter": CCMAppAdapter,
    "GuangmingAdapter": GuangmingAdapter,
    "XinhuaAdapter": XinhuaAdapter,
    "BeijingDailyAdapter": BeijingDailyAdapter,
    "TianjinDailyAdapter": TianjinDailyAdapter,
    "ChongqingDailyAdapter": ChongqingDailyAdapter,
    "HebeiDailyAdapter": HebeiDailyAdapter,
    "ShanxiDailyAdapter": ShanxiDailyAdapter,
    "InnerMongoliaDailyAdapter": InnerMongoliaDailyAdapter,
    "DazhongDailyAdapter": DazhongDailyAdapter,
    "HeilongjiangDailyAdapter": HeilongjiangDailyAdapter,
    "JilinDailyAdapter": JilinDailyAdapter,
    "LiaoningDailyAdapter": LiaoningDailyAdapter,
    "AnhuiDailyAdapter": AnhuiDailyAdapter,
    "HenanDailyAdapter": HenanDailyAdapter,
    "HubeiDailyAdapter": HubeiDailyAdapter,
    "ZhejiangDailyAdapter": ZhejiangDailyAdapter,
    "SouthernDailyAdapter": SouthernDailyAdapter,
    "FujianDailyAdapter": FujianDailyAdapter,
    "GansuDailyAdapter": GansuDailyAdapter,
    "NingxiaDailyAdapter": NingxiaDailyAdapter,
    "HunanDailyAdapter": HunanDailyAdapter,
    "GuizhouDailyAdapter": GuizhouDailyAdapter,
    "ShaanxiDailyAdapter": ShaanxiDailyAdapter,
    "JiangxiDailyAdapter": JiangxiDailyAdapter,
    "XizangDailyAdapter": XizangDailyAdapter,
    "SichuanDailyAdapter": SichuanDailyAdapter,
    "HainanDailyAdapter": HainanDailyAdapter,
    "BingtuanDailyAdapter": BingtuanDailyAdapter,
    "GuangxiDailyAdapter": GuangxiDailyAdapter,
    "XinhuaJiangsuDailyAdapter": XinhuaJiangsuDailyAdapter,
    "WenhuiDailyAdapter": WenhuiDailyAdapter,
    "QinghaiDailyAdapter": QinghaiDailyAdapter,
    "YunnanDailyAdapter": YunnanDailyAdapter,
    "XinjiangDailyAdapter": XinjiangDailyAdapter,
    "GlobalTimesAdapter": StubAdapter,
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
