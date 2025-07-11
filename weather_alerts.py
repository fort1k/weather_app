import os
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()

def get_weather(api_key, city, country):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('cod') != 200:
            raise ValueError(f"API Error: {data.get('message', 'Unknown error')}")

        tunis_tz = pytz.timezone('Africa/Tunis')
        timestamp = datetime.now(tunis_tz).strftime("%Y-%m-%d %H:%M %Z")
        
        return {
            'temp': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'wind_direction': deg_to_compass(data['wind'].get('deg', 0)),
            'visibility': f"{data.get('visibility', 'N/A')}m",
            'clouds': data['clouds'].get('all', 0),
            'conditions': data['weather'][0]['description'],
            'sunrise': format_time(data['sys']['sunrise'], tunis_tz),
            'sunset': format_time(data['sys']['sunset'], tunis_tz),
            'timestamp': timestamp
        }
    except Exception as e:
        print(f"⚠️ Failed to fetch weather: {e}")
        return None

def deg_to_compass(degrees):
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    return directions[int((degrees % 360) / 22.5)]

def format_time(timestamp, timezone):
    return datetime.fromtimestamp(timestamp, timezone).strftime("%H:%M")

def send_alert(recipient, weather):
    if not weather:
        return False

    msg = EmailMessage()
    msg['Subject'] = f"🌦️ Weather Alert for {recipient['city']}"
    msg['From'] = os.getenv('SENDER_EMAIL')
    msg['To'] = recipient['email']
    
    # Weather icon
    weather_icon = get_weather_icon(weather['conditions'].lower())
    
    # HTML Content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .card {{
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                max-width: 500px;
                margin: 0 auto;
            }}
            .header {{ color: #2c3e50; }}
            .weather-icon {{ font-size: 48px; text-align: center; }}
            .data-table {{ width: 100%; border-collapse: collapse; }}
            .data-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .data-table tr:last-child td {{ border-bottom: none; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1 class="header">🌤️ Weather Alert for {recipient['city']}, {recipient['country']}</h1>
            <div class="weather-icon">{weather_icon}</div>
            
            <table class="data-table">
                <tr><td>📅 Time</td><td>{weather['timestamp']}</td></tr>
                <tr><td>🌡️ Temperature</td><td>{weather['temp']}°C (Feels like {weather['feels_like']}°C)</td></tr>
                <tr><td>💧 Humidity</td><td>{weather['humidity']}%</td></tr>
                <tr><td>🌬️ Wind</td><td>{weather['wind_speed']} m/s {weather['wind_direction']}</td></tr>
                <tr><td>👁️ Visibility</td><td>{weather['visibility']}</td></tr>
            </table>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Weather Alert for {recipient['city']}
    Temperature: {weather['temp']}°C
    Conditions: {weather['conditions']}
    """
    
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype='html')
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv('SENDER_EMAIL'), os.getenv('SENDER_PASSWORD'))
            server.send_message(msg)
        print(f"✅ Email sent to {recipient['email']}")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

def get_weather_icon(condition):
    icons = {
        'clear': '☀️',
        'clouds': '☁️',
        'rain': '🌧️',
        'thunderstorm': '⛈️',
        'snow': '❄️',
        'mist': '🌫️'
    }
    return icons.get(condition, '🌈')
def main():
    api_key = os.getenv('OPENWEATHER_API_KEY')
    recipients = eval(os.getenv('RECIPIENTS'))
    
    for person in recipients:
        name, email, city, country = person.split('|')
        weather = get_weather(api_key, city, country)
        if weather:
            send_alert({
                'name': name,
                'email': email,
                'city': city,
                'country': country
            }, weather)

if __name__ == "__main__":
    main()