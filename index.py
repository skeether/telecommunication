from flask import Flask, request, render_template_string
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from datetime import datetime
import urllib.parse  # Для декодирования города (Vercel кодирует %20 и т.д.)

app = Flask(__name__)

# ProxyFix на всякий случай (для совместимости)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Логгер (добавили гео-поля)
logging.basicConfig(
    filename='access.log',
    level=logging.INFO,
    format='%(asctime)s | Real IP: %(message)s | Country: %(country)s | Region: %(region)s | City: %(city)s | User-Agent: %(user_agent)s',
)

# Функция для получения IP и гео (приоритет Vercel-заголовкам)
def get_client_info():
    # IP: сначала Vercel, потом fallback
    client_ip = request.headers.get('x-vercel-forwarded-for')
    if not client_ip:
        client_ip = request.headers.get('x-forwarded-for', '').split(',')[0].strip()
    if not client_ip:
        client_ip = request.remote_addr  # Локально или прямой доступ
    
    # Гео из Vercel-заголовков (доступны только на реальном деплое)
    country_code = request.headers.get('x-vercel-ip-country')
    country = request.headers.get('x-vercel-ip-country', 'Неизвестно')  # Полное имя не всегда, но код есть
    region = request.headers.get('x-vercel-ip-country-region', '')
    city_encoded = request.headers.get('x-vercel-ip-city')
    city = urllib.parse.unquote(city_encoded) if city_encoded else 'Неизвестно'
    
    if not country_code:  # Локально или без Vercel-гео
        if client_ip in ['127.0.0.1', '::1'] or client_ip.startswith(('192.168.', '10.')):
            location = "Локальное подключение"
            country = region = city = ""
        else:
            location = "Геолокация доступна только на Vercel"
            country = region = city = "Неизвестно"
    else:
        location_parts = [city, region, country]
        location = ", ".join(part for part in location_parts if part and part != 'Неизвестно')
        if not location:
            location = "Неизвестно"
    
    return client_ip, location, country, region, city

# HTML-шаблон (как раньше)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мой сайт на Flask</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f4; color: #333; }
        .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; }
        .ip { font-weight: bold; color: #e74c3c; }
        .geo { font-weight: bold; color: #27ae60; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Добро пожаловать на мой сайт!</h1>
        <p>Это простой сайт на Python + Flask, задеплоен на Vercel.</p>
        <p class="ip">Ваш реальный IP-адрес: {{ client_ip }}</p>
        <p class="geo">Примерное местоположение: {{ location }}</p>
        <p>Данные записаны в лог.</p>
        <p>Текущая дата и время: {{ current_time }}</p>
        <p><a href="/about">О сайте</a></p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    client_ip, location, country, region, city = get_client_info()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    logging.info(client_ip, extra={'user_agent': user_agent, 'country': country, 'region': region, 'city': city})
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(
        HTML_TEMPLATE,
        client_ip=client_ip or 'Неизвестно',
        location=location,
        current_time=current_time
    )

@app.route('/about')
def about():
    client_ip, location, country, region, city = get_client_info()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    logging.info(client_ip, extra={'user_agent': user_agent, 'country': country, 'region': region, 'city': city})
    
    return f'''
    <h1>О сайте</h1>
    <p>Демонстрационный сайт на Flask + Vercel.</p>
    <p class="ip">Ваш реальный IP-адрес: {client_ip or 'Неизвестно'}</p>
    <p class="geo">Примерное местоположение: {location}</p>
    <p><a href="/">На главную</a></p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)