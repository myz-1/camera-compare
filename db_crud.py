import pymysql
import json
from datetime import datetime

# 数据库配置
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "zmy060830",
    "database": "camera_db",
    "charset": "utf8mb4"
}

BRAND_TABLES = {
    "1": {"name": "佳能", "table": "canon_price"},
    "2": {"name": "尼康", "table": "nikon_price"},
    "3": {"name": "索尼", "table": "sony_price"},
    "4": {"name": "富士", "table": "fujifilm_price"}
}

class CameraDBTool:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def _connect(self):
        """连接数据库"""
        try:
            self.conn = pymysql.connect(**MYSQL_CONFIG)
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            return True
        except pymysql.MySQLError as e:
            print(f"\n❌ 数据库连接失败：{e}")
            return False

    def _close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def _select_brand(self):
        """选择品牌"""
        print("\n===== 选择相机品牌 =====")
        for k, v in BRAND_TABLES.items():
            print(f"{k}. {v['name']}")
        
        while True:
            choice = input("请输入品牌编号（1-4）：").strip()
            if choice in BRAND_TABLES:
                return BRAND_TABLES[choice]
            print("❌ 输入错误，请输入1-4的数字")

    # ========== 核心：查询全部数据 ==========
    def query_all_data(self):
        """查询所有品牌/指定品牌的全部数据（含历史）"""
        print("\n===== 查询范围选择 =====")
        print("1. 查询所有品牌的全部数据")
        print("2. 查询指定品牌的全部数据")
        
        while True:
            q_choice = input("请选择（1/2）：").strip()
            if q_choice in ['1', '2']:
                break
            print("❌ 输入错误，请输入1或2")

        if not self._connect():
            return

        try:
            total_count = 0
            # 1. 查询所有品牌全部数据
            if q_choice == '1':
                print("\n" + "="*60)
                print("                     所有品牌全部数据（含历史）")
                print("="*60)
                for brand_key in BRAND_TABLES.keys():
                    brand = BRAND_TABLES[brand_key]
                    self.cursor.execute(f"SELECT * FROM {brand['table']} ORDER BY camera_model, crawl_time DESC")
                    data_list = self.cursor.fetchall()
                    
                    if not data_list:
                        print(f"\n【{brand['name']}】：暂无任何数据")
                        continue
                    
                    print(f"\n【{brand['name']}】（共{len(data_list)}条数据）：")
                    current_model = ""
                    for idx, data in enumerate(data_list, 1):
                        total_count += 1
                        # 型号分组展示
                        if data['camera_model'] != current_model:
                            current_model = data['camera_model']
                            print(f"\n  ├── {current_model}")
                        # 解析价格
                        xianyu = json.loads(data['xianyu_prices']) if data['xianyu_prices'] else []
                        jd = json.loads(data['jd_prices']) if data['jd_prices'] else []
                        # 展示详情
                        print(f"  │   └── 记录{idx}：更新时间={data['crawl_time'].strftime('%Y-%m-%d %H:%M:%S')} | 闲鱼价格={xianyu[:3]} | 京东价格={jd[:3]} | 平均价={data['avg_price'] or '无'}")
            
            # 2. 查询指定品牌全部数据
            else:
                brand = self._select_brand()
                self.cursor.execute(f"SELECT * FROM {brand['table']} ORDER BY camera_model, crawl_time DESC")
                data_list = self.cursor.fetchall()
                
                print("\n" + "="*60)
                print(f"                 {brand['name']}品牌全部数据（含历史）")
                print("="*60)
                
                if not data_list:
                    print(f"\n❌ 【{brand['name']}】暂无任何数据")
                    return
                
                current_model = ""
                for idx, data in enumerate(data_list, 1):
                    total_count += 1
                    if data['camera_model'] != current_model:
                        current_model = data['camera_model']
                        print(f"\n  ├── {current_model}")
                    xianyu = json.loads(data['xianyu_prices']) if data['xianyu_prices'] else []
                    jd = json.loads(data['jd_prices']) if data['jd_prices'] else []
                    print(f"  │   └── 记录{idx}：更新时间={data['crawl_time'].strftime('%Y-%m-%d %H:%M:%S')} | 闲鱼价格={xianyu[:3]} | 京东价格={jd[:3]} | 平均价={data['avg_price'] or '无'}")

            # 总计提示
            print(f"\n" + "="*60)
            print(f"查询完成！共查询到 {total_count} 条数据")
            print("="*60)

        except pymysql.MySQLError as e:
            print(f"\n❌ 查询失败：{e}")
        finally:
            self._close()

    # ========== 核心：删除功能 ==========
    def delete_data(self):
        """删除：全品牌/指定型号 + 最新一条/全部数据"""
        # 步骤1：选品牌
        brand = self._select_brand()
        
        # 步骤2：选删除范围
        print("\n===== 选择删除范围 =====")
        print("1. 删除该品牌下所有数据")
        print("2. 删除该品牌下指定型号数据")
        
        while True:
            delete_scope = input("请选择（1/2）：").strip()
            if delete_scope in ['1', '2']:
                break
            print("❌ 输入错误，请输入1或2")

        # 步骤3：选删除粒度
        print("\n===== 选择删除粒度 =====")
        print("1. 只删除最新一条数据")
        print("2. 删除所有数据（谨慎！）")
        
        while True:
            delete_granularity = input("请选择（1/2）：").strip()
            if delete_granularity in ['1', '2']:
                break
            print("❌ 输入错误，请输入1或2")

        # 构建删除描述
        is_delete_all = (delete_granularity == '2')
        if delete_scope == '1':
            delete_desc = f"删除【{brand['name']}】品牌下{'所有数据' if is_delete_all else '所有型号的最新一条数据'}"
        else:
            model = input(f"\n请输入【{brand['name']}】要删除的型号（如：索尼a7m4）：").strip()
            if not model:
                print("❌ 型号不能为空")
                return
            delete_desc = f"删除【{brand['name']}】{model} {'所有数据' if is_delete_all else '最新一条数据'}"

        # 步骤4：删除确认
        print(f"\n⚠️  确认{delete_desc}？")
        confirm = input("输入 y 确认删除，其他键取消：").strip().lower()
        if confirm != 'y':
            print("❌ 取消删除")
            return
        
        # 步骤5：执行删除
        if not self._connect():
            return

        try:
            affected_rows = 0
            table = brand['table']

            # 删全品牌
            if delete_scope == '1':
                if is_delete_all:
                    # 删品牌所有数据
                    self.cursor.execute(f"DELETE FROM {table}")
                    affected_rows = self.cursor.rowcount
                else:
                    # 删品牌下每个型号最新一条
                    self.cursor.execute(f"""
                        SELECT t.id FROM {table} t
                        INNER JOIN (
                            SELECT camera_model, MAX(crawl_time) AS latest_time
                            FROM {table} GROUP BY camera_model
                        ) t2 ON t.camera_model = t2.camera_model AND t.crawl_time = t2.latest_time
                    """)
                    latest_ids = [item['id'] for item in self.cursor.fetchall()]
                    if not latest_ids:
                        print("\n❌ 该品牌暂无数据可删除")
                        return
                    placeholders = ','.join(['%s']*len(latest_ids))
                    self.cursor.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", latest_ids)
                    affected_rows = len(latest_ids)

            # 删指定型号
            else:
                if is_delete_all:
                    # 删型号所有数据
                    self.cursor.execute(f"DELETE FROM {table} WHERE camera_model = %s", (model,))
                else:
                    # 删型号最新一条
                    self.cursor.execute(f"""
                        DELETE FROM {table} WHERE id = (
                            SELECT id FROM (
                                SELECT id FROM {table}
                                WHERE camera_model = %s ORDER BY crawl_time DESC LIMIT 1
                            ) t
                        )
                    """, (model,))
                affected_rows = self.cursor.rowcount

            self.conn.commit()

            # 结果提示
            if affected_rows == 0:
                print(f"\n❌ 删除失败：未找到对应数据")
            else:
                print(f"\n✅ 删除成功！共删除 {affected_rows} 条数据")

        except pymysql.MySQLError as e:
            print(f"\n❌ 删除失败：{e}")
            self.conn.rollback()
        finally:
            self._close()

    # ========== 主菜单 ==========
    def main_menu(self):
        """极简主菜单：查询全部数据 + 删除数据"""
        while True:
            print("\n" + "="*40)
            print("          相机价格数据库操作工具")
            print("="*40)
            print("1. 查询全部数据（含历史）")
            print("2. 删除数据")
            print("0. 退出程序")
            print("="*40)

            choice = input("请选择操作（0-2）：").strip()
            if choice == '0':
                print("\n👋 退出程序，再见！")
                break
            elif choice == '1':
                self.query_all_data()
            elif choice == '2':
                self.delete_data()
            else:
                print("\n❌ 输入错误，请输入0-2的数字")

            # 操作后暂停
            input("\n按回车键返回主菜单...")

# ========== 运行程序 ==========
if __name__ == "__main__":
    tool = CameraDBTool()
    tool.main_menu()