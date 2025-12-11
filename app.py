from flask import Flask, jsonify, redirect, send_from_directory, request
import pymysql
import json
import os

# ===================== 数据库配置（和db_operation.py一致） =====================
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "zmy060830",  # 替换为你的MySQL密码
    "database": "camera_db",
    "charset": "utf8mb4"
}

BRAND_TABLES = {
    "佳能": "canon_price",
    "尼康": "nikon_price",
    "索尼": "sony_price",
    "富士": "fujifilm_price"
}

# ===================== Flask应用初始化 =====================
app = Flask(__name__, 
            static_folder="frontend",  # 前端文件所在文件夹（存放index.html/style.css/script.js）
            static_url_path="")        # 静态文件根路径

# 解决跨域问题
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# ===================== 核心接口（前端所需） =====================
# 1. 根路径：直接返回前端页面（解决404）
@app.route('/')
def index():
    # 返回前端index.html文件
    return send_from_directory(app.static_folder, 'index.html')

# 2. 获取所有相机价格数据（核心接口）
@app.route('/api/camera/all', methods=['GET'])
def get_all_camera_data():
    all_data = []
    # 遍历所有品牌表
    for brand, table_name in BRAND_TABLES.items():
        conn = None
        try:
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 查询每个型号的最新数据
            cursor.execute(f"""
                SELECT t.* FROM {table_name} t
                INNER JOIN (
                    SELECT camera_model, MAX(crawl_time) AS latest_time
                    FROM {table_name}
                    GROUP BY camera_model
                ) t2 ON t.camera_model = t2.camera_model AND t.crawl_time = t2.latest_time
            """)
            
            # 解析数据
            results = cursor.fetchall()
            for item in results:
                item['brand'] = brand
                # 解析JSON价格
                item['xianyu_prices'] = json.loads(item['xianyu_prices']) if item.get('xianyu_prices') else []
                item['jd_prices'] = json.loads(item['jd_prices']) if item.get('jd_prices') else []
                # 确保数值类型正确
                item['min_price'] = float(item['min_price']) if item.get('min_price') else 0.0
                item['max_price'] = float(item['max_price']) if item.get('max_price') else 0.0
                item['avg_price'] = float(item['avg_price']) if item.get('avg_price') else 0.0
                all_data.append(item)
                
        except Exception as e:
            print(f"❌ 查询{brand}数据失败：{e}")
        finally:
            if conn:
                conn.close()
    
    return jsonify(all_data)

# 3. 按品牌查询数据（前端品牌筛选用）
@app.route('/api/camera/brand/<brand>', methods=['GET'])
def get_camera_by_brand(brand):
    if brand not in BRAND_TABLES:
        return jsonify({"error": f"品牌{brand}不存在，可选：{list(BRAND_TABLES.keys())}"}), 400
    
    table_name = BRAND_TABLES[brand]
    conn = None
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询最新数据
        cursor.execute(f"""
            SELECT t.* FROM {table_name} t
            INNER JOIN (
                SELECT camera_model, MAX(crawl_time) AS latest_time
                FROM {table_name}
                GROUP BY camera_model
            ) t2 ON t.camera_model = t2.camera_model AND t.crawl_time = t2.latest_time
        """)
        
        results = cursor.fetchall()
        for item in results:
            item['brand'] = brand
            item['xianyu_prices'] = json.loads(item['xianyu_prices']) if item.get('xianyu_prices') else []
            item['jd_prices'] = json.loads(item['jd_prices']) if item.get('jd_prices') else []
            item['min_price'] = float(item['min_price']) if item.get('min_price') else 0.0
            item['max_price'] = float(item['max_price']) if item.get('max_price') else 0.0
            item['avg_price'] = float(item['avg_price']) if item.get('avg_price') else 0.0
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# 4. 按型号搜索数据（前端搜索框用）
@app.route('/api/camera/search', methods=['GET'])
def search_camera():
    # 获取前端传入的搜索关键词
    model = request.args.get('model', '').strip().lower()
    if not model:
        return jsonify({"error": "请输入搜索型号"}), 400
    
    all_data = []
    # 遍历所有品牌表搜索
    for brand, table_name in BRAND_TABLES.items():
        conn = None
        try:
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 模糊搜索型号
            cursor.execute(f"""
                SELECT t.* FROM {table_name} t
                INNER JOIN (
                    SELECT camera_model, MAX(crawl_time) AS latest_time
                    FROM {table_name}
                    GROUP BY camera_model
                ) t2 ON t.camera_model = t2.camera_model AND t.crawl_time = t2.latest_time
                WHERE LOWER(t.camera_model) LIKE %s
            """, (f"%{model}%",))
            
            results = cursor.fetchall()
            for item in results:
                item['brand'] = brand
                item['xianyu_prices'] = json.loads(item['xianyu_prices']) if item.get('xianyu_prices') else []
                item['jd_prices'] = json.loads(item['jd_prices']) if item.get('jd_prices') else []
                item['min_price'] = float(item['min_price']) if item.get('min_price') else 0.0
                item['max_price'] = float(item['max_price']) if item.get('max_price') else 0.0
                item['avg_price'] = float(item['avg_price']) if item.get('avg_price') else 0.0
                all_data.append(item)
                
        except Exception as e:
            print(f"❌ 搜索{brand}数据失败：{e}")
        finally:
            if conn:
                conn.close()
    
    return jsonify(all_data)

