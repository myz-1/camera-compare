import time
import json

# 导入独立的爬虫文件
from xianyu_crawler import XianyuPriceOnly  # 闲鱼爬虫独立文件
from jd_crawler_new import get_jd_prices_simple  # 京东爬虫独立文件

# 导入真实数据库操作文件
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
        {"model": "佳能R100", "min_price": 500, "max_price": 10000},
        {"model": "佳能R50", "min_price": 2000, "max_price": 10000},
        {"model": "佳能R7", "min_price": 1000, "max_price": 20000},
        {"model": "佳能R6", "min_price": 1000, "max_price": 20000},
        {"model": "佳能5D4", "min_price": 3000, "max_price": 25000},  # 全画幅专业机
        {"model": "佳能6D2", "min_price": 2000, "max_price": 18000},  # 入门全画幅
        {"model": "佳能R8", "min_price": 4000, "max_price": 15000},   # 轻量化全画幅
        {"model": "佳能R10", "min_price": 1500, "max_price": 12000},  # 入门微单
        {"model": "佳能M50 II", "min_price": 1000, "max_price": 8000},# 入门便携微单
        {"model": "佳能R5", "min_price": 8000, "max_price": 35000},   # 旗舰微单
        {"model": "佳能850D", "min_price": 1500, "max_price": 9000},  # 入门单反
    ],
    "尼康": [
        {"model": "尼康z6", "min_price": 2000, "max_price": 30000},
        {"model": "尼康d850", "min_price": 4000, "max_price": 28000},
        {"model": "尼康z7ii", "min_price": 6000, "max_price": 35000},
        {"model": "尼康Z5", "min_price": 3000, "max_price": 18000},    # 入门全画幅微单
        {"model": "尼康Z8", "min_price": 15000, "max_price": 45000},   # 旗舰微单
        {"model": "尼康D7500", "min_price": 1500, "max_price": 10000}, # 中端单反
        {"model": "尼康D5600", "min_price": 1000, "max_price": 8000},  # 入门单反
        {"model": "尼康Zfc", "min_price": 2000, "max_price": 10000},   # 复古微单
        {"model": "尼康Z9", "min_price": 10000, "max_price": 60000},   # 顶级旗舰微单
    ],
    "索尼": [
        {"model": "索尼a7m4", "min_price": 5000, "max_price": 15000},
        {"model": "索尼a6400", "min_price": 2000, "max_price": 8000},
        {"model": "索尼a7s3", "min_price": 10000, "max_price": 40000},
        {"model": "索尼A7C", "min_price": 4000, "max_price": 16000},    # 轻量化全画幅
        {"model": "索尼A7R5", "min_price": 12000, "max_price": 38000},  # 高像素旗舰
        {"model": "索尼ZV-E10", "min_price": 2000, "max_price": 8000}, # 视频入门微单
        {"model": "索尼A6700", "min_price": 3000, "max_price": 10000},  # 中端APS-C微单
        {"model": "索尼FX3", "min_price": 15000, "max_price": 40000},   # 专业视频机
        {"model": "索尼A1", "min_price": 10000, "max_price": 60000},    # 顶级全画幅旗舰
    ],
    "富士": [
        {"model": "富士xt5", "min_price": 4000, "max_price": 12000},
        {"model": "富士xs20", "min_price": 3000, "max_price": 10000},
        {"model": "富士xt4", "min_price": 3500, "max_price": 11000},
        {"model": "富士XT30 II", "min_price": 2500, "max_price": 9000}, # 入门复古微单
        {"model": "富士X100V", "min_price": 4000, "max_price": 12000},  # 复古旁轴
        {"model": "富士XS10", "min_price": 3000, "max_price": 10000},   # 中端APS-C
        {"model": "富士GFX 50S II", "min_price": 10000, "max_price": 35000}, # 中画幅
        {"model": "富士X-H2", "min_price": 6000, "max_price": 18000},   # 旗舰APS-C
    ],
}

# 全局变量：数据写入模式
WRITE_MODE = "add"  # 默认新增模式

