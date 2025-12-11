import time
import json

# 导入独立的爬虫文件（确保文件在同一目录）
from xianyu_crawler import XianyuPriceOnly  # 闲鱼爬虫独立文件
from jd_crawler_new import get_jd_prices_simple  # 京东爬虫独立文件

# 导入真实数据库操作文件（关键：使用你的db_operation.py）
from db_operation import (
    init_db, 
    save_camera_price_by_brand, 
    query_price_by_brand,
    BRAND_TABLES,
    get_brand_by_model
)

# 配置需要爬取的相机列表
CAMERA_CONFIGS = {
    "佳能": [
        {"model": "佳能80d", "min_price": 1000, "max_price": 20000},

    ],
    "尼康": [
        {"model": "尼康z6", "min_price": 2000, "max_price": 30000},
        {"model": "尼康d850", "min_price": 4000, "max_price": 28000},
        {"model": "尼康z7ii", "min_price": 6000, "max_price": 35000},
    ],
    "索尼": [
        {"model": "索尼a7m4", "min_price": 5000, "max_price": 15000},
        {"model": "索尼a6400", "min_price": 2000, "max_price": 8000},
        {"model": "索尼a7s3", "min_price": 10000, "max_price": 40000},
    ],
    "富士": [
        {"model": "富士xt5", "min_price": 4000, "max_price": 12000},
        {"model": "富士xs20", "min_price": 3000, "max_price": 10000},
        {"model": "富士xt4", "min_price": 3500, "max_price": 11000},
    ]
}

# 全局变量：数据写入模式（新增/替换）
WRITE_MODE = "add"  # 默认新增模式

def get_middle_three_prices(prices):
    """从价格列表中筛选中间3个价格（排序后取中间）"""
    unique_prices = sorted(list(set(prices)))  # 去重+排序
    price_count = len(unique_prices)
    
    if price_count <= 3:
        return unique_prices
    else:
        middle_idx = price_count // 2
        start_idx = max(0, middle_idx - 1)
        end_idx = min(price_count, middle_idx + 2)
        return unique_prices[start_idx:end_idx]

def run_xianyu_crawler(model, min_price, max_price):
    """调用闲鱼爬虫，返回中间3个价格"""
    xianyu = XianyuPriceOnly()
    xianyu.keyword = model
    xianyu.min_price = min_price
    xianyu.max_price = max_price
    xianyu.run(need_login=False)  # 首次运行改为True，后续False
    
    # 打印价格筛选结果（增强日志）
    print(f"\n===== 【{model}】价格筛选结果 =====")
    print(f"筛选区间：{min_price} - {max_price} 元")
    print(f"符合条件的价格：{xianyu.filtered_prices}")
    print(f"总计：{len(xianyu.filtered_prices)} 个价格")
    
    middle_prices = get_middle_three_prices(xianyu.filtered_prices)
    print(f"  闲鱼原始价格({len(xianyu.filtered_prices)}个): {xianyu.filtered_prices}")
    print(f"  闲鱼中间3个价格: {middle_prices}")
    return middle_prices

def run_jd_crawler(model, min_price, max_price):
    """调用京东爬虫（独立文件），返回中间3个价格"""
    try:
        print("⏳ 正在加载【{}】京东搜索结果...".format(model))
        # 调用京东爬虫的简化函数（传递完整参数）
        jd_prices_raw = get_jd_prices_simple(
            keyword=model,
            min_price=min_price,
            max_price=max_price,
            max_count=30,
            need_login=False
        )
        print("🔍 找到 {} 个首屏商品，开始提取价格...".format(len(jd_prices_raw)))
        
        # 过滤并转换为浮点数
        jd_prices = []
        for p in jd_prices_raw:
            try:
                jd_prices.append(float(p))
            except (ValueError, TypeError):
                continue
        
        # 获取中间3个价格
        middle_prices = get_middle_three_prices(jd_prices)
        print(f"  京东原始价格({len(jd_prices)}个): {jd_prices}")
        print(f"  京东中间3个价格: {middle_prices}")
        return middle_prices
    except Exception as e:
        print(f"❌ 京东爬虫调用失败：{str(e)}")
        return []