# 5. 按价格区间推荐（前端价格推荐用）
@app.route('/api/camera/recommend', methods=['GET'])
def recommend_camera():
    # 获取前端传入的预期价格
    try:
        price = float(request.args.get('price', 0))
    except:
        return jsonify({"error": "请输入有效的价格"}), 400
    
    if price <= 0:
        return jsonify({"error": "价格必须大于0"}), 400
    
    all_data = []
    # 遍历所有品牌表
    for brand, table_name in BRAND_TABLES.items():
        conn = None
        try:
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            cursor.execute(f"""
                SELECT t.* FROM {table_name} t
                INNER JOIN (
                    SELECT camera_model, MAX(crawl_time) AS latest_time
                    FROM {table_name}
                    GROUP BY camera_model
                ) t2 ON t.camera_model = t2.camera_model AND t.crawl_time = t2.latest_time
            """)
            
            results = cursor.fetchall()
            for item in results:
                item['brand'] = brand
                item['xianyu_prices'] = json.loads(item['xianyu_prices']) if item.get('xianyu_prices') else []
                item['jd_prices'] = json.loads(item['jd_prices']) if item.get('jd_prices') else []
                item['min_price'] = float(item['min_price']) if item.get('min_price') else 0.0
                item['max_price'] = float(item['max_price']) if item.get('max_price') else 0.0
                item['avg_price'] = float(item['avg_price']) if item.get('avg_price') else 0.0
                
                # 计算参考均价（闲鱼+京东最低均价）
                xianyu_avg = sum(item['xianyu_prices'])/len(item['xianyu_prices']) if item['xianyu_prices'] else 0
                jd_avg = sum(item['jd_prices'])/len(item['jd_prices']) if item['jd_prices'] else 0
                ref_avg = min(xianyu_avg, jd_avg) if (xianyu_avg and jd_avg) else (xianyu_avg or jd_avg or item['avg_price'])
                
                # 价格区间±20%
                if ref_avg >= price*0.8 and ref_avg <= price*1.2:
                    item['ref_avg'] = ref_avg  # 参考均价
                    item['price_diff'] = abs(ref_avg - price)  # 价格偏差
                    all_data.append(item)
                    
        except Exception as e:
            print(f"❌ 推荐{brand}数据失败：{e}")
        finally:
            if conn:
                conn.close()
    
    # 按价格偏差从小到大排序
    all_data.sort(key=lambda x: x['price_diff'])
    return jsonify(all_data)

# ===================== 启动服务 =====================
if __name__ == '__main__':
    # 确保前端文件夹存在（自动创建）
    if not os.path.exists("frontend"):
        os.makedirs("frontend")
        print("⚠️  已自动创建frontend文件夹，请将前端文件（index.html/style.css/script.js）放入该文件夹！")
    
    # 启动Flask服务（支持外部访问，调试模式）
    app.run(host='0.0.0.0', port=5000, debug=True)