def get_middle_three_prices(prices):
    """从价格列表中筛选中间3个价格（排序后取中间），并保留1位小数"""
    # 1. 去重 + 排序
    unique_prices = sorted(list(set(prices)))  # 去重+排序
    price_count = len(unique_prices)
    
    # 2. 筛选中间3个价格
    if price_count <= 3:
        middle_prices = unique_prices
    else:
        middle_idx = price_count // 2
        start_idx = max(0, middle_idx - 1)
        end_idx = min(price_count, middle_idx + 2)
        middle_prices = unique_prices[start_idx:end_idx]
    
    # 3. 新增：保留1位小数（兼容整数/浮点数）
    middle_prices_with_one_decimal = [round(price, 1) for price in middle_prices]
    
    return middle_prices_with_one_decimal

def run_xianyu_crawler(model, min_price, max_price):
    """调用闲鱼爬虫，返回中间3个价格"""
    xianyu = XianyuPriceOnly()
    xianyu.keyword = model
    xianyu.min_price = min_price
    xianyu.max_price = max_price
    xianyu.run(need_login=False)  # 首次运行改为True，后续False
    
    # 打印价格筛选结果
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
        # 调用京东爬虫的简化函（传递完整参数）
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
            
            # 3. 插入新数据
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
    """爬取单个相机型号（原有函数，保留不变）"""
    model = config["model"]
    min_price = config["min_price"]
    max_price = config["max_price"]
    
    print(f"\n📷 开始爬取 {model} (模式：{WRITE_MODE})")
    # 爬取闲鱼价格
    xianyu_prices = run_xianyu_crawler(model, min_price, max_price)
    # 爬取京东价格
    jd_prices = run_jd_crawler(model, min_price, max_price)
    # 保存/更新数据
    save_price_data(model, xianyu_prices, jd_prices)
    # 防反爬延迟
    time.sleep(3)

def crawl_specify_model():
    """新增：爬取用户指定的单个型号"""
    # 先列出所有可选型号，方便用户选择
    all_models = []
    print("\n===== 可选型号列表 =====")
    for brand, models in CAMERA_CONFIGS.items():
        print(f"{brand}：")
        for m in models:
            model_name = m["model"]
            all_models.append(model_name)
            print(f"  - {model_name}")
    
    # 获取用户输入的型号
    while True:
        target_model = input("\n请输入要爬取的单个型号（如：佳能80d）：").strip()
        if target_model in all_models:
            break
        else:
            print(f"❌ 型号{target_model}不存在！请从列表中选择")
    
    # 查找该型号对应的配置（品牌、价格区间）
    target_config = None
    for brand, models in CAMERA_CONFIGS.items():
        for m in models:
            if m["model"] == target_model:
                target_config = m
                break
        if target_config:
            break
    
    # 执行单个型号爬取
    print(f"\n========== 开始爬取单个型号【{target_model}】(模式：{WRITE_MODE}) ==========")
    crawl_single_model(target_config)
    print(f"✅ 单个型号【{target_model}】爬取完成！")

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
    """核心控制函数 - 交互式选择爬取方式（新增单型号爬取选项）"""
    # 初始化数据库（调用db_operation中的真实初始化函数）
    init_db()
    
    # 第一步：选择写入模式
    choose_write_mode()
    
    # 第二步：选择爬取方式
    print("\n===== 相机价格爬取控制中心 =====")
    print("1. 爬取指定品牌")
    print("2. 爬取所有品牌（一键爬取）")
    print("3. 爬取单个指定型号")  # 新增选项
    print("4. 退出")  
    
    while True:
        choice = input("\n请输入操作编号（1/2/3/4）：").strip()
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
        elif choice == "3":  # 新增分支：爬取单个型号
            crawl_specify_model()
        elif choice == "4":  # 原有退出逻辑移到4
            print("👋 退出程序，再见！")
            break
        else:
            print("❌ 输入错误，请输入1/2/3/4")

if __name__ == "__main__":
    # 启动控制中心
    main_control()