def save_price_data(model, xianyu_prices, jd_prices):
    """根据选择的模式保存/更新数据"""
    # 提取品牌（从型号中匹配）
    brand = get_brand_by_model(model)
    
    if WRITE_MODE == "add":
        # 新增模式：调用db_operation中的真实保存函数
        save_camera_price_by_brand(model, xianyu_prices, jd_prices)
    else:
        # 替换模式：先删除该型号旧数据，再插入新数据（实现替换效果）
        import pymysql
        from db_operation import MYSQL_CONFIG, BRAND_TABLES
        
        conn = None
        cursor = None
        try:
            # 1. 连接数据库
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            table_name = BRAND_TABLES[brand]
            
            # 2. 删除该型号旧数据
            delete_sql = f"DELETE FROM {table_name} WHERE camera_model = %s"
            cursor.execute(delete_sql, (model,))
            conn.commit()
            print(f"🗑️  已删除【{brand}-{model}】历史数据")
            
            # 3. 插入新数据（调用原有保存函数）
            save_camera_price_by_brand(model, xianyu_prices, jd_prices)
            print(f"💾 【替换模式】更新【{brand}-{model}】最新价格：")
            print(f"   新闲鱼价格：{xianyu_prices}")
            print(f"   新京东价格：{jd_prices}")
            
        except Exception as e:
            print(f"❌ 替换模式更新失败：{e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def crawl_single_model(config):
    """爬取单个相机型号"""
    model = config["model"]
    min_price = config["min_price"]
    max_price = config["max_price"]
    
    print(f"\n📷 开始爬取 {model} (模式：{WRITE_MODE})")
    # 爬取闲鱼价格
    xianyu_prices = run_xianyu_crawler(model, min_price, max_price)
    # 爬取京东价格
    jd_prices = run_jd_crawler(model, min_price, max_price)
    # 保存/更新数据（真实写入数据库）
    save_price_data(model, xianyu_prices, jd_prices)
    # 防反爬延迟
    time.sleep(3)

def crawl_by_brand(brand):
    """爬取指定品牌的所有型号"""
    if brand not in CAMERA_CONFIGS:
        print(f"❌ 品牌{brand}不存在！可选品牌：{list(CAMERA_CONFIGS.keys())}")
        return
    
    print(f"\n========== 开始爬取【{brand}】品牌 (模式：{WRITE_MODE}) ==========")
    for config in CAMERA_CONFIGS[brand]:
        crawl_single_model(config)
    print(f"✅ 【{brand}】品牌爬取完成！")

def crawl_all_brands():
    """爬取所有品牌的所有型号（一键爬取）"""
    print(f"========== 开始爬取所有品牌相机 (模式：{WRITE_MODE}) ==========")
    for brand in CAMERA_CONFIGS.keys():
        crawl_by_brand(brand)
        time.sleep(5)  # 品牌间增加延迟，降低反爬风险
    print("\n🎉 所有品牌爬取完成！")

def choose_write_mode():
    """选择数据写入模式"""
    global WRITE_MODE
    print("\n===== 选择数据写入模式 =====")
    print("1. 新增模式（保留历史数据，新增一条最新记录）")
    print("2. 替换模式（删除旧数据，只保留最新一条）")
    
    while True:
        mode_choice = input("请选择模式（1/2）：").strip()
        if mode_choice == "1":
            WRITE_MODE = "add"
            print(f"✅ 已选择【新增模式】")
            break
        elif mode_choice == "2":
            WRITE_MODE = "replace"
            print(f"✅ 已选择【替换模式】")
            break
        else:
            print("❌ 输入错误，请输入1或2")

def main_control():
    """核心控制函数 - 交互式选择爬取方式（新增模式选择）"""
    # 初始化数据库（调用db_operation中的真实初始化函数）
    init_db()
    
    # 第一步：选择写入模式
    choose_write_mode()
    
    # 第二步：选择爬取方式
    print("\n===== 相机价格爬取控制中心 =====")
    print("1. 爬取指定品牌")
    print("2. 爬取所有品牌（一键爬取）")
    print("3. 退出")
    
    while True:
        choice = input("\n请输入操作编号（1/2/3）：").strip()
        if choice == "1":
            print(f"\n可选品牌：{list(CAMERA_CONFIGS.keys())}")
            brand = input("请输入要爬取的品牌：").strip()
            crawl_by_brand(brand)
        elif choice == "2":
            confirm = input("确认爬取所有品牌？(y/n)：").strip().lower()
            if confirm == "y":
                crawl_all_brands()
            else:
                print("取消爬取")
        elif choice == "3":
            print("👋 退出程序，再见！")
            break
        else:
            print("❌ 输入错误，请输入1/2/3")

if __name__ == "__main__":
    # 启动控制中心（新增模式选择）
    main_control()