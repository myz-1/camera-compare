# jd_crawler_new.py
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import re
from typing import List, Optional

class JDPriceCrawlerRunner:
    """京东价格爬虫运行器（极速版：无滚动+短等待）"""
    
    DEFAULT_CONFIG = {
        "keyword": "佳能80d机身",
        "min_price": 1000,
        "max_price": 20000,
        "max_price_count": 30,
        "browser_data_dir": "F:\\jd\\browser_data",
        "headless": False
    }

    def __init__(self, config: Optional[dict] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.browser: Optional[ChromiumPage] = None
        self.filtered_prices: List[float] = []
        
        # 提取配置
        self.keyword = self.config["keyword"]
        self.min_price = self.config["min_price"]
        self.max_price = self.config["max_price"]
        self.max_price_count = self.config["max_price_count"]
        self.browser_data_dir = self.config["browser_data_dir"]
        self.headless = self.config["headless"]

    def _init_browser(self) -> ChromiumPage:
        """初始化浏览器（禁用缓存）"""
        if self.browser and self.browser.connected:
            return self.browser
        
        co = ChromiumOptions()
        # 反爬+防缓存配置
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--ignore-certificate-errors')
        co.set_argument(f'--user-data-dir={self.browser_data_dir}')
        # UA配置
        co.set_user_agent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        co.headless(self.headless)
        
        self.browser = ChromiumPage(co)
        return self.browser

    def manual_login(self) -> None:
        """手动登录京东"""
        self._init_browser()
        print("🔐 请在浏览器完成京东登录后按回车...")
        self.browser.get('https://www.jd.com')
        input("✅ 登录完成 → 按回车键继续")
        print("📌 登录状态已保存，后续运行无需重复登录")

    def _extract_price_from_item(self, item) -> Optional[float]:
        """从单个商品元素提取价格"""
        try:
            # 优先提取data-price属性
            price_attr = item.attr('data-price') or item.ele('.p-price').attr('data-price')
            if price_attr and price_attr.replace('.', '').isdigit():
                return float(price_attr)
            return None
        except (ValueError, AttributeError, TypeError):
            return None

    def _extract_prices(self) -> List[float]:
        """提取价格（无滚动+短等待+首屏优先）"""
        valid_prices = []
        
        # 1. 构造URL+轻量刷新
        search_url = f"https://search.jd.com/Search?keyword={self.keyword}&enc=utf8&t={int(time.time())}"
        self.browser.get(search_url)
        print(f"⏳ 正在加载【{self.keyword}】京东搜索结果...")
        time.sleep(4)  
        
        # 2. 直接提取首屏商品
        product_items = self.browser.eles('div.gl-item')
        print(f"🔍 找到 {len(product_items)} 个首屏商品，开始提取价格...")
        
        # 3. 极速提取价格（只取前30个符合条件的）
        for item in product_items:
            if len(valid_prices) >= self.max_price_count:
                break
            price = self._extract_price_from_item(item)
            if price and self.min_price <= price <= self.max_price:
                valid_prices.append(price)
        
        # 兜底：如果首屏不够，极简全局匹配
        if not valid_prices:
            page_source = self.browser.html
            price_pattern = re.compile(r'¥\s*(\d+(?:\.\d+)?)')
            all_price_str = price_pattern.findall(page_source)[:self.max_price_count]
            valid_prices = [float(p) for p in all_price_str if self.min_price <= float(p) <= self.max_price]
        
        # 去重+限制数量
        valid_prices = list(dict.fromkeys(valid_prices))[:self.max_price_count]
        return valid_prices

    def run(self, need_login: bool = True) -> List[float]:
        """运行爬虫（极速版）"""
        try:
            if need_login:
                self.manual_login()
            else:
                self._init_browser()
            
            self.filtered_prices = []
            self.filtered_prices = self._extract_prices()
            return self.filtered_prices
        
        except Exception as e:
            print(f"❌ 京东爬虫运行出错：{str(e)}")
            raise

# ===================== 关键：添加供外部调用的函数 =====================
def get_jd_prices_simple(keyword, min_price=1000, max_price=20000, max_count=30, need_login=False):
    """
    京东价格提取简化函数（供 crawler_runner.py 调用）
    :param keyword: 搜索关键词
    :param min_price: 最低价格
    :param max_price: 最高价格
    :param max_count: 最多提取数量
    :param need_login: 是否需要登录
    :return: 价格列表（字符串格式，兼容原始调用逻辑）
    """
    config = {
        "keyword": keyword,
        "min_price": min_price,
        "max_price": max_price,
        "max_price_count": max_count
    }
    crawler = JDPriceCrawlerRunner(config)
    prices = crawler.run(need_login=need_login)
    # 转换为字符串格式，避免浮点数精度问题
    return [str(p) for p in prices]

# ------------------- 测试入口（可选） -------------------
if __name__ == "__main__":
    # 测试函数调用
    test_prices = get_jd_prices_simple("索尼a7m4机身", 5000, 15000, 30, False)
    print("测试提取的价格：", test_prices)