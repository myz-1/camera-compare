import logging
import os
from typing import Dict, List

import pymysql
import json
from flask import Flask, jsonify, send_from_directory, request, Response

# ===================== 基础配置 =====================
# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 数据库配置（替换为你的实际配置）
MYSQL_CONFIG: Dict[str, any] = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "zmy060830",  # 你的MySQL密码
    "database": "camera_db",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

# 品牌-表名映射
BRAND_TABLES: Dict[str, str] = {
    "佳能": "canon_price",
    "尼康": "nikon_price",
    "索尼": "sony_price",
    "富士": "fujifilm_price"
}

# Flask应用初始化
app = Flask(
    __name__,
    static_folder="frontend",
    static_url_path=""
)

# ===================== 通用工具函数 =====================
def get_db_connection() -> pymysql.connections.Connection:
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        logger.info("✅ 数据库连接成功")
        return conn
    except Exception as e:
        logger.error(f"❌ 数据库连接失败：{str(e)}")
        raise e

def parse_price_data(item: Dict, brand: str) -> Dict:
    """统一解析价格数据，处理空值和类型转换"""
    try:
        item["brand"] = brand
        item["id"] = item.get("id", 0)
        item["camera_model"] = item.get("camera_model", "")
        
        # 解析价格数组
        try:
            item["xianyu_prices"] = json.loads(item.get("xianyu_prices", "[]")) if item.get("xianyu_prices") else []
        except:
            item["xianyu_prices"] = []
        
        try:
            item["jd_prices"] = json.loads(item.get("jd_prices", "[]")) if item.get("jd_prices") else []
        except:
            item["jd_prices"] = []
        
        # 数值转换
        for field in ["min_price", "max_price", "avg_price"]:
            try:
                item[field] = float(item.get(field, 0.0)) if item.get(field) else 0.0
            except:
                item[field] = 0.0
        
        # 计算参考均价
        xianyu_avg = sum(item["xianyu_prices"]) / len(item["xianyu_prices"]) if item["xianyu_prices"] else 0.0
        jd_avg = sum(item["jd_prices"]) / len(item["jd_prices"]) if item["jd_prices"] else 0.0
        ref_avg_candidates = [v for v in [xianyu_avg, jd_avg] if v > 0]
        item["ref_avg"] = min(ref_avg_candidates) if ref_avg_candidates else item["avg_price"]
        
        return item
    except Exception as e:
        logger.error(f"❌ 数据解析失败：{str(e)}")
        return {}

def get_latest_camera_data(table_name: str) -> List[Dict]:
    """获取指定表的最新数据（兼容无crawl_time的情况）"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 兼容逻辑：如果有crawl_time则取最新，否则取所有数据
        cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE 'crawl_time'")
        has_crawl_time = cursor.fetchone() is not None
        
        if has_crawl_time:
            sql = f"""
                SELECT t.* FROM {table_name} t
                INNER JOIN (
                    SELECT camera_model, MAX(crawl_time) AS latest_time
                    FROM {table_name}
                    GROUP BY camera_model
                ) t2 ON t.camera_model = t2.camera_model AND t.crawl_time = t2.latest_time
            """
        else:
            sql = f"SELECT * FROM {table_name}"  # 无crawl_time则取全表
        
        cursor.execute(sql)
        results = cursor.fetchall()
        logger.info(f"✅ 从{table_name}获取到{len(results)}条数据")
        return results
    except Exception as e:
        logger.error(f"❌ 查询{table_name}失败：{str(e)}")
        return []
    finally:
        if conn:
            conn.close()

# ===================== 全局中间件 =====================
@app.after_request
def add_response_headers(response: Response) -> Response:
    """跨域+缓存配置"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, HEAD'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    # 禁用静态文件缓存
    if request.path.endswith(('.css', '.js', '.html', '.ico')):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# ===================== 基础路由 =====================
@app.route('/favicon.ico')
def favicon() -> Response:
    return Response(status=204)

@app.route('/')
def index() -> Response:
    if not os.path.exists(app.static_folder):
        os.makedirs(app.static_folder)
        logger.warning("⚠️  自动创建frontend文件夹，请放入前端文件")
        return "请将前端文件放入frontend文件夹！", 404
    return send_from_directory(app.static_folder, 'index.html')

# ===================== 核心接口 =====================
@app.route('/api/camera/all', methods=['GET'])
def get_all_camera_data() -> Response:
    """获取所有相机数据"""
    try:
        all_data = []
        for brand, table_name in BRAND_TABLES.items():
            brand_data = get_latest_camera_data(table_name)
            for item in brand_data:
                parsed_item = parse_price_data(item, brand)
                if parsed_item:
                    all_data.append(parsed_item)
        
        return jsonify({
            "code": 0,
            "message": "获取数据成功",
            "data": all_data
        })
    except Exception as e:
        logger.error(f"❌ 获取所有数据失败：{str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取失败：{str(e)}",
            "data": []
        })

@app.route('/api/camera/brand/<brand>', methods=['GET'])
def get_camera_by_brand(brand: str) -> Response:
    """按品牌获取数据"""
    if brand not in BRAND_TABLES:
        return jsonify({
            "code": 400,
            "message": f"品牌不存在，可选：{list(BRAND_TABLES.keys())}",
            "data": []
        })
    
    try:
        table_name = BRAND_TABLES[brand]
        brand_data = get_latest_camera_data(table_name)
        parsed_data = [parse_price_data(item, brand) for item in brand_data if parse_price_data(item, brand)]
        
        return jsonify({
            "code": 0,
            "message": f"获取{brand}数据成功",
            "data": parsed_data
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取失败：{str(e)}",
            "data": []
        })

@app.route('/api/camera/search', methods=['GET'])
def search_camera() -> Response:
    """按型号搜索"""
    model = request.args.get('model', '').strip().lower()
    if not model:
        return jsonify({
            "code": 400,
            "message": "请输入搜索型号",
            "data": []
        })
    
    try:
        all_data = []
        for brand, table_name in BRAND_TABLES.items():
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = f"""
                SELECT * FROM {table_name}
                WHERE LOWER(camera_model) LIKE %s
            """
            cursor.execute(sql, (f"%{model}%",))
            results = cursor.fetchall()
            conn.close()
            
            for item in results:
                parsed_item = parse_price_data(item, brand)
                if parsed_item:
                    all_data.append(parsed_item)
        
        return jsonify({
            "code": 0,
            "message": f"搜索到{len(all_data)}条结果",
            "data": all_data
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"搜索失败：{str(e)}",
            "data": []
        })

# ===================== 启动服务 =====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)