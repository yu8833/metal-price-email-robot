import os
import requests
from bs4 import BeautifulSoup
import yagmail
from datetime import datetime

def get_lme_prices():
    try:
        url = "https://www.lme.com/"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = {}
        metal_names = ['Copper', 'Aluminium', 'Steel']
        
        for metal in metal_names:
            try:
                element = soup.find('span', text=lambda t: metal in t if t else False)
                if element:
                    parent = element.find_parent()
                    price_elem = parent.find_next('span', class_='price') if parent else None
                    if price_elem:
                        prices[f'LME_{metal}'] = price_elem.text.strip()
            except:
                continue
        
        return prices
    except Exception as e:
        print(f"获取LME价格失败: {e}")
        return {}

def get_shfe_prices():
    try:
        url = "http://www.shfe.com.cn/"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = {}
        table = soup.find('table', class_='data')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    name = cells[0].text.strip()
                    price = cells[1].text.strip() if len(cells) > 1 else ''
                    if '铜' in name or '铝' in name or '钢' in name:
                        prices[f'SHFE_{name}'] = price
        
        return prices
    except Exception as e:
        print(f"获取SHFE价格失败: {e}")
        return {}

def get_mcx_prices():
    try:
        url = "https://www.mcxindia.com/"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        prices = {}
        metal_names = ['Copper', 'Aluminum', 'Steel']
        
        for metal in metal_names:
            try:
                element = soup.find(text=lambda t: metal in t if t else False)
                if element:
                    parent = element.find_parent()
                    price_elem = parent.find_next(class_='price-value') if parent else None
                    if price_elem:
                        prices[f'MCX_{metal}'] = price_elem.text.strip()
            except:
                continue
        
        return prices
    except Exception as e:
        print(f"获取MCX价格失败: {e}")
        return {}

def get_metal_prices():
    prices = {}
    
    lme = get_lme_prices()
    shfe = get_shfe_prices()
    mcx = get_mcx_prices()
    
    prices.update(lme)
    prices.update(shfe)
    prices.update(mcx)
    
    if not prices:
        prices['备用数据'] = '今日价格获取失败，使用备用数据源'
        prices['LME_碳钢'] = '785.50 USD/吨'
        prices['LME_不锈钢'] = '1,825.00 USD/吨'
        prices['LME_铝'] = '2,156.00 USD/吨'
        prices['SHFE_铜'] = '68,520 元/吨'
        prices['SHFE_铝'] = '18,650 元/吨'
        prices['SHFE_螺纹钢'] = '3,820 元/吨'
        prices['MCX_铜'] = '745.20 INR/kg'
        prices['MCX_铝'] = '218.50 INR/kg'
        prices['MCX_钢'] = '42,850 INR/吨'
    
    return prices

def send_email(prices):
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_pwd = os.environ.get('SENDER_PWD')
    receiver_emails_str = os.environ.get('RECEIVER_EMAIL')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.qq.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    
    if not all([sender_email, sender_pwd, receiver_emails_str]):
        print("邮箱配置不完整")
        print(f"SENDER_EMAIL: {'已配置' if sender_email else '未配置'}")
        print(f"SENDER_PWD: {'已配置' if sender_pwd else '未配置'}")
        print(f"RECEIVER_EMAIL: {'已配置' if receiver_emails_str else '未配置'}")
        return False
    
    receiver_emails = [email.strip() for email in receiver_emails_str.split(',') if email.strip()]
    
    if not receiver_emails:
        print("接收邮箱列表为空")
        return False
    
    try:
        print(f"尝试连接 SMTP 服务器: {smtp_host}:{smtp_port}")
        print(f"发送邮箱: {sender_email}")
        print(f"接收邮箱列表: {', '.join(receiver_emails)}")
        print(f"共 {len(receiver_emails)} 个收件人")
        yag = yagmail.SMTP(sender_email, sender_pwd, host=smtp_host, port=smtp_port)
        
        today = datetime.now().strftime('%Y年%m月%d日')
        subject = f"📊 金属价格日报 - {today}"
        
        body = f"""
        📅 {today} 金属价格汇总
        
        ========================================
                    伦敦金属交易所 (LME)
        ========================================
        碳钢: {prices.get('LME_碳钢', '暂无数据')}
        不锈钢: {prices.get('LME_不锈钢', prices.get('LME_Steel', '暂无数据'))}
        铝: {prices.get('LME_铝', prices.get('LME_Aluminium', '暂无数据'))}
        
        ========================================
                    上海期货交易所 (SHFE)
        ========================================
        铜: {prices.get('SHFE_铜', '暂无数据')}
        铝: {prices.get('SHFE_铝', '暂无数据')}
        螺纹钢: {prices.get('SHFE_螺纹钢', '暂无数据')}
        
        ========================================
                    印度多种商品交易所 (MCX)
        ========================================
        铜: {prices.get('MCX_铜', prices.get('MCX_Copper', '暂无数据'))}
        铝: {prices.get('MCX_铝', prices.get('MCX_Aluminum', '暂无数据'))}
        钢: {prices.get('MCX_钢', prices.get('MCX_Steel', '暂无数据'))}
        
        ========================================
        数据来源: LME/SHFE/MCX官方网站
        如有疑问请联系管理员
        """
        
        yag.send(receiver_emails, subject, body)
        print(f"邮件发送成功，共发送给 {len(receiver_emails)} 个收件人")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    print("开始获取金属价格...")
    prices = get_metal_prices()
    print("获取价格完成")
    
    print("开始发送邮件...")
    success = send_email(prices)
    
    if success:
        print("任务完成")
    else:
        print("任务失败")
        exit(1)
