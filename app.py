import logging
import os
from typing import Dict, List

import pymysql
import json
from flask import Flask, jsonify, send_from_directory, request, Response, session
from datetime import timedelta

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

# ========== 管理员session配置 ==========
app.secret_key = 'camera_admin_2025_zmy'
app.permanent_session_lifetime = timedelta(hours=1)

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

# ========== 初始化管理员表 ==========
def init_admin_table():
    """首次运行自动创建管理员表"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 创建管理员表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(50) NOT NULL,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 初始化默认管理员（账号：admin，密码：123456）
        cursor.execute("""
            INSERT IGNORE INTO admin (username, password) 
            VALUES ('myz', '123456')
        """)
        conn.commit()
        logger.info("✅ 管理员表初始化成功")
    except Exception as e:
        logger.error(f"❌ 管理员表初始化失败：{str(e)}")
    finally:
        if conn:
            conn.close()

# 启动时初始化管理员表
init_admin_table()

# ========== 权限验证装饰器 ==========
def login_required(f):
    """登录验证装饰器"""
    def wrapper(*args, **kwargs):
        if not session.get('admin_login'):
            return jsonify({
                "code": 403,
                "message": "请先登录管理员账号",
                "data": []
            })
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def parse_price_data(item: Dict, brand: str) -> Dict:
    """统一解析价格数据"""
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
    """获取指定表的最新数据"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 兼容crawl_time字段
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
            sql = f"SELECT * FROM {table_name}"
        
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
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, HEAD, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    
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

