import os
import ast
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime

# Load config
load_dotenv()


def get_recipients():
    try:
        recipients_str = os.getenv("RECIPIENTS").replace('\n', '')
        return [{
            'name': r.split('|')[0],
            'email': r.split('|')[1],
            'city': r.split('|')[2],
            'country': r.split('|')[3]
        } for r in ast.literal_eval(recipients_str)]
    except Exception as e:
        print(f"Error parsing recipients: {e}")
        return []


def get_weather(api_key, city, country):
    """Fetch weather for specific location"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return {
            'temp': data['main']['temp'],
            'conditions': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    except Exception as e:
        print(f"⚠️ Failed to fetch weather for {city}: {e}")
        return None


def send_alert(recipient, weather):
    """Send personalized email"""
    if not weather:
        return False

    msg = EmailMessage()
    msg['Subject'] = f"🌤️ Weather Alert for {recipient['city']}"
    msg['From'] = os.getenv("SENDER_EMAIL")
    msg['To'] = recipient['email']

    body = f"""
    Hola {recipient['name']}, l email hedha automated normallement yousel kol youm at 7:00AM, météo sghir XD

    Your weather alert for {recipient['city']}, {recipient['country']}:
    - Temperature: {weather['temp']}°C
    - Conditions: {weather['conditions']}
    - Humidity: {weather['humidity']}%

    Generated at: {weather['timestamp']}
    """
    msg.set_content(body.strip())

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv("SENDER_EMAIL"), os.getenv("SENDER_PASSWORD"))
            server.send_message(msg)
        print(f"✅ Alert sent to {recipient['email']}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to email {recipient['email']}: {e}")
        return False


def main():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    recipients = get_recipients()

    for person in recipients:
        weather = get_weather(api_key, person['city'], person['country'])
        if weather:
            send_alert(person, weather)


if __name__ == "__main__":
    main()
