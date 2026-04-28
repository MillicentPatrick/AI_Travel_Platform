import requests
from datetime import datetime
import time

class WeatherAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def get_current_weather(self, city):
        """Fetch current weather data for a city"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            visibility = data.get('visibility' , 10000) # Default to 10km if not provided
            
            if visibility is None:
                visibility = 10000

            return {
                'temp': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'visibility': visibility / 1000, # convert to km
                'description': data['weather'][0]['description'],
                'main_condition': data['weather'][0]['main'],
                'coord': data.get('coord', {'lat':0, 'lon': 0}) # Add default if missing
            }
        except Exception as e:
            print(f"Error fetching weather for {city}: {e}")
            return None
    
    def get_forecast(self, city):
        """Fetch 5-day weather forecast"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': 40  # 5 days * 8 readings per day
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process forecast data - one reading per day (noon)
            daily_forecast = []
            dates_seen = set()
            
            for item in data['list']:
                date = item['dt_txt'].split()[0]
                if date not in dates_seen and len(daily_forecast) < 5:
                    dates_seen.add(date)
                    daily_forecast.append({
                        'date': date,
                        'day_name': datetime.strptime(date, '%Y-%m-%d').strftime('%A'),
                        'temp': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': item['wind']['speed'],
                        'description': item['weather'][0]['description'],
                        'main_condition': item['weather'][0]['main']
                    })
            
            return daily_forecast
        except Exception as e:
            print(f"Error fetching forecast for {city}: {e}")
            return None