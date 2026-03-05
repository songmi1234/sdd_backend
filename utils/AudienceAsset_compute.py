import pandas as pd
import os

def rename_columns(col_name):
    if "本品牌" in col_name and "资产" in col_name:
        return "本品牌人群资产"
    elif "对比品牌" in col_name and "资产" in col_name:
        return "对比品牌人群资产均值"
    else:
        return col_name  # 不满足条件的列名保持不变
def audience_assets_compute(file_path):
    file_data=pd.read_csv(file_path)
    type_map={"A1":"A1人群","A2":"A2人群","A3":"A3人群","A4":"A4人群","A5":"A5人群","人群总资产":"人群总资产"}
    for key,value in type_map.items():
        if key in os.path.basename(file_path):
            file_data["audience_type"]=type_map[key]
    # file_data["audience_type"]=os.path.basename(file_path)
    file_data.rename(columns=rename_columns,inplace=True) #特定列修改统一
    column_mapping_snake = {
        "日期": "date",
        "本品牌人群资产": "our_brand_audience_assets",
        "本品牌日新增": "our_brand_daily_new",
        "本品牌日流失": "our_brand_daily_loss",
        "对比品牌人群资产均值": "competitor_avg_audience_assets",
        "对比品牌均值日新增": "competitor_avg_daily_new",
        "对比品牌均值日流失": "competitor_avg_daily_loss"
    }
    file_data.rename(columns=column_mapping_snake,inplace=True)
    # print(file_data.head(2))
    # file_data.to_csv("xxx1.csv")
    return file_data.to_dict(orient="records")