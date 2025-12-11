from DrissionPage import ChromiumPage, ChromiumOptions
import time
import re

class XianyuPriceOnly:
    def __init__(self):
        self.filtered_prices = []
        self.browser = None
        # 配置参数（只改这3行）
        self.keyword = '佳能80d'
        self.min_price = 1000
        self.max_price = 20000

    def create_browser(self):
        """创建浏览器（保留登录会话）"""
        co = ChromiumOptions()
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--user-data-dir=F:\\camera\\browser_data')
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        co.headless(False)
        self.browser = ChromiumPage(co)
        return self.browser

    def manual_login(self):
        """仅第一次需要登录"""
        if not self.browser:
            self.create_browser()
        print("🔐 请在浏览器完成闲鱼登录后按回车...")
        self.browser.get('https://www.goofish.com')
        input("✅ 登录完成 → 按回车键继续")

    def get_prices(self, need_login=True):
        """仅提取并筛选价格"""
        # 1. 初始化浏览器
        if need_login:
            self.manual_login()
        elif not self.browser:
            self.create_browser()

        # 2. 访问搜索页+等待加载
        self.browser.get(f"https://www.goofish.com/search?q={self.keyword}")
        for i in range(1):
            time.sleep(1)
        src = self.browser.html

        # 3. 正则提取所有价格
        page_source = self.browser.html
        price_pattern = re.compile(r'<span class="number--\w+">(\d+)</span>')
        all_prices = [float(p) for p in price_pattern.findall(page_source) if p.isdigit()]
        self.filtered_prices = [p for p in all_prices if self.min_price <= p <= self.max_price]

        # 2. 如果没拿到，再抓“万”
        if not self.filtered_prices:
            split = re.findall(
                r'<span[^>]*>\s*(\d+)\s*</span>\s*'
                r'<span[^>]*>\s*(\.\d{1,2})\s*</span>.*?'
                r'<span[^>]*>\s*万\s*</span>', src, re.DOTALL
            )
            prices = [float(int_p + dec_p) * 10000 for int_p, dec_p in split]
            self.filtered_prices = [p for p in prices if self.min_price <= p <= self.max_price][:20]
       

    def print_prices(self):
        """仅打印筛选后的价格"""
        print(f"\n===== 【{self.keyword}】价格筛选结果 =====")
        print(f"筛选区间：{self.min_price} - {self.max_price} 元")
        print(f"符合条件的价格：{self.filtered_prices}")
        print(f"总计：{len(self.filtered_prices)} 个价格")

    def run(self, need_login=True):
        self.get_prices(need_login)
        self.print_prices()

if __name__ == "__main__":
    # 仅改这里
    tool = XianyuPriceOnly()
    tool.keyword = "索尼a7m3"
    tool.min_price = 1000
    tool.max_price = 20000
    tool.run(need_login=True)  # 第一次True，后续False