# ===================== 管理员接口 =====================
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录接口"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                "code": 400,
                "message": "账号和密码不能为空",
                "data": []
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM admin WHERE username = %s AND password = %s
        """, (username, password))
        admin = cursor.fetchone()
        conn.close()
        
        if not admin:
            return jsonify({
                "code": 401,
                "message": "账号或密码错误",
                "data": []
            })
        
        # 保存登录状态
        session['admin_login'] = True
        session['admin_username'] = username
        logger.info(f"✅ 管理员{username}登录成功")
        
        return jsonify({
            "code": 0,
            "message": "登录成功",
            "data": {"username": username}
        })
    except Exception as e:
        logger.error(f"❌ 管理员登录失败：{str(e)}")
        return jsonify({
            "code": 500,
            "message": f"登录失败：{str(e)}",
            "data": []
        })

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """管理员退出登录"""
    session.clear()
    logger.info("✅ 管理员退出登录")
    return jsonify({
        "code": 0,
        "message": "退出成功",
        "data": []
    })

# ===================== 数据增删改查接口 =====================
@app.route('/api/camera/add', methods=['POST'])
@login_required
def add_camera():
    """添加相机数据"""
    try:
        data = request.get_json() or {}
        brand = data.get('brand', '').strip()
        camera_model = data.get('camera_model', '').strip()
        min_price = data.get('min_price', 0.0)
        max_price = data.get('max_price', 0.0)
        avg_price = data.get('avg_price', 0.0)
        jd_prices = data.get('jd_prices', [])
        xianyu_prices = data.get('xianyu_prices', [])
        crawl_time = data.get('crawl_time', None)
        
        if brand not in BRAND_TABLES:
            return jsonify({
                "code": 400,
                "message": f"品牌不存在，可选：{list(BRAND_TABLES.keys())}",
                "data": []
            })
        if not camera_model:
            return jsonify({
                "code": 400,
                "message": "相机型号不能为空",
                "data": []
            })
        
        table_name = BRAND_TABLES[brand]
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 兼容crawl_time字段
        cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE 'crawl_time'")
        has_crawl_time = cursor.fetchone() is not None
        
        if has_crawl_time and crawl_time:
            sql = f"""
                INSERT INTO {table_name} (camera_model, min_price, max_price, avg_price, jd_prices, xianyu_prices, crawl_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                camera_model, float(min_price), float(max_price), float(avg_price),
                json.dumps(jd_prices), json.dumps(xianyu_prices), crawl_time
            )
        else:
            sql = f"""
                INSERT INTO {table_name} (camera_model, min_price, max_price, avg_price, jd_prices, xianyu_prices)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (
                camera_model, float(min_price), float(max_price), float(avg_price),
                json.dumps(jd_prices), json.dumps(xianyu_prices)
            )
        
        cursor.execute(sql, params)
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 新增{brand}相机{camera_model}成功")
        return jsonify({
            "code": 0,
            "message": f"添加{brand}-{camera_model}成功",
            "data": {"id": cursor.lastrowid}
        })
    except Exception as e:
        logger.error(f"❌ 添加相机数据失败：{str(e)}")
        return jsonify({
            "code": 500,
            "message": f"添加失败：{str(e)}",
            "data": []
        })

@app.route('/api/camera/edit', methods=['POST'])
@login_required
def edit_camera():
    """修改相机数据"""
    try:
        data = request.get_json() or {}
        brand = data.get('brand', '').strip()
        camera_id = data.get('id', 0)
        camera_model = data.get('camera_model', '').strip()
        min_price = data.get('min_price', 0.0)
        max_price = data.get('max_price', 0.0)
        avg_price = data.get('avg_price', 0.0)
        jd_prices = data.get('jd_prices', [])
        xianyu_prices = data.get('xianyu_prices', [])
        crawl_time = data.get('crawl_time', None)
        
        if brand not in BRAND_TABLES:
            return jsonify({
                "code": 400,
                "message": f"品牌不存在，可选：{list(BRAND_TABLES.keys())}",
                "data": []
            })
        if not camera_id or not camera_model:
            return jsonify({
                "code": 400,
                "message": "ID和型号不能为空",
                "data": []
            })
        
        table_name = BRAND_TABLES[brand]
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 组装更新SQL
        update_fields = [
            "camera_model = %s",
            "min_price = %s",
            "max_price = %s",
            "avg_price = %s",
            "jd_prices = %s",
            "xianyu_prices = %s"
        ]
        params = [
            camera_model, float(min_price), float(max_price), float(avg_price),
            json.dumps(jd_prices), json.dumps(xianyu_prices)
        ]
        
        if crawl_time:
            update_fields.append("crawl_time = %s")
            params.append(crawl_time)
        
        params.append(camera_id)
        
        sql = f"""
            UPDATE {table_name} 
            SET {', '.join(update_fields)} 
            WHERE id = %s
        """
        cursor.execute(sql, params)
        conn.commit()
        conn.close()
        
        if cursor.rowcount == 0:
            return jsonify({
                "code": 404,
                "message": "数据不存在或未修改",
                "data": []
            })
        
        logger.info(f"✅ 修改{brand}相机{camera_model}(ID:{camera_id})成功")
        return jsonify({
            "code": 0,
            "message": f"修改{brand}-{camera_model}成功",
            "data": []
        })
    except Exception as e:
        logger.error(f"❌ 修改相机数据失败：{str(e)}")
        return jsonify({
            "code": 500,
            "message": f"修改失败：{str(e)}",
            "data": []
        })

@app.route('/api/camera/delete', methods=['POST'])
@login_required
def delete_camera():
    """删除相机数据"""
    try:
        data = request.get_json() or {}
        brand = data.get('brand', '').strip()
        camera_id = data.get('id', 0)
        
        if brand not in BRAND_TABLES:
            return jsonify({
                "code": 400,
                "message": f"品牌不存在，可选：{list(BRAND_TABLES.keys())}",
                "data": []
            })
        if not camera_id:
            return jsonify({
                "code": 400,
                "message": "ID不能为空",
                "data": []
            })
        
        table_name = BRAND_TABLES[brand]
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (camera_id,))
        conn.commit()
        conn.close()
        
        if cursor.rowcount == 0:
            return jsonify({
                "code": 404,
                "message": "数据不存在",
                "data": []
            })
        
        logger.info(f"✅ 删除{brand}相机(ID:{camera_id})成功")
        return jsonify({
            "code": 0,
            "message": "删除成功",
            "data": []
        })
    except Exception as e:
        logger.error(f"❌ 删除相机数据失败：{str(e)}")
        return jsonify({
            "code": 500,
            "message": f"删除失败：{str(e)}",
            "data": []
        })

# ===================== 原有核心接口 =====================
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
    