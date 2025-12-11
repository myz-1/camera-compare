import requests
import re

def get_jd_prices_simple():
    """直接获取京东佳能80D价格 - 最简版本"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive'
    }
    
    # 使用您提供的链接
    url = "https://re.jd.com/search?keyword=佳能80d"
    
    try:
        print("正在获取页面...")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        # 打印状态码确认请求成功
        print(f"HTTP状态码: {response.status_code}")
        
        # 直接在整个HTML中搜索价格模式
        html_content = response.text
        
        # 多种价格匹配模式
        price_patterns = [
            r'"price":"([\d.]+)"',           # JSON格式价格
            r'￥\s*(\d+\.?\d*)',             # ￥符号价格
            r'¥\s*(\d+\.?\d*)',              # ¥符号价格  
            r'price.*?["\':](\d+\.?\d*)',    # price字段
            r'jdPrice["\':](\d+\.?\d*)',     # jdPrice字段
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match not in prices and float(match) > 10:  # 过滤掉太小的数字
                    prices.append(match)
                    print(f"找到价格: ¥{match}")
                if len(prices) >= 10:
                    break
            if len(prices) >= 10:
                break

        
        return prices[:10]  # 确保只返回前3个
        
    except Exception as e:
        print(f"出错: {e}")
        return []

# 运行代码
if __name__ == "__main__":
    print("开始获取佳能80D价格...")
    prices = get_jd_prices_simple()
    
    print("\n" + "="*50)
    if prices:
        print("成功获取到价格:")
        for i, price in enumerate(prices, 1):
            print(f"第{i}个价格: ¥{price}")
    else:
        print("未能获取价格，可能原因:")
        print("1. 链接需要登录或验证")
        print("2. 页面结构特殊")
        print("3. 网络问题")
        print("4. 反爬机制")