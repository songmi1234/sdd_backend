import pandas as pd
import numpy as np
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any

# --- 核心枚举 ---


class DataTopic(Enum):
    SITE_PROMOTION_PRODUCT_AD = "SITE_PROMOTION_PRODUCT_AD"
    SITE_PROMOTION_PRODUCT_PRODUCT = "SITE_PROMOTION_PRODUCT_PRODUCT"
    SITE_PROMOTION_PRODUCT_POST_ASSIST_TASK = "SITE_PROMOTION_PRODUCT_POST_ASSIST_TASK"
    SITE_PROMOTION_POST_DATA_LIVE = "SITE_PROMOTION_POST_DATA_LIVE"
    SITE_PROMOTION_POST_DATA_VIDEO = "SITE_PROMOTION_POST_DATA_VIDEO"
    SITE_PROMOTION_POST_DATA_OTHER = "SITE_PROMOTION_POST_DATA_OTHER"
    SITE_PROMOTION_POST_DATA_TITLE = "SITE_PROMOTION_POST_DATA_TITLE"
    SITE_PROMOTION_PRODUCT_POST_DATA_TITLE = "SITE_PROMOTION_PRODUCT_POST_DATA_TITLE"
    SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE = "SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE"
    SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO = "SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO"
    SITE_PROMOTION_PRODUCT_POST_DATA_OTHER = "SITE_PROMOTION_PRODUCT_POST_DATA_OTHER"
    ROI2_IMAGE_AGG_MATERIAL_ANALYSIS = "ROI2_IMAGE_AGG_MATERIAL_ANALYSIS"

# --- 真正的 Pandas 重构基类 ---


class BaseDataResolver:
    data_topic: str = ""
    dimensions: List[str] = []
    metrics: List[str] = []
    order_by: List[Dict] = []
    field_map: Dict[str, Tuple[str, str]] = {}

    def __init__(self, anchor_id: str, aggregate_smart_bid_type: Optional[str] = "0", ecp_app_id: Optional[str] = "1"):
        self.anchor_id = anchor_id
        self.aggregate_smart_bid_type = aggregate_smart_bid_type
        self.ecp_app_id = ecp_app_id
        self.filters = [
            {"field": "anchor_id", "type": 1,
                "operator": 7, "values": [self.anchor_id]},
            {"field": "aggregate_smart_bid_type", "operator": 7,
                "values": [self.aggregate_smart_bid_type]},
            {"field": "ecp_app_id", "operator": 7,
                "values": [self.ecp_app_id]},
        ]

    def resolvedata(self, raw_data: Dict) -> Tuple[List[Dict], int]:
        """完全基于 Pandas 向量化的数据解析逻辑"""
        data_json = raw_data.get("data", {})
        rows = data_json.get("rows", [])
        total_page = data_json.get("page_info", {}).get("total_page", 0)
        # import json
        # with open('test.json', 'w', encoding='utf-8') as f:
        #     json.dump(raw_data, f, ensure_ascii=False, indent=2)
        if not rows:
            return [], total_page

        # 1. 向量化打平 JSON
        df_raw = pd.json_normalize(rows)
        df = pd.DataFrame()
        # df_raw.to_csv('1x.csv')
        # 2. 批量字段映射
        for target, (cat, source) in self.field_map.items():
            path = f"{cat}.{source}.ValueStr"
            df[target] = df_raw[path] if path in df_raw.columns else np.nan
            # else np.nan	结果 B	如果表头里没这个名字，就给这一整列填上 NaN (Not a Number，即空值)。
        # df.to_csv('x.csv')
        # 3. 向量化清洗：处理 material_id (强制字符串，防止大数字科学计数法)
        if 'material_id' in df.columns:
            df['material_id'] = df['material_id'].astype(
                str).replace(['nan', 'None', '-'], '0')

        # 4. 向量化清洗：处理数字（带逗号和百分比）
        # 排除掉不需要转数字的列
        exclude_cols = ['stat_time_day', 'material_video_name',
                        'roi2_material_upload_time', 'material_id']
        numeric_cols = [c for c in df.columns if c not in exclude_cols]

        for col in numeric_cols:
            if df[col].dtype == 'object':
                # 处理百分比
                mask = df[col].astype(str).str.contains('%', na=False)
                df.loc[mask, col] = df.loc[mask, col].astype(
                    str).str.replace('%', '').astype(float) / 100
                # 处理逗号
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 5. 向量化时间转换 (这步会产生 pd.NaT)
        if 'roi2_material_upload_time' in df.columns:
            df['roi2_material_upload_time'] = pd.to_datetime(
                df['roi2_material_upload_time'], errors='coerce')

        # 6. 核心修复：彻底消灭 NaT 和 NaN (适配 Tortoise ORM)
        # 我们不能直接 to_dict，因为 Pandas 的 Timestamp 和 NaT 依然在里面
        # 必须转回 Python 原生对象
        def sanitize_val(v, key):
            # 处理 Pandas 的缺失值 (NaN, NaT)
            if pd.isna(v):
                if key == "material_video_name":
                    return ""  # 非空字符串字段兜底
                if "time" in key:
                    return None               # 时间字段必须给 None
                return 0                                   # 数值字段给 0

            # 处理 Pandas 的 Timestamp 对象转回 Python 原生 datetime
            if isinstance(v, pd.Timestamp):
                return v.to_pydatetime()

            return v

        # 先转字典，再进行一次深度清洗以确保 ORM 兼容
        records = df.to_dict(orient='records')
        final_list = []
        for row in records:
            cleaned_row = {k: sanitize_val(v, k) for k, v in row.items()}
            cleaned_row['data_topic'] = self.data_topic
            # 如果 material_video_name 还是 None (因为 map 里没定义)，强制给空串
            if cleaned_row.get('material_video_name') is None:
                cleaned_row['material_video_name'] = ""
            final_list.append(cleaned_row)

        return final_list, total_page

