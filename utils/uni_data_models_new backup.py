from enum import Enum, auto
from abc import ABC, abstractmethod
from datetime import datetime  # 补充必要的导入
from typing import Optional

# 数据清洗工具函数（修复：增加对空字符串的处理）


def convert_comma_separated_int(value):
    """将带逗号的数字字符串转换为整数，无法转换时返回0"""
    if value == 0 or value == '':
        return 0
    if isinstance(value, str):
        cleaned_value = value.replace(',', '')
        try:
            return int(cleaned_value)
        except ValueError:
            return 0
    return int(value) if value else 0


def convert_comma_separated_float(value):
    """将带逗号的数字字符串转换为浮点数，无法转换时返回0.0"""
    if value == 0 or value == '':
        return 0.0
    if isinstance(value, str):
        cleaned_value = value.replace(',', '')
        try:

            return float(cleaned_value)
        except ValueError:
            return 0.0
    return float(value) if value else 0.0


def convert_percentage(value):
    """将百分比字符串转换为浮点数，无法转换时返回0.0"""
    if value == 0 or value == '':
        return 0.0
    if isinstance(value, str) and value.endswith('%'):
        try:
            return float(value.strip('%')) / 100
        except ValueError:
            return 0.0
    return float(value) if value else 0.0


def convert_roi2_material_upload_time(value):
    if value == "-":
        # return datetime.strptime("2000-01-01 06:05:28", "%Y-%m-%d %H:%M:%S")
        return None
    else:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def convert_material_video_name(value):
    if value == "-":
        return 0
    else:
        return value


class DataTopic(Enum):
    """数据主题枚举类，定义各类数据主题及其描述"""

    #
    SITE_PROMOTION_PRODUCT_AD = "SITE_PROMOTION_PRODUCT_AD"
    SITE_PROMOTION_PRODUCT_PRODUCT = "SITE_PROMOTION_PRODUCT_PRODUCT"
    SITE_PROMOTION_PRODUCT_POST_ASSIST_TASK = "SITE_PROMOTION_PRODUCT_POST_ASSIST_TASK"
    # 直播全域推广-素材
    SITE_PROMOTION_POST_DATA_LIVE = "SITE_PROMOTION_POST_DATA_LIVE"
    SITE_PROMOTION_POST_DATA_VIDEO = "SITE_PROMOTION_POST_DATA_VIDEO"
    SITE_PROMOTION_POST_DATA_OTHER = "SITE_PROMOTION_POST_DATA_OTHER"
    SITE_PROMOTION_POST_DATA_TITLE = "SITE_PROMOTION_POST_DATA_TITLE"

    # 商品全域推广-素材
    SITE_PROMOTION_PRODUCT_POST_DATA_TITLE = "SITE_PROMOTION_PRODUCT_POST_DATA_TITLE"
    SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE = "SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE"
    SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO = "SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO"
    SITE_PROMOTION_PRODUCT_POST_DATA_OTHER = "SITE_PROMOTION_PRODUCT_POST_DATA_OTHER"
    ROI2_IMAGE_AGG_MATERIAL_ANALYSIS = "ROI2_IMAGE_AGG_MATERIAL_ANALYSIS"
    # 中文描述映射
    _descriptions = {
        SITE_PROMOTION_PRODUCT_AD: "商品全域-计划数据",  # 暂时不用
        SITE_PROMOTION_PRODUCT_PRODUCT: "商品全域-商品数据",  # 暂时不用
        SITE_PROMOTION_PRODUCT_POST_ASSIST_TASK: "商品全域-调控数据",  # 暂时不用
        SITE_PROMOTION_POST_DATA_LIVE: "直播全域推广-素材-直播间画面",
        SITE_PROMOTION_POST_DATA_VIDEO: "直播全域推广-素材-视频",
        SITE_PROMOTION_POST_DATA_OTHER: "直播全域推广-素材-其他创意",
        SITE_PROMOTION_POST_DATA_TITLE: "直播全域推广-素材-标题",
        SITE_PROMOTION_PRODUCT_POST_DATA_TITLE: "商品全域推广-素材-标题",
        SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE: "商品全域推广-素材-图片",
        SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO: "商品全域推广-素材-视频",
        SITE_PROMOTION_PRODUCT_POST_DATA_OTHER: "商品全域推广-素材-其他创意",
        ROI2_IMAGE_AGG_MATERIAL_ANALYSIS: "全域数据-素材数据-图文数据"
    }


