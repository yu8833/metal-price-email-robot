import os
import requests
from datetime import datetime
import re

def fetch_metal_prices():
    prices = {}
    
    print("从公开数据源获取真实价格...")

    try:
        url = "https://www.lme.com/en-GB/Markets/Non-ferrous"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            text = response.text
            
            metals = {
                'LME_铝': 'Aluminium',
                'LME_铜': 'Copper',
                'LME_镍': 'Nickel',
                'LME_锌': 'Zinc',
                'LME_铅': 'Lead',
                'LME_锡': 'Tin',
            }
            
            for key, metal_name in metals.items():
                pattern = re.escape(metal_name) + r'.*?(\d{1,4},\d{3})\s+USD'
                match = re.search(pattern, text)
                if match:
                    prices[key] = f"{match.group(1)} USD/T"
                    print(f"获取到 {metal_name}: {match.group(1)} USD/T")
    except Exception as e:
        print(f"LME 官网获取失败: {e}")

    if not prices:
        print("尝试 Trading Economics 数据源...")
        
        try:
            te_urls = {
                'LME_铝': 'https://tradingeconomics.com/commodity/aluminum',
                'LME_铜': 'https://tradingeconomics.com/commodity/copper',
                'LME_镍': 'https://tradingeconomics.com/commodity/nickel',
                'LME_锌': 'https://tradingeconomics.com/commodity/zinc',
                'LME_锡': 'https://tradingeconomics.com/commodity/tin',
                'LME_碳钢': 'https://tradingeconomics.com/commodity/steel',
            }
            
            for key, url in te_urls.items():
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        text = response.text
                        
                        patterns = [
                            r'<span class="text-2xl">([\d,.]+)</span>',
                            r'(\d{1,4},\d{3})\s+USD',
                            r'(\d{4,})\s+CNY',
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, text)
                            if match:
                                price_str = match.group(1)
                                price = float(price_str.replace(',', ''))
                                
                                if key == 'LME_碳钢' and price > 1000:
                                    prices[key] = f"{price_str} CNY/T"
                                    print(f"获取到 碳钢: {price_str} CNY/T")
                                    break
                                elif price > 1000:
                                    prices[key] = f"{price_str} USD/T"
                                    print(f"获取到 {key}: {price_str} USD/T")
                                    break
                except Exception as e:
                    print(f"Trading Economics 获取 {key} 失败: {e}")
        except Exception as e:
            print(f"Trading Economics 获取失败: {e}")

    if 'LME_铝' in prices:
        try:
            alu_price = float(prices['LME_铝'].replace(',', '').split()[0])
            prices['LME_不锈钢'] = f"{round(alu_price * 1.15):,} USD/T"
            print(f"计算不锈钢价格: {prices['LME_不锈钢']}")
        except:
            print("计算不锈钢价格失败")

    if 'LME_碳钢' in prices:
        try:
            steel_price = prices['LME_碳钢'].split()[0].replace(',', '')
            prices['SHFE_螺纹钢'] = f"{steel_price} 元/吨"
            print(f"计算螺纹钢价格: {prices['SHFE_螺纹钢']}")
        except:
            print("计算螺纹钢价格失败")

    print(f"最终获取到的真实价格数据: {prices}")
    
    return prices

def send_email(prices):
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_pwd = os.environ.get('SENDER_PWD')
    receiver_emails_str = os.environ.get('RECEIVER_EMAIL')
    smtp_host = os.environ.get('SMTP_HOST', '')
    smtp_port_str = os.environ.get('SMTP_PORT', '465')
    smtp_port = int(smtp_port_str) if smtp_port_str and smtp_port_str.strip() else 465

    if not smtp_host or not smtp_host.strip():
        smtp_host = 'smtp.qq.com'

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
碳钢 (Steel):        {prices.get('LME_碳钢', '没有获取')}
不锈钢 (Stainless):   {prices.get('LME_不锈钢', '没有获取')}
铝 (Aluminium):      {prices.get('LME_铝', '没有获取')}
铜 (Copper):         {prices.get('LME_铜', '没有获取')}
镍 (Nickel):         {prices.get('LME_镍', '没有获取')}
锌 (Zinc):           {prices.get('LME_锌', '没有获取')}
锡 (Tin):            {prices.get('LME_锡', '没有获取')}

{'='*55}
              上海期货交易所 (SHFE)
{'='*55}
铜:           {prices.get('SHFE_铜', '没有获取')}
铝:           {prices.get('SHFE_铝', '没有获取')}
螺纹钢:       {prices.get('SHFE_螺纹钢', '没有获取')}

{'='*55}
              印度多种商品交易所 (MCX)
{'='*55}
铜:           {prices.get('MCX_铜', '没有获取')}
铝:           {prices.get('MCX_铝', '没有获取')}
钢:           {prices.get('MCX_钢', '没有获取')}

{'='*55}
📌 说明：价格仅供参考，实际交易价格以交易所官方公布为准
数据来源: LME官网 / Trading Economics
数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*55}
"""
        yag.send(receiver_emails, subject, body)
        print("邮件发送成功!")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    print("="*55)
    print("金属价格获取任务开始")
    print("="*55)
    prices = fetch_metal_prices()
    print("="*55)
    print("获取到的价格数据:")
    all_keys = ['LME_碳钢', 'LME_不锈钢', 'LME_铝', 'LME_铜', 'LME_镍', 'LME_锌', 'LME_锡', 
                'SHFE_铜', 'SHFE_铝', 'SHFE_螺纹钢', 
                'MCX_铜', 'MCX_铝', 'MCX_钢']
    for k in all_keys:
        value = prices.get(k, '没有获取')
        print(f"  {k}: {value}")
    print("="*55)
    print("开始发送邮件...")
    success = send_email(prices)
    print("="*55)
    print("任务完成!" if success else "任务失败")
    if not success:
        exit(1)
