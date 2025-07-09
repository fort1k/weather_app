import os
import ast
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime

# Initialize logging
def log_error(message):
    with open("weather_errors.log", "a") as f:
        f.write(f"{datetime.now()} - {message}\n")

# Load config
load_dotenv()

def get_recipients():
    """Safely parse recipients with validation"""
    try:
        recipients_str = os.getenv("RECIPIENTS", "").strip()
        if not recipients_str:
            raise ValueError("RECIPIENTS is empty")
        
        # Remove all whitespace and newlines for parsing
        recipients_str = recipients_str.replace('\n', '').replace(' ', '')
        recipients = ast.literal_eval(recipients_str)
        
        # Validate structure
        valid_recipients = []
        for r in recipients:
            parts = r.split('|')
            if len(parts) != 4:
                log_error(f"Invalid recipient format: {r}")
                continue
            valid_recipients.append({
                'name': parts[0],
                'email': parts[1],
                'city': parts[2],
                'country': parts[3]
            })
        return valid_recipients
        
    except Exception as e:
        log_error(f"CRITICAL: Failed to parse recipients - {str(e)}")
        return []

def get_weather(api_key, city, country):
    """Fetch weather with robust error handling"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('cod') != 200:
            raise ValueError(f"API Error: {data.get('message', 'Unknown')}")
            
        return {
            'temp': data['main']['temp'],
            'conditions': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    except Exception as e:
        log_error(f"Weather fetch failed for {city}: {str(e)}")
        return None

def send_alert(recipient, weather):
    """Send email with attachment safety"""
    if not weather:
        return False

    msg = EmailMessage()
    msg['Subject'] = f"🌤️ Météo Alert for {recipient['city']}"
    msg['From'] = os.getenv("SENDER_EMAIL")
    msg['To'] = recipient['email']

    body = f"""
    Hola {recipient['name']}, 
    This automated email sends daily at 7:00AM. Météo sghir XD

    Your weather for {recipient['city']}, {recipient['country']}:
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
        print(f"✅ Email sent to {recipient['email']}")
        return True
    except Exception as e:
        log_error(f"Failed to email {recipient['email']}: {str(e)}")
        return False

def main():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        log_error("Missing OPENWEATHER_API_KEY")
        return

    recipients = get_recipients()
    if not recipients:
        log_error("No valid recipients found")
        return

    for person in recipients:
        weather = get_weather(api_key, person['city'], person['country'])
        if weather:
            send_alert(person, weather)

if __name__ == "__main__":
    main()