class SITE_PROMOTION_PRODUCT_AD:
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_AD.value
    pass

# 直播间画面


class SITE_PROMOTION_POST_DATA_LIVE:
    def __init__(self, anchor_id: str, aggregate_smart_bid_type: Optional[str] = "0", ecp_app_id: Optional[str] = "1"):
        self.anchor_id = anchor_id
        self.aggregate_smart_bid_type = aggregate_smart_bid_type
        self.ecp_app_id = ecp_app_id
        self.filters = [
            {"field": "anchor_id", "type": 1,
                "operator": 7, "values": [self.anchor_id]},
            {"field": "aggregate_smart_bid_type",  "operator": 7,
                "values": [aggregate_smart_bid_type]},
            {"field": "ecp_app_id",  "operator": 7, "values": [ecp_app_id]},
        ]

    data_topic = DataTopic.SITE_PROMOTION_POST_DATA_LIVE.value
    dimensions = ["stat_time_day", "anchor_id"]  # 待定
    metrics = [
        "live_show_count_exclude_video_for_roi2", "live_watch_count_exclude_video_for_roi2",
        "total_pay_order_count_for_roi2_fork", "total_pay_order_gmv_include_coupon_for_roi2_fork",
        "stat_cost_for_roi2_fork", "total_prepay_and_pay_order_roi2_fork",
        "total_pay_order_coupon_amount_for_roi2_fork"
    ]
    order_by = [
        {"type": 1, "field": "stat_cost_for_roi2_fork"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        data_list = []
        for row in data.get("rows", {}):
            # dimensions
            stat_time_day = row.get("dimensions", {}).get(
                "stat_time_day", 0).get("ValueStr", 0)
            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            stat_cost = convert_comma_separated_float(metrics.get(
                "stat_cost_for_roi2_fork", 0).get("ValueStr", 0))  # 消耗
            total_pay_order_gmv = convert_comma_separated_float(metrics.get(
                # 整体成交
                "total_pay_order_gmv_include_coupon_for_roi2_fork", 0).get("ValueStr", 0))
            total_pay_order_coupon_amount = convert_comma_separated_float(metrics.get(
                # 优惠劵金额
                "total_pay_order_coupon_amount_for_roi2_fork", 0).get("ValueStr", 0))
            roi = convert_comma_separated_float(metrics.get(
                # ROI
                "total_prepay_and_pay_order_roi2_fork", 0).get("ValueStr", 0))
            show_count = convert_comma_separated_int(metrics.get(
                # 展示次数
                "live_show_count_exclude_video_for_roi2", 0).get("ValueStr", 0))
            click_count = convert_comma_separated_int(metrics.get(
                # 点击次数
                "live_watch_count_exclude_video_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_count = convert_comma_separated_int(metrics.get(
                # 成交订单数
                "total_pay_order_count_for_roi2_fork", 0).get("ValueStr", 0))
            video_play_duration_3s_rate = 0

            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "stat_cost": stat_cost, "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount, "roi": roi,
                "show_count": show_count, "click_count": click_count,
                "total_pay_order_count": total_pay_order_count, "video_play_duration_3s_rate": video_play_duration_3s_rate,
                "material_video_name": "直播间画面"
            }
            data_list.append(model_fields)
        return data_list, total_page


# 直播全域推广-素材-视频
class SITE_PROMOTION_POST_DATA_VIDEO:
    def __init__(self, anchor_id: str, aggregate_smart_bid_type: Optional[str] = "0", ecp_app_id: Optional[str] = "1"):
        self.anchor_id = anchor_id
        self.aggregate_smart_bid_type = aggregate_smart_bid_type
        self.ecp_app_id = ecp_app_id
        self.filters = [
            {"field": "anchor_id", "type": 1,
                "operator": 7, "values": [self.anchor_id]},
            {"field": "aggregate_smart_bid_type",  "operator": 7,
                "values": [aggregate_smart_bid_type]},
            {"field": "ecp_app_id",  "operator": 7, "values": [ecp_app_id]},
        ]

    data_topic = DataTopic.SITE_PROMOTION_POST_DATA_VIDEO.value
    dimensions = [
        "stat_time_day",               #
        "roi2_material_video_type",    #
        "roi2_material_video_name",    #
        "roi2_material_upload_time",   #
        "material_id",                 #
    ]  #
    metrics = [
        "live_show_count_for_roi2_v2",
        "live_watch_count_for_roi2_v2",
        "stat_cost_for_roi2",
        "total_pay_order_count_for_roi2",
        "total_pay_order_gmv_include_coupon_for_roi2",
        "total_prepay_and_pay_order_roi2",
        "video_play_duration_3s_rate_for_roi2",
        "total_pay_order_coupon_amount_for_roi2"
    ]
    order_by = [
        {"type": 1, "field": "stat_cost_for_roi2"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        print(total_page)
        data_list = []
        for row in data.get("rows", {}):
            # dimensions
            dimensionss = row.get("dimensions", {})
            stat_time_day = dimensionss.get(
                "stat_time_day", 0).get("ValueStr", 0)
            roi2_material_video_type = dimensionss.get(
                "roi2_material_video_type", 0).get("ValueStr", 0)
            # roi2_material_upload_time=dimensionss.get("roi2_material_upload_time", 0).get("ValueStr",0)
            material_id = convert_material_video_name(
                dimensionss.get("material_id", 0).get("ValueStr", 0))

            material_video_name = dimensionss.get(
                "roi2_material_video_name", "no_value").get("ValueStr", 0)

            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            stat_cost = convert_comma_separated_float(metrics.get(
                "stat_cost_for_roi2", 0).get("ValueStr", 0))  # 消耗
            total_pay_order_gmv = convert_comma_separated_float(metrics.get(
                # 整体成交
                "total_pay_order_gmv_include_coupon_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_coupon_amount = convert_comma_separated_float(metrics.get(
                # 优惠劵金额
                "total_pay_order_coupon_amount_for_roi2", 0).get("ValueStr", 0))
            roi = convert_comma_separated_float(metrics.get(
                # ROI
                "total_prepay_and_pay_order_roi2", 0).get("ValueStr", 0))
            show_count = convert_comma_separated_int(metrics.get(
                "live_show_count_for_roi2_v2", 0).get("ValueStr", 0))  # 展示次数
            click_count = convert_comma_separated_int(metrics.get(
                "live_watch_count_for_roi2_v2", 0).get("ValueStr", 0))  # 点击次数
            total_pay_order_count = convert_comma_separated_int(metrics.get(
                # 成交订单数
                "total_pay_order_count_for_roi2", 0).get("ValueStr", 0))
            video_play_duration_3s_rate = convert_percentage(metrics.get(
                # 3s播放率
                "video_play_duration_3s_rate_for_roi2", 0).get("ValueStr", 0))
            roi2_material_upload_time = convert_roi2_material_upload_time(
                dimensionss.get("roi2_material_upload_time", 0).get("ValueStr", 0))

            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "stat_cost": stat_cost, "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount, "roi": roi,
                "show_count": show_count, "click_count": click_count,
                "total_pay_order_count": total_pay_order_count, "video_play_duration_3s_rate": video_play_duration_3s_rate,
                "material_id": material_id, "material_video_name": material_video_name,
                "roi2_material_upload_time": roi2_material_upload_time
            }
            data_list.append(model_fields)
            # with open("tests.txt","w",encoding="utf-8") as f:
            #     for data in data_list:
            #         f.write(str(data))
        # 下一步更新数据库增加素材上传时间和素材类型
        return data_list, total_page


# 直播全域推广-素材-其他创意
class SITE_PROMOTION_POST_DATA_OTHER:
    def __init__(self, anchor_id: str, aggregate_smart_bid_type: Optional[str] = "0", ecp_app_id: Optional[str] = "1"):
        self.anchor_id = anchor_id
        self.aggregate_smart_bid_type = aggregate_smart_bid_type
        self.ecp_app_id = ecp_app_id
        self.filters = [
            {"field": "anchor_id", "type": 1,
                "operator": 7, "values": [self.anchor_id]},
            {"field": "aggregate_smart_bid_type",  "operator": 7,
                "values": [aggregate_smart_bid_type]},
            {"field": "ecp_app_id",  "operator": 7, "values": [ecp_app_id]},
        ]
    data_topic = DataTopic.SITE_PROMOTION_POST_DATA_OTHER.value
    dimensions = ["stat_time_day", "roi2_other_creative_name"]  # 待定
    metrics = [
        "total_pay_order_count_for_roi2", "total_pay_order_gmv_include_coupon_for_roi2",
        "total_pay_order_coupon_amount_for_roi2"
    ]
    order_by = [
        {"type": 1, "field": "total_pay_order_count_for_roi2"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        data_list = []
        for row in data.get("rows", {}):
            # dimensions
            dimensionss = row.get("dimensions", {})
            stat_time_day = dimensionss.get(
                "stat_time_day", 0).get("ValueStr", 0)
            material_video_name = dimensionss.get(
                "roi2_other_creative_name", 0).get("ValueStr", 0)
            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            total_pay_order_gmv = convert_comma_separated_float(metrics.get(
                # 整体成交
                "total_pay_order_gmv_include_coupon_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_coupon_amount = convert_comma_separated_float(metrics.get(
                # 优惠劵金额
                "total_pay_order_coupon_amount_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_count = convert_comma_separated_int(metrics.get(
                # 成交订单数
                "total_pay_order_count_for_roi2", 0).get("ValueStr", 0))

            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount,
                "total_pay_order_count": total_pay_order_count,
                "material_video_name": material_video_name
            }
            data_list.append(model_fields)
        return data_list, total_page


# 商品全域推广-素材-视频
class SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO:
    def __init__(self, anchor_id: str, aggregate_smart_bid_type: Optional[str] = "0", ecp_app_id: Optional[str] = "1"):
        self.anchor_id = anchor_id
        self.aggregate_smart_bid_type = aggregate_smart_bid_type
        self.ecp_app_id = ecp_app_id
        self.filters = [
            # {"field": "anchor_id", "type": 1, "operator": 7, "values": [self.anchor_id]},
            # {"field": "aggregate_smart_bid_type",  "operator": 7,"values": [aggregate_smart_bid_type]},
            {"field": "ecp_app_id",  "operator": 7, "values": [ecp_app_id]},
        ]
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO.value
    dimensions = ["stat_time_day", "roi2_material_video_name",
                  "roi2_material_upload_time", "material_id"]
    metrics = [
        "product_show_count_for_roi2", "product_click_count_for_roi2", "stat_cost_for_roi2",
        "total_pay_order_count_for_roi2", "total_pay_order_gmv_include_coupon_for_roi2",
        "total_prepay_and_pay_order_roi2", "video_play_duration_3s_rate_for_roi2",
        "total_pay_order_coupon_amount_for_roi2"
    ]
    order_by = [
        {"type": 1, "field": "stat_cost_for_roi2"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        data_list = []

        for row in data.get("rows", {}):
            # dimensions

            dimensionss = row.get("dimensions", {})
            stat_time_day = dimensionss.get(
                "stat_time_day", 0).get("ValueStr", 0)
            # roi2_material_upload_time=dimensionss.get("roi2_material_upload_time", 0).get("ValueStr",0)
            material_id = convert_material_video_name(
                dimensionss.get("material_id", 0).get("ValueStr", 0))
            # 1. 先获取原始值，默认值设为更合理的空字符串（而非"no_value"，语义更清晰）
            material_video_info = dimensionss.get(
                "roi2_material_video_name", "")

            # 2. 若原始值是字典，取 ValueStr；否则直接使用原始值（含默认值""）
            material_video_name = material_video_info.get("ValueStr", material_video_info) if isinstance(
                material_video_info, dict) else material_video_info

            # material_video_name_raw = dimensionss.get("roi2_material_video_name", "no_value")
            # if material_video_name_raw == "no_value":
            #     material_video_name = material_video_name_raw
            # else :
            #     material_video_name = dimensionss.get("roi2_material_video_name", "no_value").get("ValueStr",0)
            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            stat_cost = convert_comma_separated_float(metrics.get(
                "stat_cost_for_roi2", 0).get("ValueStr", 0))  # 消耗
            total_pay_order_gmv = convert_comma_separated_float(metrics.get(
                # 整体成交
                "total_pay_order_gmv_include_coupon_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_coupon_amount = convert_comma_separated_float(metrics.get(
                # 优惠劵金额
                "total_pay_order_coupon_amount_for_roi2", 0).get("ValueStr", 0))
            roi = convert_comma_separated_float(metrics.get(
                # ROI
                "total_prepay_and_pay_order_roi2", 0).get("ValueStr", 0))
            show_count = convert_comma_separated_int(metrics.get(
                "product_show_count_for_roi2", 0).get("ValueStr", 0))  # 展示次数
            click_count = convert_comma_separated_int(metrics.get(
                "product_click_count_for_roi2", 0).get("ValueStr", 0))  # 点击次数
            total_pay_order_count = convert_comma_separated_int(metrics.get(
                # 成交订单数
                "total_pay_order_count_for_roi2", 0).get("ValueStr", 0))
            video_play_duration_3s_rate = convert_percentage(metrics.get(
                # 3s播放率
                "video_play_duration_3s_rate_for_roi2", 0).get("ValueStr", 0))
            # roi2_material_upload_time=convert_roi2_material_upload_time(dimensionss.get("roi2_material_upload_time", 0).get("ValueStr",0))

            roi2_material_upload_time = convert_roi2_material_upload_time(dimensionss.get("roi2_material_upload_time", 0).get(
                "ValueStr", 0)) if dimensionss.get("roi2_material_upload_time", 0) != 0 else 0
            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "stat_cost": stat_cost, "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount, "roi": roi,
                "show_count": show_count, "click_count": click_count,
                "total_pay_order_count": total_pay_order_count, "video_play_duration_3s_rate": video_play_duration_3s_rate,
                "material_id": material_id, "material_video_name": material_video_name,
                "roi2_material_upload_time": roi2_material_upload_time
            }
            data_list.append(model_fields)
        # 加入素材上传时间
        return data_list, total_page
        # except Exception as e:
        #     return e


# 商品全域推广-素材-图片
class SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE:
    def __init__(self, anchor_id: str, aggregate_smart_bid_type: Optional[str] = "0", ecp_app_id: Optional[str] = "1"):
        self.anchor_id = anchor_id
        self.aggregate_smart_bid_type = aggregate_smart_bid_type
        self.ecp_app_id = ecp_app_id
        self.filters = [
            # {"field": "anchor_id", "type": 1, "operator": 7, "values": [self.anchor_id]},
            # {"field": "aggregate_smart_bid_type",  "operator": 7,"values": [aggregate_smart_bid_type]},
            {"field": "ecp_app_id",  "operator": 7, "values": [ecp_app_id]},
        ]
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE.value
    dimensions = ["stat_time_day", "roi2_material_image_name",
                  "roi2_material_upload_time", "material_id"]
    metrics = [
        "product_show_count_for_roi2", "product_click_count_for_roi2", "stat_cost_for_roi2",
        "total_pay_order_count_for_roi2", "total_pay_order_gmv_include_coupon_for_roi2",
        "total_prepay_and_pay_order_roi2", "total_pay_order_coupon_amount_for_roi2"
    ]
    order_by = [
        {"type": 1, "field": "stat_cost_for_roi2"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        data_list = []
        for row in data.get("rows", {}):
            # dimensions
            dimensionss = row.get("dimensions", {})
            stat_time_day = dimensionss.get(
                "stat_time_day", 0).get("ValueStr", 0)
            material_id = convert_material_video_name(
                dimensionss.get("material_id", 0).get("ValueStr", 0))
            material_video_name = dimensionss.get(
                "roi2_material_image_name", "no_value").get("ValueStr", 0)
            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            stat_cost = convert_comma_separated_float(metrics.get(
                "stat_cost_for_roi2", 0).get("ValueStr", 0))  # 消耗
            total_pay_order_gmv = convert_comma_separated_float(metrics.get(
                # 整体成交
                "total_pay_order_gmv_include_coupon_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_coupon_amount = convert_comma_separated_float(metrics.get(
                # 优惠劵金额
                "total_pay_order_coupon_amount_for_roi2", 0).get("ValueStr", 0))
            roi = convert_comma_separated_float(metrics.get(
                # ROI
                "total_prepay_and_pay_order_roi2", 0).get("ValueStr", 0))
            show_count = convert_comma_separated_int(metrics.get(
                "product_show_count_for_roi2", 0).get("ValueStr", 0))  # 展示次数
            click_count = convert_comma_separated_int(metrics.get(
                "product_click_count_for_roi2", 0).get("ValueStr", 0))  # 点击次数
            total_pay_order_count = convert_comma_separated_int(metrics.get(
                # 成交订单数
                "total_pay_order_count_for_roi2", 0).get("ValueStr", 0))
            # video_play_duration_3s_rate = convert_percentage(metrics.get("video_play_duration_3s_rate_for_roi2", 0).get("ValueStr",0))  # 3s播放率
            roi2_material_upload_time = convert_roi2_material_upload_time(
                dimensionss.get("roi2_material_upload_time", 0).get("ValueStr", 0))

            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "stat_cost": stat_cost, "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount, "roi": roi,
                "show_count": show_count, "click_count": click_count,
                "total_pay_order_count": total_pay_order_count,
                # "video_play_duration_3s_rate": video_play_duration_3s_rate,
                "material_id": material_id, "material_video_name": material_video_name,
                "roi2_material_upload_time": roi2_material_upload_time
            }
            data_list.append(model_fields)
        return data_list, total_page


# 商品全域推广-素材-其他
class SITE_PROMOTION_PRODUCT_POST_DATA_OTHER:
    def __init__(self, anchor_id: str, aggregate_smart_bid_type: Optional[str] = "0", ecp_app_id: Optional[str] = "1"):
        self.anchor_id = anchor_id
        self.aggregate_smart_bid_type = aggregate_smart_bid_type
        self.ecp_app_id = ecp_app_id
        self.filters = [
            # {"field": "anchor_id", "type": 1, "operator": 7, "values": [self.anchor_id]},
            # {"field": "aggregate_smart_bid_type",  "operator": 7,"values": [aggregate_smart_bid_type]},
            {"field": "ecp_app_id",  "operator": 7, "values": [ecp_app_id]},
        ]
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_POST_DATA_OTHER.value
    dimensions = ["stat_time_day", "roi2_other_creative_name"]  # 待定
    metrics = [
        "total_pay_order_count_for_roi2", "total_pay_order_gmv_include_coupon_for_roi2",
        "total_pay_order_coupon_amount_for_roi2"
    ]
    order_by = [
        {"type": 1, "field": "total_pay_order_count_for_roi2"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        data_list = []
        for row in data.get("rows", {}):
            # dimensions
            dimensionss = row.get("dimensions", {})
            stat_time_day = dimensionss.get(
                "stat_time_day", 0).get("ValueStr", 0)
            material_video_name = dimensionss.get(
                "roi2_other_creative_name", 0).get("ValueStr", 0)

            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            total_pay_order_gmv = convert_comma_separated_float(metrics.get(
                # 整体成交
                "total_pay_order_gmv_include_coupon_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_coupon_amount = convert_comma_separated_float(metrics.get(
                # 优惠劵金额
                "total_pay_order_coupon_amount_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_count = convert_comma_separated_int(metrics.get(
                # 成交订单数
                "total_pay_order_count_for_roi2", 0).get("ValueStr", 0))

            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount,
                "total_pay_order_count": total_pay_order_count,
                "material_video_name": material_video_name
            }
            data_list.append(model_fields)
        return data_list, total_page


# 直播全域推广-素材-标题
class SITE_PROMOTION_POST_DATA_TITLE:
    data_topic = DataTopic.SITE_PROMOTION_POST_DATA_TITLE.value
    dimensions = ["stat_time_day", "roi2_other_creative_name"]  # 待定
    metrics = [
        "live_show_count_exclude_video_for_roi2", "live_watch_count_exclude_video_for_roi2",
        "total_pay_order_count_for_roi2_fork", "total_pay_order_gmv_include_coupon_for_roi2_fork",
        "stat_cost_for_roi2_fork", "total_prepay_and_pay_order_roi2_fork",
        "total_pay_order_coupon_amount_for_roi2_fork"
    ]
    order_by = [
        {"type": 1, "field": "stat_cost_for_roi2_fork"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        data_list = []
        for row in data.get("rows", {}):
            # dimensions
            dimensionss = row.get("dimensions", {})
            stat_time_day = dimensionss.get(
                "stat_time_day", 0).get("ValueStr", 0)
            material_video_name = dimensionss.get(
                "roi2_other_creative_name", 0).get("ValueStr", 0)
            # stat_time_day = row.get("dimensions", {}).get("stat_time_day", 0)
            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            stat_cost = convert_comma_separated_float(
                metrics.get("stat_cost_for_roi2_fork", 0))  # 消耗
            total_pay_order_gmv = convert_comma_separated_float(metrics.get(
                "total_pay_order_gmv_include_coupon_for_roi2_fork", 0))  # 整体成交
            total_pay_order_coupon_amount = convert_comma_separated_float(
                # 优惠劵金额
                metrics.get("total_pay_order_coupon_amount_for_roi2_fork", 0))
            roi = convert_comma_separated_float(metrics.get(
                "total_prepay_and_pay_order_roi2_fork", 0))  # ROI
            show_count = convert_comma_separated_int(metrics.get(
                "live_show_count_exclude_video_for_roi2", 0))  # 展示次数
            click_count = convert_comma_separated_int(metrics.get(
                "live_watch_count_exclude_video_for_roi2", 0))  # 点击次数
            total_pay_order_count = convert_comma_separated_int(
                metrics.get("total_pay_order_count_for_roi2_fork", 0))  # 成交订单数

            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "stat_cost": stat_cost, "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount, "roi": roi,
                "show_count": show_count, "click_count": click_count,
                "total_pay_order_count": total_pay_order_count,
                "material_video_name": material_video_name
            }
            data_list.append(model_fields)
        return data_list, total_page


# 商品全域推广-素材-标题
class SITE_PROMOTION_PRODUCT_POST_DATA_TITLE:
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_POST_DATA_TITLE.value
    dimensions = ["stat_time_day"]  # 待定
    metrics = [
        "product_show_count_for_roi2", "product_click_count_for_roi2", "stat_cost_for_roi2",
        "total_pay_order_count_for_roi2", "total_pay_order_gmv_include_coupon_for_roi2",
        "total_prepay_and_pay_order_roi2", "total_pay_order_coupon_amount_for_roi2"
    ]
    order_by = [
        {"type": 1, "field": "stat_cost_for_roi2"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        data_list = []
        for row in data.get("rows", {}):
            # dimensions
            dimensionss = row.get("dimensions", {})
            stat_time_day = dimensionss.get("stat_time_day", 0)
            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            stat_cost = convert_comma_separated_float(
                metrics.get("stat_cost_for_roi2", 0))  # 消耗
            total_pay_order_gmv = convert_comma_separated_float(
                # 整体成交
                metrics.get("total_pay_order_gmv_include_coupon_for_roi2", 0))
            total_pay_order_coupon_amount = convert_comma_separated_float(
                # 优惠劵金额
                metrics.get("total_pay_order_coupon_amount_for_roi2", 0))
            roi = convert_comma_separated_float(metrics.get(
                "total_prepay_and_pay_order_roi2", 0))  # ROI
            show_count = convert_comma_separated_int(
                metrics.get("product_show_count_for_roi2", 0))  # 展示次数
            click_count = convert_comma_separated_int(
                metrics.get("product_click_count_for_roi2", 0))  # 点击次数
            total_pay_order_count = convert_comma_separated_int(
                metrics.get("total_pay_order_count_for_roi2", 0))  # 成交订单数

            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "stat_cost": stat_cost, "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount, "roi": roi,
                "show_count": show_count, "click_count": click_count,
                "total_pay_order_count": total_pay_order_count
            }
            data_list.append(model_fields)
        return data_list, total_page


# 图文素材
class ROI2_IMAGE_AGG_MATERIAL_ANALYSIS:
    def __init__(self, anchor_id: str, aggregate_smart_bid_type: Optional[str] = "0", ecp_app_id: Optional[str] = "1"):
        self.anchor_id = anchor_id
        self.aggregate_smart_bid_type = aggregate_smart_bid_type
        self.ecp_app_id = ecp_app_id
        self.filters = [
            # {"field": "anchor_id", "type": 1, "operator": 7, "values": [self.anchor_id]},
            # {"field": "aggregate_smart_bid_type",  "operator": 7,"values": [aggregate_smart_bid_type]},
            # {"field": "ecp_app_id",  "operator": 7,"values": [ecp_app_id]},
        ]
    data_topic = DataTopic.ROI2_IMAGE_AGG_MATERIAL_ANALYSIS.value
    dimensions = ["stat_time_day", "material_name_v2",
                  "material_create_time_v2", "material_id"]
    metrics = [
        "product_show_count_for_roi2", "product_click_count_for_roi2", "stat_cost_for_roi2",
        "total_pay_order_count_for_roi2", "total_pay_order_gmv_include_coupon_for_roi2",
        "total_prepay_and_pay_order_roi2", "total_pay_order_coupon_amount_for_roi2"
    ]
    order_by = [
        {"type": 1, "field": "stat_cost_for_roi2"}  # 排序字段有效
    ]

    def resolvedata(self, raw_data):
        data = raw_data.get("data", {})
        page = data.get("page_info", {}).get("page", 0)
        total_page = data.get("page_info", {}).get("total_page", 0)
        data_list = []
        for row in data.get("rows", {}):
            # dimensions
            dimensionss = row.get("dimensions", {})
            stat_time_day = dimensionss.get(
                "stat_time_day", 0).get("ValueStr", 0)
            material_id = convert_material_video_name(
                dimensionss.get("material_id", 0).get("ValueStr", 0))
            material_video_name = dimensionss.get(
                "material_name_v2", "no_value").get("ValueStr", 0)
            # metrics
            metrics = row.get("metrics", {})

            # 修复：对数字字段应用清洗函数
            stat_cost = convert_comma_separated_float(metrics.get(
                "stat_cost_for_roi2", 0).get("ValueStr", 0))  # 消耗
            total_pay_order_gmv = convert_comma_separated_float(metrics.get(
                # 整体成交
                "total_pay_order_gmv_include_coupon_for_roi2", 0).get("ValueStr", 0))
            total_pay_order_coupon_amount = convert_comma_separated_float(metrics.get(
                # 优惠劵金额
                "total_pay_order_coupon_amount_for_roi2", 0).get("ValueStr", 0))
            roi = convert_comma_separated_float(metrics.get(
                # ROI
                "total_prepay_and_pay_order_roi2", 0).get("ValueStr", 0))
            show_count = convert_comma_separated_int(metrics.get(
                "product_show_count_for_roi2", 0).get("ValueStr", 0))  # 展示次数
            click_count = convert_comma_separated_int(metrics.get(
                "product_click_count_for_roi2", 0).get("ValueStr", 0))  # 点击次数
            total_pay_order_count = convert_comma_separated_int(metrics.get(
                # 成交订单数
                "total_pay_order_count_for_roi2", 0).get("ValueStr", 0))
            # video_play_duration_3s_rate = convert_percentage(metrics.get("video_play_duration_3s_rate_for_roi2", 0).get("ValueStr",0))  # 3s播放率
            roi2_material_upload_time = convert_roi2_material_upload_time(
                dimensionss.get("material_create_time_v2", 0).get("ValueStr", 0))

            model_fields = {
                "data_topic": self.data_topic, "stat_time_day": stat_time_day,
                "stat_cost": stat_cost, "total_pay_order_gmv": total_pay_order_gmv,
                "total_pay_order_coupon_amount": total_pay_order_coupon_amount, "roi": roi,
                "show_count": show_count, "click_count": click_count,
                "total_pay_order_count": total_pay_order_count,
                # "video_play_duration_3s_rate": video_play_duration_3s_rate,
                "material_id": material_id, "material_video_name": material_video_name,
                "roi2_material_upload_time": roi2_material_upload_time
            }
            data_list.append(model_fields)
        return data_list, total_page
