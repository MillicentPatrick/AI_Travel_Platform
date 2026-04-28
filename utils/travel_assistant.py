import re
from datetime import datetime

class TravelAssistant:
    def __init__(self, weather_api, scoring_engine, recommendation_engine):
        self.weather_api = weather_api
        self.scoring_engine = scoring_engine
        self.recommendation_engine = recommendation_engine
        
        self.intent_patterns = {
            'best_destination': [
                r'(where|which city|best place).*(should|can) i.*(travel|go|visit)',
                r'recommend.*destination',
                r'best.*(place|city|destination)'
            ],
            'beach_weather': [
                r'best beach.*weather',
                r'beach.*(recommend|suggest)',
                r'where.*(sun|warm).*beach'
            ],
            'weather_comparison': [
                r'compare.*(weather|city|cities)',
                r'which.*(better|best).*weather'
            ],
            'packing_advice': [
                r'what.*(pack|bring|wear)',
                r'packing.*(list|advice|suggestion)'
            ]
        }
    
    def detect_intent(self, query):
        """Simple rules-based intent detection"""
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        return 'general'
    
    def process_query(self, query, cities, travel_type):
        """Process user query and return response"""
        intent = self.detect_intent(query)
        
        if intent == 'best_destination':
            return self.get_best_destination_recommendation(cities, travel_type)
        elif intent == 'beach_weather':
            return self.get_beach_recommendation(cities)
        elif intent == 'weather_comparison':
            return self.compare_destinations(cities)
        elif intent == 'packing_advice':
            return self.get_packing_advice(travel_type)
        else:
            return self.get_general_response(query, cities, travel_type)
    
    def get_best_destination_recommendation(self, cities, travel_type):
        """Return ranking of best destinations"""
        if not cities:
            return "Please add some cities to analyze first!"
        
        # Fetch and score all cities
        scored = []
        for city in cities:
            weather_data = self.weather_api.get_current_weather(city)
            if weather_data:
                score_data = self.scoring_engine.calculate_travel_score(weather_data, travel_type)
                scored.append({
                    'city': city.split(',')[0],
                    'score': score_data['score'],
                    'status': score_data['status']
                })
        
        if not scored:
            return "Could not fetch weather data for the specified cities."
        
        scored.sort(key=lambda x: x['score'], reverse=True)
        
        response = f"**Top Recommendations for {travel_type} Travel:**\n\n"
        for i, dest in enumerate(scored[:3], 1):
            response += f"{i}. **{dest['city']}** - Score: {dest['score']}/100 ({dest['status']})\n"
        
        if scored[0]['score'] >= 80:
            response += f"\n🌟 **Best Choice:** {scored[0]['city']} offers excellent conditions!"
        elif scored[0]['score'] >= 60:
            response += f"\n👍 **Good Choice:** {scored[0]['city']} provides suitable conditions."
        
        return response
    
    def get_beach_recommendation(self, cities):
        """Specialized beach destination recommendation"""
        if not cities:
            return "Please add some coastal cities to analyze!"
        
        beach_scores = []
        for city in cities:
            weather_data = self.weather_api.get_current_weather(city)
            if weather_data:
                temp = weather_data['temp']
                # Beach-specific scoring
                if 25 <= temp <= 32:
                    beach_score = 100
                    recommendation = "🏖️ Excellent beach weather!"
                elif 20 <= temp < 25:
                    beach_score = 70
                    recommendation = "🌊 Good beach conditions"
                elif temp > 32:
                    beach_score = 60
                    recommendation = "☀️ Very hot - good with shade"
                else:
                    beach_score = max(0, 100 - abs(28 - temp) * 8)
                    recommendation = "⚠️ Cooler beach conditions"
                
                beach_scores.append({
                    'city': city.split(',')[0],
                    'score': beach_score,
                    'recommendation': recommendation,
                    'temp': temp
                })
        
        beach_scores.sort(key=lambda x: x['score'], reverse=True)
        
        response = "**🏖️ Beach Destination Analysis:**\n\n"
        for dest in beach_scores[:3]:
            response += f"• **{dest['city']}**: {dest['temp']}°C - {dest['recommendation']}\n"
        
        return response
    
    def compare_destinations(self, cities):
        """Compare weather across destinations"""
        if len(cities) < 2:
            return "Add at least 2 cities to compare!"
        
        comparisons = []
        for city in cities:
            weather_data = self.weather_api.get_current_weather(city)
            if weather_data:
                comparisons.append({
                    'city': city.split(',')[0],
                    'temp': weather_data['temp'],
                    'condition': weather_data['description'],
                    'humidity': weather_data['humidity']
                })
        
        response = "**📊 Weather Comparison:**\n\n"
        for comp in comparisons:
            response += f"**{comp['city']}**: {comp['temp']}°C, {comp['condition']}, Humidity: {comp['humidity']}%\n"
        
        return response
    
    def get_packing_advice(self, travel_type):
        """Provide packing recommendations based on travel type"""
        packing_lists = {
            'Beach': "👙 **Beach Packing:** Swimsuit, sunscreen, towel, hat, sunglasses, light clothing, sandals",
            'City Tour': "🏙️ **City Tour Packing:** Comfortable walking shoes, camera, daypack, weather-appropriate clothing, power bank",
            'Adventure': "🥾 **Adventure Packing:** Hiking boots, backpack, water bottle, first aid kit, navigation tools, layered clothing",
            'Business': "💼 **Business Packing:** Professional attire, laptop, notebook, business cards, portable charger, formal shoes"
        }
        
        return packing_lists.get(travel_type, "Pack according to weather forecast and planned activities!")
    
    def get_general_response(self, query, cities, travel_type):
        """Fallback general response"""
        return f"I can help you with travel decisions! Try asking:\n" \
               f"• 'Where should I travel?'\n" \
               f"• 'Compare weather in my cities'\n" \
               f"• 'Best beach destination'\n" \
               f"• 'What to pack for {travel_type}?'"