import pandas as pd
import os
# file_path=r"C:\Users\A\Desktop\真不二个人护理旗舰店 商品.xlsx"
def shop_data(file_path):
    if os.path.exists(file_path):
        shop_data=pd.read_excel(file_path,engine='calamine')
    else:
        raise Exception("no thise file")

    chinese_to_english_a ={
                '统计日期': 'stat_date',
                '日期': 'date',
                '商品ID': 'product_id',
                '商品名称': 'product_name',
                '载体类型': 'media_type',
                '账号类型': 'account_type',
                '达人名称': 'influencer_name',
                '抖音号': 'douyin_id',
                '用户支付金额': 'transaction_amount',
                '成交订单数': 'transaction_orders',
                '成交件数': 'transaction_items',
                '成交人数': 'transaction_buyers',
                '千次曝光用户支付金额': 'transaction_amount_per_k_exposure',
                '新客支付金额': 'new_customer_amount',
                '老客支付金额': 'return_customer_amount',
                '新客成交订单数': 'new_customer_orders',
                '老客成交订单数': 'return_customer_orders',
                '新客成交人数': 'new_customer_buyers',
                '老客成交人数': 'return_customer_buyers',
                '商品曝光次数': 'product_exposure_count',
                '商品点击次数': 'product_click_count',
                '商品加购次数': 'product_add_to_cart_count',
                '商品曝光点击率': 'product_click_through_rate',
                '商品点击成交转化率': 'product_conversion_rate',
                '商品曝光人数': 'product_exposure_users',
                '商品点击人数': 'product_click_users',
                '商品加购人数': 'product_add_to_cart_users',
                '商品曝光点击率（人数）': 'product_click_through_rate_users',
                '商品点击成交转化率（人数）': 'product_conversion_rate_users',
                '预售订单数': 'pre_order_count',
                '预售全款金额': 'pre_order_full_payment_amount',
                '退款金额': 'refund_amount',
                '退款订单数': 'refund_orders',
                '退款件数': 'refund_items',
                '退款人数': 'refund_buyers',
                '退款金额（按支付时间计）': 'refund_amount_by_payment_time'
            }
    fill_values_a ={
                '商品ID': 'no_value',
                '商品名称': 'no_value',
                '载体类型': 'no_value',
                '账号类型': 'no_value',
                '达人名称': 'no_value',
                '抖音号': 'no_value',
                '用户支付金额': 0,
                '成交订单数': 0,
                '成交件数': 0,
                '成交人数': 0,
                '千次曝光用户支付金额':0,
                '新客支付金额': 0,
                '老客支付金额': 0,
                '新客成交订单数': 0,
                '老客成交订单数': 0,
                '新客成交人数': 0,
                '老客成交人数': 0,
                '商品曝光次数': 0,
                '商品点击次数': 0,
                '商品加购次数': 0,
                '商品曝光点击率': 0,
                '商品点击成交转化率': 0,
                '商品曝光人数': 0,
                '商品点击人数': 0,
                '商品加购人数': 0,
                '商品曝光点击率（人数）': 0,
                '商品点击成交转化率（人数）': 0,
                '预售订单数': 0,
                '预售全款金额':0,
                '退款金额': 0,
                '退款订单数': 0,
                '退款件数': 0,
                '退款人数': 0,
                '退款金额（按支付时间计）': 0}
    chinese_to_english_b ={
                '统计日期': 'stat_date',
                '日期': 'date',
                '商品ID': 'product_id',
                '商品名称': 'product_name',
                '载体类型': 'media_type',
                '账号类型': 'account_type',
                '达人名称': 'influencer_name',
                '抖音号': 'douyin_id',
                '成交金额': 'transaction_amount',
                '成交订单数': 'transaction_orders',
                '成交件数': 'transaction_items',
                '成交人数': 'transaction_buyers',
                '千次曝光成交金额': 'transaction_amount_per_k_exposure',
                '新客成交金额': 'new_customer_amount',
                '老客成交金额': 'return_customer_amount',
                '新客成交订单数': 'new_customer_orders',
                '老客成交订单数': 'return_customer_orders',
                '新客成交人数': 'new_customer_buyers',
                '老客成交人数': 'return_customer_buyers',
                '商品曝光次数': 'product_exposure_count',
                '商品点击次数': 'product_click_count',
                '商品加购次数': 'product_add_to_cart_count',
                '商品曝光点击率': 'product_click_through_rate',
                '商品点击成交转化率': 'product_conversion_rate',
                '商品曝光人数': 'product_exposure_users',
                '商品点击人数': 'product_click_users',
                '商品加购人数': 'product_add_to_cart_users',
                '商品曝光点击率（人数）': 'product_click_through_rate_users',
                '商品点击成交转化率（人数）': 'product_conversion_rate_users',
                '预售订单数': 'pre_order_count',
                '预售全款金额': 'pre_order_full_payment_amount',
                '退款金额': 'refund_amount',
                '退款订单数': 'refund_orders',
                '退款件数': 'refund_items',
                '退款人数': 'refund_buyers',
                '退款金额（按支付时间计）': 'refund_amount_by_payment_time'
            }
    fill_values_b ={
                '商品ID': 'no_value',
                '商品名称': 'no_value',
                '载体类型': 'no_value',
                '账号类型': 'no_value',
                '达人名称': 'no_value',
                '抖音号': 'no_value',
                '成交金额': 0,
                '成交订单数': 0,
                '成交件数': 0,
                '成交人数': 0,
                '千次曝光成交金额':0,
                '新客成交金额': 0,
                '老客成交金额': 0,
                '新客成交订单数': 0,
                '老客成交订单数': 0,
                '新客成交人数': 0,
                '老客成交人数': 0,
                '商品曝光次数': 0,
                '商品点击次数': 0,
                '商品加购次数': 0,
                '商品曝光点击率': 0,
                '商品点击成交转化率': 0,
                '商品曝光人数': 0,
                '商品点击人数': 0,
                '商品加购人数': 0,
                '商品曝光点击率（人数）': 0,
                '商品点击成交转化率（人数）': 0,
                '预售订单数': 0,
                '预售全款金额':0,
                '退款金额': 0,
                '退款订单数': 0,
                '退款件数': 0,
                '退款人数': 0,
                '退款金额（按支付时间计）': 0}    

    file_except_status=True #默认文件ok
    file_type="A" #默认为a
    for col,value in chinese_to_english_a.items():
        if not col in shop_data.columns:
            file_except_status=False
    if not file_except_status: #如果文件类型A正常自动跳过
        for col,value in chinese_to_english_b.items():
            if not col in shop_data.columns or file_except_status:
                raise Exception("文件错误")
            file_type="B"
                
    #通用转化类型 
    shop_data["日期"]=pd.to_datetime(shop_data["日期"],format='%Y%m%d')
    shop_data["商品ID"]=shop_data["商品ID"].astype(str)
    shop_data["统计日期"]=shop_data["统计日期"].astype(str)
    shop_data["抖音号"]=shop_data["抖音号"].astype(str)
    if file_type=="A":   
        # for col,value in fill_values_a.items():
        #     if col in shop_data.columns:
        #         shop_data[col]=shop_data[col].fillna(value)
        shop_data.fillna(fill_values_a,inplace=True)
        shop_data_new=shop_data.rename(columns=chinese_to_english_a)
    else:
        # for col,value in fill_values_b.items():
        #     if col in shop_data.columns:
        #         shop_data[col]=shop_data[col].fillna(value)
        shop_data.fillna(fill_values_b,inplace=True)
        shop_data_new=shop_data.rename(columns=chinese_to_english_b)        
    # shop_data_new.to_csv("english_shop.csv")
    # print(shop_data_new.to_dict(orient="records"))
 
    print(file_path,file_type)
    # print(shop_data_new.head(1))
    return shop_data_new.to_dict(orient="records")

if __name__ == '__main__':
    # data = get_access_token()
    # print(data)   
    # pass
    file_path=r"C:\Users\Administrator\Downloads\真不二官方旗舰店 账号 商品20250801-20250803 09_36_23.xlsx"
    shop_data(file_path)