class RecommendationEngine:
    def generate_travel_advice(self, weather_data, score, travel_type):
        """Generate personalized travel advice"""
        temp = weather_data['temp']
        humidity = weather_data['humidity']
        wind = weather_data['wind_speed']
        condition = weather_data['main_condition']
        
        advice_parts = []
        
        # Temperature advice
        if travel_type == 'Beach':
            if 25 <= temp <= 32:
                advice_parts.append("Perfect beach conditions! 🌊")
            elif temp > 32:
                advice_parts.append("Very hot - use strong SPF and stay hydrated ☀️")
            elif temp < 20:
                advice_parts.append("Cool for beach - bring a jacket 🧥")
        
        # Packing suggestions
        if temp > 28:
            advice_parts.append("Pack: Light clothing, sunscreen, hat")
        elif temp < 15:
            advice_parts.append("Pack: Warm layers, jacket, umbrella")
        
        # Humidity advice
        if humidity > 75:
            advice_parts.append("High humidity - stay hydrated, take breaks indoors 💧")
        elif humidity < 30:
            advice_parts.append("Low humidity - use moisturizer, drink water")
        
        # Wind advice
        if wind < 2:
            advice_parts.append("Calm conditions - great for outdoor activities 🎯")
        elif wind > 8:
            advice_parts.append("Windy - secure loose items, consider indoor alternatives 🌬️")
        
        # Condition-specific advice
        if condition == 'Rain':
            advice_parts.append("Rain expected - bring umbrella, plan indoor activities ☔")
        elif condition == 'Thunderstorm':
            advice_parts.append("Thunderstorms - avoid outdoor activities, stay informed ⛈️")
        
        return " ".join(advice_parts) if advice_parts else "Good conditions for your trip!"