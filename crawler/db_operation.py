import pymysql
import json
from datetime import datetime

# MySQL配置（请修改为你的实际配置）
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "zmy060830",
    "database": "camera_db",
    "charset": "utf8mb4"
}

# 定义品牌表名映射
BRAND_TABLES = {
    "佳能": "canon_price",
    "尼康": "nikon_price",
    "索尼": "sony_price",
    "富士": "fujifilm_price"
}

def init_db():
    """初始化数据库和品牌分表"""
    conn = None
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            charset=MYSQL_CONFIG["charset"]
        )
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        cursor.execute(f"USE {MYSQL_CONFIG['database']}")
        
        # 为每个品牌创建独立的表
        for brand, table_name in BRAND_TABLES.items():
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
                camera_model VARCHAR(50) NOT NULL COMMENT '相机型号',
                prices JSON COMMENT '该品牌价格列表（闲鱼+京东合并）',
                xianyu_prices JSON COMMENT '闲鱼价格列表（中间3个）',
                jd_prices JSON COMMENT '京东价格列表（中间3个）',
                crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '爬取时间',
                min_price DECIMAL(10,2) COMMENT '最低价格',
                max_price DECIMAL(10,2) COMMENT '最高价格',
                avg_price DECIMAL(10,2) COMMENT '平均价格'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{brand}相机价格表';
            """
            cursor.execute(create_table_sql)
        
        conn.commit()
        print("✅ 数据库初始化成功（已创建4个品牌分表）")
        
    except pymysql.MySQLError as e:
        print(f"❌ 数据库初始化失败: {e}")
        if "latin-1" in str(e):
            print("⚠️  密码包含中文/特殊字符！建议改为纯字母数字密码")
    finally:
        if conn:
            conn.close()

def get_brand_by_model(model):
    """根据相机型号自动识别所属品牌"""
    model_lower = model.lower()
    if "佳能" in model or "canon" in model_lower:
        return "佳能"
    elif "尼康" in model or "nikon" in model_lower:
        return "尼康"
    elif "索尼" in model or "sony" in model_lower or "a7" in model_lower:
        return "索尼"
    elif "富士" in model or "fujifilm" in model_lower or "xt" in model_lower:
        return "富士"
    else:
        print(f"⚠️  无法识别{model}的品牌，默认存入佳能表")
        return "佳能"

def save_camera_price_by_brand(camera_model, xianyu_prices, jd_prices):
    """
    根据品牌自动存入对应表
    :param camera_model: 相机型号
    :param xianyu_prices: 闲鱼中间3个价格
    :param jd_prices: 京东中间3个价格
    """
    # 识别品牌
    brand = get_brand_by_model(camera_model)
    table_name = BRAND_TABLES[brand]
    
    # 合并价格并计算统计值
    all_prices = xianyu_prices + jd_prices
    min_p = min(all_prices) if all_prices else None
    max_p = max(all_prices) if all_prices else None
    avg_p = sum(all_prices)/len(all_prices) if all_prices else None
    
    conn = None
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # 插入数据
        insert_sql = f"""
        INSERT INTO {table_name} (
            camera_model, prices, xianyu_prices, jd_prices,
            min_price, max_price, avg_price
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            camera_model,
            json.dumps(all_prices, ensure_ascii=False),
            json.dumps(xianyu_prices, ensure_ascii=False),
            json.dumps(jd_prices, ensure_ascii=False),
            min_p, max_p, avg_p
        ))
        conn.commit()
        print(f"✅ {brand}-{camera_model} 数据存入 {table_name} 表成功")
        
    except pymysql.MySQLError as e:
        print(f"❌ {brand}-{camera_model} 数据存入失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# 可选：按品牌查询数据（供前端/调试使用）
def query_price_by_brand(brand, model=None):
    """
    查询指定品牌的价格数据
    :param brand: 品牌（佳能/尼康/索尼/富士）
    :param model: 型号（可选，None则查该品牌所有型号）
    :return: 查询结果
    """
    if brand not in BRAND_TABLES:
        print(f"❌ 品牌{brand}不存在，可选品牌：{list(BRAND_TABLES.keys())}")
        return None
    
    table_name = BRAND_TABLES[brand]
    conn = None
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        if model:
            # 查询指定型号
            cursor.execute(f"""
                SELECT * FROM {table_name} 
                WHERE camera_model = %s 
                ORDER BY crawl_time DESC LIMIT 1
            """, (model,))
        else:
            # 查询该品牌所有型号
            cursor.execute(f"""
                SELECT DISTINCT camera_model FROM {table_name}
                ORDER BY camera_model
            """)
        
        result = cursor.fetchall()
        # 解析JSON价格
        for item in result:
            if "prices" in item:
                item["prices"] = json.loads(item["prices"]) if item["prices"] else []
            if "xianyu_prices" in item:
                item["xianyu_prices"] = json.loads(item["xianyu_prices"]) if item["xianyu_prices"] else []
            if "jd_prices" in item:
                item["jd_prices"] = json.loads(item["jd_prices"]) if item["jd_prices"] else []
        
        conn.close()
        return result
    except pymysql.MySQLError as e:
        print(f"❌ 查询失败: {e}")
        return None