# --- 子类定义 (补全所有属性，解决 AttributeError) ---


class SITE_PROMOTION_PRODUCT_AD:
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_AD.value
    dimensions, metrics, order_by = [], [], []
    def __init__(self, *args, **kwargs): self.filters = []


class SITE_PROMOTION_POST_DATA_LIVE(BaseDataResolver):
    data_topic = DataTopic.SITE_PROMOTION_POST_DATA_LIVE.value
    dimensions = ["stat_time_day", "anchor_id"]
    metrics = ["live_show_count_exclude_video_for_roi2", "live_watch_count_exclude_video_for_roi2", "total_pay_order_count_for_roi2_fork",
               "total_pay_order_gmv_include_coupon_for_roi2_fork", "stat_cost_for_roi2_fork", "total_prepay_and_pay_order_roi2_fork", "total_pay_order_coupon_amount_for_roi2_fork"]
    order_by = [{"type": 1, "field": "stat_cost_for_roi2_fork"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "stat_cost": ("metrics", "stat_cost_for_roi2_fork"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2_fork"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2_fork"),
        "roi": ("metrics", "total_prepay_and_pay_order_roi2_fork"),
        "show_count": ("metrics", "live_show_count_exclude_video_for_roi2"),
        "click_count": ("metrics", "live_watch_count_exclude_video_for_roi2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2_fork"),
    }

    def resolvedata(self, raw_data: Dict):
        res, total = super().resolvedata(raw_data)
        for r in res:
            r['material_video_name'] = "直播间画面"
        return res, total


class SITE_PROMOTION_POST_DATA_VIDEO(BaseDataResolver):
    data_topic = DataTopic.SITE_PROMOTION_POST_DATA_VIDEO.value
    dimensions = ["stat_time_day", "roi2_material_video_type",
                  "roi2_material_video_name", "roi2_material_upload_time", "material_id"]
    metrics = ["live_show_count_for_roi2_v2", "live_watch_count_for_roi2_v2", "stat_cost_for_roi2", "total_pay_order_count_for_roi2",
               "total_pay_order_gmv_include_coupon_for_roi2", "total_prepay_and_pay_order_roi2", "video_play_duration_3s_rate_for_roi2", "total_pay_order_coupon_amount_for_roi2"]
    order_by = [{"type": 1, "field": "stat_cost_for_roi2"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "material_id": ("dimensions", "material_id"),
        "material_video_name": ("dimensions", "roi2_material_video_name"),
        "roi2_material_upload_time": ("dimensions", "roi2_material_upload_time"),
        "stat_cost": ("metrics", "stat_cost_for_roi2"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2"),
        "roi": ("metrics", "total_prepay_and_pay_order_roi2"),
        "show_count": ("metrics", "live_show_count_for_roi2_v2"),
        "click_count": ("metrics", "live_watch_count_for_roi2_v2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2"),
        "video_play_duration_3s_rate": ("metrics", "video_play_duration_3s_rate_for_roi2"),
    }


class SITE_PROMOTION_POST_DATA_OTHER(BaseDataResolver):
    data_topic = DataTopic.SITE_PROMOTION_POST_DATA_OTHER.value
    dimensions = ["stat_time_day", "roi2_other_creative_name"]
    metrics = ["total_pay_order_count_for_roi2",
               "total_pay_order_gmv_include_coupon_for_roi2", "total_pay_order_coupon_amount_for_roi2"]
    order_by = [{"type": 1, "field": "total_pay_order_count_for_roi2"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "material_video_name": ("dimensions", "roi2_other_creative_name"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2"),
    }


class SITE_PROMOTION_POST_DATA_TITLE(BaseDataResolver):
    data_topic = DataTopic.SITE_PROMOTION_POST_DATA_TITLE.value
    dimensions = ["stat_time_day", "roi2_other_creative_name"]
    metrics = ["live_show_count_exclude_video_for_roi2", "live_watch_count_exclude_video_for_roi2", "total_pay_order_count_for_roi2_fork",
               "total_pay_order_gmv_include_coupon_for_roi2_fork", "stat_cost_for_roi2_fork", "total_prepay_and_pay_order_roi2_fork", "total_pay_order_coupon_amount_for_roi2_fork"]
    order_by = [{"type": 1, "field": "stat_cost_for_roi2_fork"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "material_video_name": ("dimensions", "roi2_other_creative_name"),
        "stat_cost": ("metrics", "stat_cost_for_roi2_fork"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2_fork"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2_fork"),
        "roi": ("metrics", "total_prepay_and_pay_order_roi2_fork"),
        "show_count": ("metrics", "live_show_count_exclude_video_for_roi2"),
        "click_count": ("metrics", "live_watch_count_exclude_video_for_roi2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2_fork"),
    }


class SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO(BaseDataResolver):
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_POST_DATA_VIDEO.value
    dimensions = ["stat_time_day", "roi2_material_video_name",
                  "roi2_material_upload_time", "material_id"]
    metrics = ["product_show_count_for_roi2", "product_click_count_for_roi2", "stat_cost_for_roi2", "total_pay_order_count_for_roi2",
               "total_pay_order_gmv_include_coupon_for_roi2", "total_prepay_and_pay_order_roi2", "video_play_duration_3s_rate_for_roi2", "total_pay_order_coupon_amount_for_roi2"]
    order_by = [{"type": 1, "field": "stat_cost_for_roi2"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "material_id": ("dimensions", "material_id"),
        "material_video_name": ("dimensions", "roi2_material_video_name"),
        "roi2_material_upload_time": ("dimensions", "roi2_material_upload_time"),
        "stat_cost": ("metrics", "stat_cost_for_roi2"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2"),
        "roi": ("metrics", "total_prepay_and_pay_order_roi2"),
        "show_count": ("metrics", "product_show_count_for_roi2"),
        "click_count": ("metrics", "product_click_count_for_roi2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2"),
        "video_play_duration_3s_rate": ("metrics", "video_play_duration_3s_rate_for_roi2"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters = [{"field": "ecp_app_id",
                         "operator": 7, "values": [self.ecp_app_id]}]


class SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE(BaseDataResolver):
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_POST_DATA_IMAGE.value
    dimensions = ["stat_time_day", "roi2_material_image_name",
                  "roi2_material_upload_time", "material_id"]
    metrics = ["product_show_count_for_roi2", "product_click_count_for_roi2", "stat_cost_for_roi2", "total_pay_order_count_for_roi2",
               "total_pay_order_gmv_include_coupon_for_roi2", "total_prepay_and_pay_order_roi2", "total_pay_order_coupon_amount_for_roi2"]
    order_by = [{"type": 1, "field": "stat_cost_for_roi2"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "material_id": ("dimensions", "material_id"),
        "material_video_name": ("dimensions", "roi2_material_image_name"),
        "roi2_material_upload_time": ("dimensions", "roi2_material_upload_time"),
        "stat_cost": ("metrics", "stat_cost_for_roi2"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2"),
        "roi": ("metrics", "total_prepay_and_pay_order_roi2"),
        "show_count": ("metrics", "product_show_count_for_roi2"),
        "click_count": ("metrics", "product_click_count_for_roi2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters = [{"field": "ecp_app_id",
                         "operator": 7, "values": [self.ecp_app_id]}]


class SITE_PROMOTION_PRODUCT_POST_DATA_OTHER(BaseDataResolver):
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_POST_DATA_OTHER.value
    dimensions = ["stat_time_day", "roi2_other_creative_name"]
    metrics = ["total_pay_order_count_for_roi2",
               "total_pay_order_gmv_include_coupon_for_roi2", "total_pay_order_coupon_amount_for_roi2"]
    order_by = [{"type": 1, "field": "total_pay_order_count_for_roi2"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "material_video_name": ("dimensions", "roi2_other_creative_name"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters = [{"field": "ecp_app_id",
                         "operator": 7, "values": [self.ecp_app_id]}]


class SITE_PROMOTION_PRODUCT_POST_DATA_TITLE(BaseDataResolver):
    data_topic = DataTopic.SITE_PROMOTION_PRODUCT_POST_DATA_TITLE.value
    dimensions = ["stat_time_day"]
    metrics = ["product_show_count_for_roi2", "product_click_count_for_roi2", "stat_cost_for_roi2", "total_pay_order_count_for_roi2",
               "total_pay_order_gmv_include_coupon_for_roi2", "total_prepay_and_pay_order_roi2", "total_pay_order_coupon_amount_for_roi2"]
    order_by = [{"type": 1, "field": "stat_cost_for_roi2"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "stat_cost": ("metrics", "stat_cost_for_roi2"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2"),
        "roi": ("metrics", "total_prepay_and_pay_order_roi2"),
        "show_count": ("metrics", "product_show_count_for_roi2"),
        "click_count": ("metrics", "product_click_count_for_roi2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2"),
    }


class ROI2_IMAGE_AGG_MATERIAL_ANALYSIS(BaseDataResolver):
    data_topic = DataTopic.ROI2_IMAGE_AGG_MATERIAL_ANALYSIS.value
    dimensions = ["stat_time_day", "material_name_v2",
                  "material_create_time_v2", "material_id"]
    metrics = ["product_show_count_for_roi2", "product_click_count_for_roi2", "stat_cost_for_roi2", "total_pay_order_count_for_roi2",
               "total_pay_order_gmv_include_coupon_for_roi2", "total_prepay_and_pay_order_roi2", "total_pay_order_coupon_amount_for_roi2"]
    order_by = [{"type": 1, "field": "stat_cost_for_roi2"}]
    field_map = {
        "stat_time_day": ("dimensions", "stat_time_day"),
        "material_id": ("dimensions", "material_id"),
        "material_video_name": ("dimensions", "material_name_v2"),
        "roi2_material_upload_time": ("dimensions", "material_create_time_v2"),
        "stat_cost": ("metrics", "stat_cost_for_roi2"),
        "total_pay_order_gmv": ("metrics", "total_pay_order_gmv_include_coupon_for_roi2"),
        "total_pay_order_coupon_amount": ("metrics", "total_pay_order_coupon_amount_for_roi2"),
        "roi": ("metrics", "total_prepay_and_pay_order_roi2"),
        "show_count": ("metrics", "product_show_count_for_roi2"),
        "click_count": ("metrics", "product_click_count_for_roi2"),
        "total_pay_order_count": ("metrics", "total_pay_order_count_for_roi2"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters = []
