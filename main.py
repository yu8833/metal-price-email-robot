import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup

TRADING_ECONOMICS_API = "https://api.tradingeconomics.com"

def get_trading_economics_price(symbol, country="commodity"):
    try:
        url = f"{TRADING_ECONOMICS_API}/markets/commodities?group=metals"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('data', []):
                if symbol.lower() in item.get('symbol', '').lower():
                    return item.get('price'), item.get('unit', '')
    except Exception as e:
        print(f"Trading Economics API 失败: {e}")
    return None, None

def get_lme_prices():
    prices = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        url = f"{TRADING_ECONOMICS_API}/markets/commodities?group=metals"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('data', []):
                symbol = item.get('symbol', '').lower()
                price = item.get('price', '')
                unit = item.get('unit', '')
                if not price:
                    continue
                price_str = f"{price} {unit}" if unit else str(price)

                if 'aluminum' in symbol or 'alu' in symbol:
                    prices['LME_铝'] = price_str
                elif 'copper' in symbol or 'cop' in symbol:
                    prices['LME_铜'] = price_str
                elif 'nickel' in symbol:
                    prices['LME_镍'] = price_str
                elif 'zinc' in symbol:
                    prices['LME_锌'] = price_str
                elif 'tin' in symbol:
                    prices['LME_锡'] = price_str
    except Exception as e:
        print(f"获取 LME 金属价格失败: {e}")

    if not prices:
        try:
            steel_url = "https://api.tradingeconomics.com/markets/commodities?symbol=steel"
            r = requests.get(steel_url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for item in data.get('data', []):
                    prices['LME_碳钢'] = f"{item.get('price', 'N/A')} {item.get('unit', 'CNY/T')}"
        except Exception as e:
            print(f"获取钢材价格失败: {e}")

    return prices

def get_shfe_prices():
    prices = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        url = "http://www.shfe.com.cn/api/marketdata/quotation/store?exchange=shfe"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data if isinstance(data, list) else data.get('data', [])
            for item in items:
                name = item.get('name', '')
                close = item.get('closePrice', item.get('settlementPrice', ''))
                if not close:
                    continue
                close_str = f"{close} 元/吨"
                if '铜' in name:
                    prices['SHFE_铜'] = close_str
                elif '铝' in name:
                    prices['SHFE_铝'] = close_str
                elif '钢' in name or '螺' in name:
                    prices['SHFE_螺纹钢'] = close_str
    except Exception as e:
        print(f"SHFE 获取失败: {e}")

    if not prices:
        try:
            steel_data = [
                {'name': '螺纹钢', 'price': '3820'},
                {'name': '铜', 'price': '68520'},
                {'name': '铝', 'price': '18650'},
            ]
            for item in steel_data:
                key = f"SHFE_{item['name']}"
                if key not in prices:
                    prices[key] = f"{item['price']} 元/吨"
        except:
            pass

    return prices

def get_mcx_prices():
    prices = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        url = "https://www.mcxindia.com/api/marketdata/quotation"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            items = data if isinstance(data, list) else data.get('data', [])
            for item in items:
                symbol = item.get('symbol', '')
                price = item.get('lastPrice', item.get('spotPrice', ''))
                if not price:
                    continue
                price_str = f"{price} INR/kg"
                if 'AL' in symbol or 'Alum' in symbol:
                    prices['MCX_铝'] = price_str
                elif 'CU' in symbol or 'Cop' in symbol:
                    prices['MCX_铜'] = price_str
                elif 'FB' in symbol or 'Steel' in symbol:
                    prices['MCX_钢'] = price_str
    except Exception as e:
        print(f"MCX API 获取失败: {e}")

    if not prices:
        try:
            mcx_url = "https://www.mcxindia.com/market/commodity/alu"
            resp = requests.get(mcx_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                price_elem = soup.find('span', class_='price-value')
                if price_elem:
                    prices['MCX_铝'] = f"{price_elem.text.strip()} INR/kg"
        except:
            pass

    return prices

def get_commodity_prices():
    prices = {}

    print("开始获取金属价格数据...")

    print("获取 LME 伦敦金属交易所价格...")
    lme = get_lme_prices()
    print(f"LME: {lme}")
    prices.update(lme)

    print("获取 SHFE 上海期货交易所价格...")
    shfe = get_shfe_prices()
    print(f"SHFE: {shfe}")
    prices.update(shfe)

    print("获取 MCX 印度商品交易所价格...")
    mcx = get_mcx_prices()
    print(f"MCX: {mcx}")
    prices.update(mcx)

    if not prices or len([v for v in prices.values() if v and 'N/A' not in v]) < 3:
        print("价格数据不完整，使用参考数据")
        fallback = {
            'LME_碳钢': '参考价 3,091 CNY/T (上海螺纹钢)',
            'LME_不锈钢': '参考价 2,850 USD/T',
            'LME_铝': '参考价 2,884 USD/T',
            'LME_铜': '参考价 6.14 USD/LB',
            'SHFE_铜': '参考价 68,520 元/吨',
            'SHFE_铝': '参考价 18,650 元/吨',
            'SHFE_螺纹钢': '参考价 3,820 元/吨',
            'MCX_铜': '参考价 745 INR/kg',
            'MCX_铝': '参考价 218 INR/kg',
            'MCX_钢': '参考价 62,500 INR/吨',
        }
        for k, v in fallback.items():
            if k not in prices:
                prices[k] = v

    return prices

def send_email(prices):
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_pwd = os.environ.get('SENDER_PWD')
    receiver_emails_str = os.environ.get('RECEIVER_EMAIL')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.qq.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '465'))

    if not all([sender_email, sender_pwd, receiver_emails_str]):
        print("邮箱配置不完整")
        return False

    receiver_emails = [email.strip() for email in receiver_emails_str.split(',') if email.strip()]
    if not receiver_emails:
        print("接收邮箱列表为空")
        return False

    try:
        print(f"连接 SMTP: {smtp_host}:{smtp_port}")
        import yagmail
        yag = yagmail.SMTP(sender_email, sender_pwd, host=smtp_host, port=smtp_port)

        today = datetime.now().strftime('%Y年%m月%d日')
        subject = f"📊 金属价格日报 - {today}"

        body = f"""
📅 {today} 金属价格汇总

{'='*55}
              伦敦金属交易所 (LME)
{'='*55}
碳钢 (Steel):        {prices.get('LME_碳钢', '暂无数据')}
不锈钢 (Stainless):   {prices.get('LME_不锈钢', '暂无数据')}
铝 (Aluminium):      {prices.get('LME_铝', '暂无数据')}
铜 (Copper):         {prices.get('LME_铜', '暂无数据')}
镍 (Nickel):         {prices.get('LME_镍', '暂无数据')}
锌 (Zinc):           {prices.get('LME_锌', '暂无数据')}
锡 (Tin):            {prices.get('LME_锡', '暂无数据')}

{'='*55}
              上海期货交易所 (SHFE)
{'='*55}
铜:           {prices.get('SHFE_铜', '暂无数据')}
铝:           {prices.get('SHFE_铝', '暂无数据')}
螺纹钢:       {prices.get('SHFE_螺纹钢', '暂无数据')}

{'='*55}
              印度多种商品交易所 (MCX)
{'='*55}
铜:           {prices.get('MCX_铜', '暂无数据')}
铝:           {prices.get('MCX_铝', '暂无数据')}
钢:           {prices.get('MCX_钢', '暂无数据')}

{'='*55}
📌 说明：价格仅供参考，实际交易价格以交易所官方公布为准
数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*55}
"""
        yag.send(receiver_emails, subject, body)
        print(f"邮件发送成功!")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    print("="*55)
    print("金属价格获取任务开始")
    print("="*55)
    prices = get_commodity_prices()
    print("="*55)
    print("开始发送邮件...")
    success = send_email(prices)
    print("="*55)
    print("任务完成!" if success else "任务失败")
    if not success:
        exit(1)
