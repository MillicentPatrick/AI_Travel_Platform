import numpy as np
from datetime import datetime

class TravelScoringEngine:
    def __init__(self):
        self.base_weights = {
            'temperature': 0.35,
            'humidity': 0.20,
            'wind': 0.20,
            'visibility': 0.15,
            'conditions': 0.10
        }
        
        self.travel_type_modifiers = {
            'Beach': {'temperature': 0.40, 'humidity': 0.25, 'wind': 0.15, 'visibility': 0.10, 'conditions': 0.10},
            'City': {'temperature': 0.30, 'humidity': 0.20, 'wind': 0.20, 'visibility': 0.20, 'conditions': 0.10},
            'Adventure': {'temperature': 0.25, 'humidity': 0.15, 'wind': 0.30, 'visibility': 0.20, 'conditions': 0.10},
            'Business': {'temperature': 0.30, 'humidity': 0.15, 'wind': 0.20, 'visibility': 0.25, 'conditions': 0.10}
        }
    
    def get_weights(self, travel_type):
        """Get weights for specific travel type"""
        return self.travel_type_modifiers.get(travel_type, self.base_weights)
    
    def score_temperature(self, temp, travel_type):
        """Score temperature based on travel type preferences"""
        if travel_type == 'Beach':
            # Beach: 25-32°C is ideal
            if 25 <= temp <= 32:
                return 100
            elif 20 <= temp < 25:
                return 70
            elif 32 < temp <= 35:
                return 60
            elif 15 <= temp < 20:
                return 40
            else:
                return max(0, 100 - abs(28 - temp) * 5)
        elif travel_type == 'Business':
            # Business: 18-24°C is ideal
            if 18 <= temp <= 24:
                return 100
            elif 24 < temp <= 28:
                return 70
            elif 12 <= temp < 18:
                return 60
            else:
                return max(0, 100 - abs(21 - temp) * 4)
        else:
            # General comfort: 20-26°C
            if 20 <= temp <= 26:
                return 100
            else:
                return max(0, 100 - abs(23 - temp) * 6)
    
    def score_humidity(self, humidity, travel_type):
        """Score humidity levels"""
        if travel_type == 'Beach':
            # Beach: slightly higher humidity OK
            if 60 <= humidity <= 80:
                return 100
            elif 80 < humidity <= 90:
                return 70
            elif 40 <= humidity < 60:
                return 80
            else:
                return max(0, 100 - abs(70 - humidity) * 2)
        else:
            # Optimal humidity is 40-60%
            if 40 <= humidity <= 60:
                return 100
            elif 60 < humidity <= 75:
                return 70
            elif 25 <= humidity < 40:
                return 60
            else:
                return max(0, 100 - abs(50 - humidity) * 1.5)
    
    def score_wind(self, wind_speed, travel_type):
        """Score wind conditions"""
        if travel_type == 'Beach':
            # Beach: light breeze ideal
            if 1 <= wind_speed <= 5:
                return 100
            elif 5 < wind_speed <= 8:
                return 70
            elif 0 <= wind_speed < 1:
                return 60
            else:
                return max(0, 100 - (wind_speed - 5) * 10)
        elif travel_type == 'Adventure':
            # Adventure: can handle higher winds
            if 0 <= wind_speed <= 10:
                return 100
            elif 10 < wind_speed <= 15:
                return 70
            else:
                return max(0, 100 - (wind_speed - 10) * 8)
        else:
            # General: low to moderate wind
            if 0 <= wind_speed <= 4:
                return 100
            elif 4 < wind_speed <= 8:
                return 75
            elif 8 < wind_speed <= 12:
                return 50
            else:
                return max(0, 100 - wind_speed * 5)
    
    def score_visibility(self, visibility_km):
        """Score visibility conditions"""
        if visibility_km is None:
            return 70  # Default score if data missing
        
        if visibility_km >= 10:
            return 100
        elif 5 <= visibility_km < 10:
            return 70
        elif 2 <= visibility_km < 5:
            return 40
        else:
            return 20
    
    def score_conditions(self, condition):
        """Score weather conditions"""
        ideal_conditions = ['Clear', 'Few clouds', 'Scattered clouds']
        moderate_conditions = ['Broken clouds', 'Light rain', 'Light snow', 'Mist']
        poor_conditions = ['Rain', 'Snow', 'Thunderstorm', 'Fog', 'Heavy rain']
        
        if condition in ideal_conditions:
            return 100
        elif condition in moderate_conditions:
            return 60
        elif condition in poor_conditions:
            return 30
        else:
            return 50
    
    def calculate_travel_score(self, weather_data, travel_type):
        """Calculate overall travel score (0-100)"""
        weights = self.get_weights(travel_type)
        
        # Calculate individual scores
        temp_score = self.score_temperature(weather_data['temp'], travel_type)
        humidity_score = self.score_humidity(weather_data['humidity'], travel_type)
        wind_score = self.score_wind(weather_data['wind_speed'], travel_type)
        visibility_score = self.score_visibility(weather_data.get('visibility', 10))
        conditions_score = self.score_conditions(weather_data.get('main_condition', 'Clear'))
        
        # Weighted average
        total_score = (
            temp_score * weights['temperature'] +
            humidity_score * weights['humidity'] +
            wind_score * weights['wind'] +
            visibility_score * weights['visibility'] +
            conditions_score * weights['conditions']
        )
        
        # Determine status
        if total_score >= 80:
            status = "Excellent 🌟"
        elif total_score >= 60:
            status = "Good 👍"
        elif total_score >= 40:
            status = "Moderate ⚠️"
        else:
            status = "Poor ❌"
        
        return {
            'score': round(total_score, 1),
            'status': status,
            'component_scores': {
                'temperature': temp_score,
                'humidity': humidity_score,
                'wind': wind_score,
                'visibility': visibility_score,
                'conditions': conditions_score
            }
        }
    
    def analyze_forecast(self, forecast_data, travel_type):
        """Analyze forecast to find best and worst travel days"""
        daily_scores = []
        
        # Check if forecast_data is valid
        if not forecast_data or not isinstance(forecast_data, list):
            return {
                'daily_scores': [],
                'best_day': "No forecast data",
                'best_score': 0,
                'worst_day': "No forecast data",
                'worst_score': 0
            }
        
        for day in forecast_data:
            try:
                # Ensure all required fields exist
                if 'visibility' not in day or day['visibility'] is None:
                    day['visibility'] = 10  # Default visibility in km
                
                # Calculate score for this day
                score_data = self.calculate_travel_score(day, travel_type)
                daily_scores.append({
                    'day': day.get('day_name', 'Unknown'),
                    'date': day.get('date', 'Unknown'),
                    'score': score_data['score'],
                    'status': score_data['status']
                })
            except Exception as e:
                print(f"Error processing forecast day: {e}")
                continue
        
        if not daily_scores:
            return {
                'daily_scores': [],
                'best_day': "No forecast data",
                'best_score': 0,
                'worst_day': "No forecast data",
                'worst_score': 0
            }
        
        best_day = max(daily_scores, key=lambda x: x['score'])
        worst_day = min(daily_scores, key=lambda x: x['score'])
        
        return {
            'daily_scores': daily_scores,
            'best_day': f"{best_day['day']} ({best_day['date']})",
            'best_score': best_day['score'],
            'worst_day': f"{worst_day['day']} ({worst_day['date']})",
            'worst_score': worst_day['score']
        }
    
    def analyze_risk(self, weather_data):
        """Analyze travel risks based on weather conditions"""
        concerns = []
        risk_score = 0
        
        # Temperature extremes
        if weather_data['temp'] > 35:
            concerns.append("Extreme heat - risk of heat exhaustion")
            risk_score += 30
        elif weather_data['temp'] < 0:
            concerns.append("Freezing temperatures - hypothermia risk")
            risk_score += 30
        
        # High wind
        if weather_data['wind_speed'] > 15:
            concerns.append("Dangerously high winds - travel disruption risk")
            risk_score += 25
        elif weather_data['wind_speed'] > 10:
            concerns.append("Strong winds - caution advised")
            risk_score += 15
        
        # Poor visibility
        visibility = weather_data.get('visibility', 10)
        if visibility < 1:
            concerns.append("Very poor visibility - driving hazard")
            risk_score += 25
        elif visibility < 3:
            concerns.append("Reduced visibility - exercise caution")
            risk_score += 10
        
        # Severe conditions
        severe_conditions = ['Thunderstorm', 'Heavy rain', 'Snow', 'Fog']
        if weather_data.get('main_condition') in severe_conditions:
            concerns.append(f"Severe weather: {weather_data.get('description', 'Unknown')}")
            risk_score += 30
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = "High"
        elif risk_score >= 25:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        reasoning = f"Weather conditions pose a {risk_level.lower()} risk for travelers."
        if concerns:
            reasoning += f" Key concerns: {', '.join(concerns[:2])}"
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'concerns': concerns,
            'reasoning': reasoning
        }