import os
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import logging
from datetime import datetime

# Initialize logging
logging.basicConfig(
    filename='weather_alerts.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config():
    """Load and validate environment variables"""
    load_dotenv()
    required_vars = [
        'OPENWEATHER_API_KEY',
        'CITY',
        'SENDER_EMAIL',
        'SENDER_PASSWORD',
        'RECIPIENT_EMAIL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        error_msg = f"Missing environment variables: {', '.join(missing_vars)}"
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    return {
        'api_key': os.getenv('OPENWEATHER_API_KEY'),
        'city': os.getenv('CITY'),
        'sender_email': os.getenv('SENDER_EMAIL'),
        'sender_password': os.getenv('SENDER_PASSWORD'),
        'recipient_email': os.getenv('RECIPIENT_EMAIL')
    }

def get_weather(api_key, city):
    """Fetch weather data with error handling"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('cod') != 200:
            error_msg = f"API Error: {data.get('message', 'Unknown error')}"
            logging.error(error_msg)
            return None
            
        return {
            'temp': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'conditions': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logging.error(f"Weather fetch failed: {str(e)}")
        return None

def send_alert(config, weather_data):
    """Send email alert with error handling"""
    if not weather_data:
        return False

    msg = EmailMessage()
    msg['Subject'] = f"🌦️ Weather Alert for {config['city']} - {weather_data['timestamp']}"
    msg['From'] = config['sender_email']
    msg['To'] = config['recipient_email']
    
    body = f"""
    Weather Alert Report
    --------------------------
    Location: {config['city']}
    Temperature: {weather_data['temp']}°C (Feels like {weather_data['feels_like']}°C)
    Conditions: {weather_data['conditions'].title()}
    Humidity: {weather_data['humidity']}%
    Wind Speed: {weather_data['wind_speed']} km/h
    --------------------------
    Alert generated at: {weather_data['timestamp']}
    """
    msg.set_content(body.strip())

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        logging.info("Alert email sent successfully")
        return True
    except Exception as e:
        logging.error(f"Email failed: {str(e)}")
        return False

def main():
    try:
        config = load_config()
        weather_data = get_weather(config['api_key'], config['city'])
        
        if weather_data:
            send_alert(config, weather_data)
            print("Weather check completed. Check logs for details.")
        else:
            print("Failed to fetch weather data. Check weather_alerts.log")
            
    except Exception as e:
        logging.critical(f"System failure: {str(e)}")
        print(f"Critical error occurred: {e}. Check logs.")

if __name__ == "__main__":
    main()