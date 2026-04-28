import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

# Import custom modules
from utils.weather_api import WeatherAPI
from utils.scoring_engine import TravelScoringEngine
from utils.recommendations import RecommendationEngine
from utils.travel_assistant import TravelAssistant

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Travel Intelligence Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_css():
    try:
        with open('assets/style.css', 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # If CSS file doesn't exist, use default styling
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
        }
        </style>
        """, unsafe_allow_html=True)

load_css()

# Initialize engines
@st.cache_resource
def init_engines():
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        st.error("⚠️ OpenWeatherMap API key not found! Please add your API key to the .env file")
        st.stop()
    
    weather_api = WeatherAPI(api_key)
    scoring_engine = TravelScoringEngine()
    recommendation_engine = RecommendationEngine()
    travel_assistant = TravelAssistant(weather_api, scoring_engine, recommendation_engine)
    return weather_api, scoring_engine, recommendation_engine, travel_assistant

def main():
    st.title("🌍 AI Travel Intelligence Platform")
    st.caption("Weather-Driven Travel Decision System")
    
    # Initialize
    weather_api, scoring_engine, recommendation_engine, travel_assistant = init_engines()
    
    # Sidebar
    with st.sidebar:
        st.header("🎮 Control Panel")
        
        # Travel type selection
        travel_type = st.selectbox(
            "Select Travel Type",
            ["🏖️ Beach", "🏙️ City Tour", "🥾 Adventure", "💼 Business"],
            help="Personalize recommendations based on your travel style"
        )
        
        # Extract travel type without emoji for processing
        travel_type_clean = travel_type.split()[1] if ' ' in travel_type else travel_type
        
        # City input
        st.subheader("📍 Destinations")
        default_cities = ["Mombasa,KE", "Lagos,NG", "Cancun,MX", "Montreal,CA"]
        cities_input = st.text_area(
            "Enter cities (one per line)",
            value="\n".join(default_cities),
            help="Format: City,Country Code (e.g., London,UK)"
        )
        
        cities = [c.strip() for c in cities_input.split('\n') if c.strip()]
        
        # Toggle options
        st.subheader("⚙️ Options")
        show_map = st.checkbox("Show Interactive Map", value=True)
        show_forecast = st.checkbox("Show 5-Day Forecast", value=True)
        show_risk = st.checkbox("Show Risk Analysis", value=True)
        
        # AI Assistant Chat
        st.divider()
        st.header("🤖 AI Travel Assistant")
        st.caption("Ask me anything about your trip!")
        
        user_query = st.text_input("Your question:", placeholder="e.g., Where should I travel this weekend?")
        if st.button("Ask Assistant", use_container_width=True):
            if user_query:
                with st.spinner("Analyzing..."):
                    response = travel_assistant.process_query(user_query, cities, travel_type_clean)
                    st.info(response)
            else:
                st.warning("Please enter a question")
    
    # Fetch weather data for all cities
    if cities:
        with st.spinner("🌤️ Fetching weather data for all destinations..."):
            weather_data = []
            for city in cities:
                try:
                    data = weather_api.get_current_weather(city)
                    if data:
                        # Add forecast data if requested
                        forecast = None
                        if show_forecast:
                            forecast = weather_api.get_forecast(city)
                        
                        weather_data.append({
                            'city': city,
                            'current': data,
                            'forecast': forecast
                        })
                    else:
                        st.warning(f"⚠️ Could not fetch data for {city}")
                except Exception as e:
                    st.warning(f"⚠️ Error fetching data for {city}: {str(e)}")
            
            if weather_data:
                # Calculate scores for each city
                scored_cities = []
                for data in weather_data:
                    try:
                        score_data = scoring_engine.calculate_travel_score(
                            data['current'], 
                            travel_type_clean
                        )
                        scored_cities.append({
                            'city': data['city'],
                            'current': data['current'],
                            'forecast': data['forecast'],
                            **score_data
                        })
                    except Exception as e:
                        st.warning(f"⚠️ Could not calculate score for {data['city']}: {str(e)}")
                        continue
                
                if not scored_cities:
                    st.error("No cities could be processed. Please check your API key and city names.")
                    return
                
                # Sort by score
                scored_cities.sort(key=lambda x: x['score'], reverse=True)
                
                # Create tabs
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📊 City Insights", 
                    "🏆 Destination Ranking", 
                    "📅 Forecast Intelligence",
                    "⚠️ Risk & Safety", 
                    "🗺️ Global Travel Map"
                ])
                
                # TAB 1: City Weather Insights
                with tab1:
                    st.header("📊 Real-Time Weather Insights")
                    
                    for city_data in scored_cities:
                        city_name = city_data['city'].split(',')[0]
                        with st.expander(f"📍 {city_name} - Score: {city_data['score']}/100"):
                            current = city_data['current']
                            
                            col1, col2, col3, col4, col5 = st.columns(5)
                            with col1:
                                st.metric("🌡️ Temperature", f"{current.get('temp', 'N/A')}°C")
                            with col2:
                                st.metric("💧 Humidity", f"{current.get('humidity', 'N/A')}%")
                            with col3:
                                st.metric("💨 Wind Speed", f"{current.get('wind_speed', 'N/A')} m/s")
                            with col4:
                                visibility = current.get('visibility', 'N/A')
                                st.metric("👁️ Visibility", f"{visibility} km" if visibility != 'N/A' else 'N/A')
                            with col5:
                                st.metric("📊 Pressure", f"{current.get('pressure', 'N/A')} hPa")
                            
                            # AI Travel Advice
                            try:
                                advice = recommendation_engine.generate_travel_advice(
                                    city_data['current'], 
                                    city_data['score'],
                                    travel_type_clean
                                )
                                st.info(f"💡 **AI Suggestion:** {advice}")
                            except Exception as e:
                                st.info(f"💡 **AI Suggestion:** Enjoy your trip to {city_name}!")
                
                # TAB 2: Destination Ranking Engine
                with tab2:
                    st.header("🏆 Destination Ranking Engine")
                    
                    # Create ranking dataframe
                    df_ranking = pd.DataFrame([
                        {
                            'Rank': i+1,
                            'City': d['city'].split(',')[0],
                            'Country': d['city'].split(',')[1] if ',' in d['city'] else '',
                            'Travel Score': d['score'],
                            'Status': d['status'],
                            'Temperature': d['current'].get('temp', 'N/A'),
                            'Conditions': d['current'].get('description', 'N/A')
                        }
                        for i, d in enumerate(scored_cities)
                    ])
                    
                    st.dataframe(
                        df_ranking,
                        width='stretch',
                        hide_index=True,
                        column_config={
                            "Travel Score": st.column_config.ProgressColumn(
                                "Travel Score",
                                help="0-100 scale",
                                format="%d",
                                min_value=0,
                                max_value=100
                            )
                        }
                    )
                    
                    # Show scoring weights
                    with st.expander("📊 Scoring Methodology"):
                        weights = scoring_engine.get_weights(travel_type_clean)
                        st.write(f"**Weighted factors for {travel_type}:**")
                        for factor, weight in weights.items():
                            st.progress(weight, text=f"{factor.capitalize()}: {int(weight*100)}%")
                
                # TAB 3: Travel Forecast Intelligence
                with tab3:
                    st.header("📅 5-Day Forecast Intelligence")
                    
                    forecast_available = False
                    for city_data in scored_cities:
                        if city_data.get('forecast') and isinstance(city_data['forecast'], list) and len(city_data['forecast']) > 0:
                            forecast_available = True
                            city_name = city_data['city'].split(',')[0]
                            st.subheader(f"📍 {city_name}")
                            
                            try:
                                forecast_data = scoring_engine.analyze_forecast(
                                    city_data['forecast'],
                                    travel_type_clean
                                )
                                
                                if forecast_data and forecast_data.get('daily_scores') and len(forecast_data['daily_scores']) > 0:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.success(f"🌟 **Best Travel Day:** {forecast_data['best_day']}")
                                        st.caption(f"Score: {forecast_data['best_score']}/100")
                                    
                                    with col2:
                                        st.error(f"⚠️ **Worst Travel Day:** {forecast_data['worst_day']}")
                                    
                                    # Forecast chart
                                    forecast_df = pd.DataFrame(forecast_data['daily_scores'])
                                    if not forecast_df.empty:
                                        fig = px.line(
                                            forecast_df, 
                                            x='day', 
                                            y='score',
                                            title=f"Daily Travel Score Trend - {city_name}",
                                            markers=True
                                        )
                                        fig.update_layout(height=300)
                                        st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info(f"No valid forecast scores available for {city_name}")
                            except Exception as e:
                                st.warning(f"Could not generate forecast for {city_name}: {str(e)}")
                    
                    if not forecast_available:
                        st.info("No forecast data available for any city. Try enabling 'Show 5-Day Forecast' in sidebar.")
                
                # TAB 4: Risk & Safety Analysis
                with tab4:
                    st.header("⚠️ Risk & Safety Analysis")
                    
                    risk_data = []
                    for city_data in scored_cities:
                        try:
                            risk_analysis = scoring_engine.analyze_risk(city_data['current'])
                            risk_data.append({
                                'City': city_data['city'].split(',')[0],
                                'Risk Level': risk_analysis['risk_level'],
                                'Risk Score': risk_analysis['risk_score'],
                                'Primary Concerns': ', '.join(risk_analysis['concerns'][:2]) if risk_analysis['concerns'] else 'None',
                                'Reasoning': risk_analysis['reasoning']
                            })
                        except Exception as e:
                            st.warning(f"Could not analyze risk for {city_data['city'].split(',')[0]}: {str(e)}")
                    
                    if risk_data:
                        df_risk = pd.DataFrame(risk_data)
                        
                        # Display risk table
                        st.dataframe(
                            df_risk,
                            width='stretch',
                            hide_index=True,
                            column_config={
                                "Risk Level": st.column_config.TextColumn(
                                    "Risk Level",
                                    help="Low, Medium, or High risk level"
                                ),
                                "Risk Score": st.column_config.NumberColumn(
                                    "Risk Score",
                                    help="0-100 risk score",
                                    format="%d"
                                )
                            }
                        )
                        
                        # Add color indicators
                        st.markdown("**Risk Level Indicators:**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown("🟢 **Low Risk** - Safe for travel")
                        with col2:
                            st.markdown("🟡 **Medium Risk** - Exercise caution")
                        with col3:
                            st.markdown("🔴 **High Risk** - Consider alternatives")
                        
                        # Detailed risk analysis for selected city
                        if len(scored_cities) > 0:
                            selected_city = st.selectbox(
                                "Detailed risk analysis for:",
                                [d['city'].split(',')[0] for d in scored_cities]
                            )
                            
                            city_data = next((d for d in scored_cities if d['city'].split(',')[0] == selected_city), None)
                            if city_data:
                                risk_analysis = scoring_engine.analyze_risk(city_data['current'])
                                
                                risk_emoji = "🟢" if risk_analysis['risk_level'] == "Low" else "🟡" if risk_analysis['risk_level'] == "Medium" else "🔴"
                                st.info(f"{risk_emoji} **Risk Assessment:** {risk_analysis['reasoning']}")
                                
                                if risk_analysis['concerns']:
                                    st.warning("**Specific Concerns:**")
                                    for concern in risk_analysis['concerns']:
                                        st.write(f"• {concern}")
                                else:
                                    st.success("No major safety concerns detected!")
                    else:
                        st.warning("No risk analysis data available")
                
                # TAB 5: Global Travel Map (Enhanced Version)
                with tab5:
                    st.header("🗺️ Interactive Travel Suitability Map")
                    
                    if show_map:
                        # Map style selector and controls
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            map_style_option = st.selectbox(
                                "🎨 Map Style",
                                ["🗺️ Streets", "🛰️ Satellite", "🌄 Terrain", "🎨 Light", "🌙 Dark", "🚗 Navigation"],
                                help="Choose different map visualizations"
                            )
                        with col2:
                            show_3d = st.checkbox("🏔️ 3D View", value=False)
                        with col3:
                            show_labels = st.checkbox("🏷️ City Labels", value=True)
                        with col4:
                            show_heatmap = st.checkbox("🔥 Heat Map", value=False)
                        
                        # Map style mapping
                        map_styles = {
                            "🗺️ Streets": "mapbox://styles/mapbox/streets-v12",
                            "🛰️ Satellite": "mapbox://styles/mapbox/satellite-streets-v12",
                            "🌄 Terrain": "mapbox://styles/mapbox/outdoors-v12",
                            "🎨 Light": "mapbox://styles/mapbox/light-v11",
                            "🌙 Dark": "mapbox://styles/mapbox/dark-v11",
                            "🚗 Navigation": "mapbox://styles/mapbox/navigation-day-v1"
                        }
                        
                        selected_map_style = map_styles.get(map_style_option, "mapbox://styles/mapbox/streets-v12")
                        
                        # Prepare map data
                        map_data = []
                        for city_data in scored_cities:
                            current = city_data['current']
                            if current and 'coord' in current and current['coord']:
                                lat = current['coord'].get('lat', 0)
                                lon = current['coord'].get('lon', 0)
                                
                                if lat != 0 and lon != 0:
                                    city_parts = city_data['city'].split(',')
                                    country = city_parts[1] if len(city_parts) > 1 else ''
                                    
                                    map_data.append({
                                        'lat': lat,
                                        'lon': lon,
                                        'city': city_parts[0],
                                        'country': country,
                                        'score': city_data['score'],
                                        'temperature': current.get('temp', 0),
                                        'conditions': current.get('description', 'N/A'),
                                        'status': city_data['status'],
                                        'humidity': current.get('humidity', 0),
                                        'wind': current.get('wind_speed', 0),
                                        'visibility': current.get('visibility', 'N/A')
                                    })
                        
                        if map_data:
                            df_map = pd.DataFrame(map_data)
                            df_map = df_map[(df_map['lat'] != 0) & (df_map['lon'] != 0)]
                            
                            if not df_map.empty:
                                # Color coding for markers
                                df_map['color'] = df_map['score'].apply(
                                    lambda x: [34, 197, 94, 200] if x >= 70 else  # Green
                                             ([251, 191, 36, 200] if x >= 50 else   # Yellow
                                              [239, 68, 68, 200])  # Red
                                )
                                
                                df_map['marker_size'] = df_map['score'].apply(lambda x: 20000 + (x * 800))
                                
                                # Set pitch for 3D view
                                pitch = 45 if show_3d else 0
                                
                                # Create view state
                                view_state = pdk.ViewState(
                                    latitude=df_map['lat'].mean(),
                                    longitude=df_map['lon'].mean(),
                                    zoom=2.5 if len(df_map) > 1 else 8,
                                    pitch=pitch,
                                    bearing=0
                                )
                                
                                # Create layers based on user preferences
                                layers = []
                                
                                if show_heatmap:
                                    # Heatmap layer
                                    heatmap_layer = pdk.Layer(
                                        'HeatmapLayer',
                                        data=df_map,
                                        get_position='[lon, lat]',
                                        get_weight='score',
                                        radius_pixels=40,
                                        intensity=1,
                                        threshold=0.05
                                    )
                                    layers.append(heatmap_layer)
                                else:
                                    # Scatter plot layer
                                    scatter_layer = pdk.Layer(
                                        'ScatterplotLayer',
                                        data=df_map,
                                        get_position='[lon, lat]',
                                        get_color='color',
                                        get_radius='marker_size',
                                        pickable=True,
                                        opacity=0.8,
                                        stroked=True,
                                        filled=True,
                                        get_line_color=[0, 0, 0, 100],
                                        line_width_min_pixels=1
                                    )
                                    layers.append(scatter_layer)
                                
                                # Add text labels if requested
                                if show_labels and not show_heatmap:
                                    text_layer = pdk.Layer(
                                        'TextLayer',
                                        data=df_map,
                                        get_position='[lon, lat]',
                                        get_text='city',
                                        get_size=14,
                                        get_color=[0, 0, 0, 200],
                                        get_angle=0,
                                        get_text_anchor='middle',
                                        get_alignment_baseline='center',
                                        billboard=True,
                                        size_scale=1.5,
                                        size_min_pixels=10,
                                        size_max_pixels=20
                                    )
                                    layers.append(text_layer)
                                
                                # Create tooltip
                                tooltip = {
                                    "html": """
                                        <div style="background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-width: 200px;">
                                            <b style="color: #1e3c72; font-size: 16px;">🏙️ {city}</b>
                                            <b style="color: #4a5568;"> {country}</b><br/>
                                            <hr style="margin: 5px 0;">
                                            <span style="color: #22C55E;">⭐ Score: {score}/100</span><br/>
                                            <span style="color: #FBBF24;">🌡️ Temp: {temperature}°C</span><br/>
                                            <span style="color: #4299E1;">💧 Humidity: {humidity}%</span><br/>
                                            <span style="color: #48BB78;">💨 Wind: {wind} m/s</span><br/>
                                            <span style="color: #718096;">☁️ {conditions}</span><br/>
                                            <span style="color: {status_color};">📊 {status}</span>
                                        </div>
                                    """,
                                    "style": {"backgroundColor": "transparent"}
                                }
                                
                                # Add status color for tooltip
                                df_map['status_color'] = df_map['score'].apply(
                                    lambda x: '#22C55E' if x >= 70 else '#FBBF24' if x >= 50 else '#EF4444'
                                )
                                
                                # Create deck
                                r = pdk.Deck(
                                    layers=layers,
                                    initial_view_state=view_state,
                                    tooltip=tooltip,
                                    map_style=selected_map_style
                                )
                                
                                # Display map
                                st.pydeck_chart(r, use_container_width=True)
                                
                                # Map statistics and legend
                                st.markdown("---")
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.markdown("""
                                    <div style="background: #f0fff4; padding: 10px; border-radius: 8px; border-left: 4px solid #22C55E;">
                                        <b style="color: #22543d;">🟢 Excellent (70-100)</b><br/>
                                        <small>Perfect conditions</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col2:
                                    st.markdown("""
                                    <div style="background: #fffff0; padding: 10px; border-radius: 8px; border-left: 4px solid #FBBF24;">
                                        <b style="color: #92400E;">🟡 Good (50-69)</b><br/>
                                        <small>Suitable conditions</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col3:
                                    st.markdown("""
                                    <div style="background: #fff5f5; padding: 10px; border-radius: 8px; border-left: 4px solid #EF4444;">
                                        <b style="color: #742A2A;">🔴 Poor (0-49)</b><br/>
                                        <small>Consider alternatives</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col4:
                                    avg_score = df_map['score'].mean()
                                    best_city = df_map.loc[df_map['score'].idxmax(), 'city']
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 10px; border-radius: 8px; color: white;">
                                        <b>📊 Summary</b><br/>
                                        <small>Avg Score: {avg_score:.1f}<br/>
                                        🏆 Best: {best_city}</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # Export option
                                with st.expander("📥 Export Map Data"):
                                    csv = df_map[['city', 'country', 'score', 'temperature', 'conditions', 'humidity', 'wind']].to_csv(index=False)
                                    st.download_button(
                                        label="📊 Download Cities Data (CSV)",
                                        data=csv,
                                        file_name=f"travel_destinations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv",
                                        use_container_width=True
                                    )
                            else:
                                st.warning("⚠️ No valid coordinate data available for selected cities")
                        else:
                            st.warning("⚠️ No map data available. Please check your API key and try again.")
                    else:
                        st.info("👈 Enable 'Show Interactive Map' in the sidebar to view the world map")
            else:
                st.error("No weather data could be fetched. Please check your API key and try again.")
    else:
        st.info("👈 Please enter at least one city in the sidebar to get started!")

if __name__ == "__main__":
    main()