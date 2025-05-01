import datetime
import pytz
from typing import List, Dict
import streamlit as st
import time
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import re

# Common city to timezone mappings
CITY_TO_TIMEZONE = {
    # North America
    'new york': 'America/New_York',
    'los angeles': 'America/Los_Angeles',
    'chicago': 'America/Chicago',
    'toronto': 'America/Toronto',
    'vancouver': 'America/Vancouver',
    # Europe
    'london': 'Europe/London',
    'paris': 'Europe/Paris',
    'berlin': 'Europe/Berlin',
    'rome': 'Europe/Rome',
    'amsterdam': 'Europe/Amsterdam',
    # Asia & Australia
    'tokyo': 'Asia/Tokyo',
    'singapore': 'Asia/Singapore',
    'hong kong': 'Asia/Hong_Kong',
    'beijing': 'Asia/Shanghai',
    'melbourne': 'Australia/Melbourne',
    # Middle East
    'dubai': 'Asia/Dubai',
    'tel aviv': 'Asia/Jerusalem',
    'riyadh': 'Asia/Riyadh',
    'istanbul': 'Europe/Istanbul',
    'doha': 'Asia/Qatar',
    # Africa
    'cape town': 'Africa/Johannesburg',
    'cairo': 'Africa/Cairo',
    'lagos': 'Africa/Lagos',
    'nairobi': 'Africa/Nairobi',
    'casablanca': 'Africa/Casablanca'
}

# Organized cities by continent
CITIES_BY_CONTINENT = {
    'North America': ['New York', 'Los Angeles', 'Chicago', 'Toronto', 'Vancouver'],
    'Europe': ['London', 'Paris', 'Berlin', 'Rome', 'Amsterdam'],
    'Asia & Australia': ['Tokyo', 'Singapore', 'Hong Kong', 'Beijing', 'Melbourne'],
    'Middle East': ['Dubai', 'Tel Aviv', 'Riyadh', 'Istanbul', 'Doha'],
    'Africa': ['Cape Town', 'Cairo', 'Lagos', 'Nairobi', 'Casablanca']
}

class TimeZoneCoordinator:
    def __init__(self):
        self.primary_city = None
        self.comparison_cities = []
        self.local_timezone = datetime.datetime.now().astimezone().tzinfo
        self.local_timezone_name = time.tzname[0]
        
    def set_primary_city(self, city_name: str) -> bool:
        city_name = city_name.lower().strip()
        if city_name in CITY_TO_TIMEZONE:
            self.primary_city = city_name
            return True
        return False
        
    def add_comparison_city(self, city_name: str) -> bool:
        city_name = city_name.lower().strip()
        if city_name in CITY_TO_TIMEZONE and len(self.comparison_cities) < 4 and city_name != self.primary_city:
            self.comparison_cities.append(city_name)
            return True
        return False
        
    def remove_comparison_city(self, city_name: str):
        city_name = city_name.lower().strip()
        if city_name in self.comparison_cities:
            self.comparison_cities.remove(city_name)
            
    def clear_comparison_cities(self):
        self.comparison_cities.clear()
            
    def get_times(self, base_time: datetime.datetime) -> Dict[str, datetime.datetime]:
        times = {}
        if self.primary_city:
            # First, set the timezone of the input time to the primary city's timezone
            primary_tz = pytz.timezone(CITY_TO_TIMEZONE[self.primary_city])
            primary_time = primary_tz.localize(base_time.replace(tzinfo=None))
            times[self.primary_city.title()] = primary_time
            
            # Then convert to other cities' timezones
            for city in self.comparison_cities:
                city_tz = pytz.timezone(CITY_TO_TIMEZONE[city])
                times[city.title()] = primary_time.astimezone(city_tz)
        return times
    
    def get_time_period(self, time: datetime.datetime) -> str:
        hour = time.hour
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 22:
            return "Evening"
        else:
            return "Night"

def create_timeline_visualization(times: Dict[str, datetime.datetime], selected_time: datetime.datetime, coordinator: TimeZoneCoordinator):
    # Create a DataFrame for the visualization
    data = []
    for city, time in times.items():
        period = coordinator.get_time_period(time)
        data.append({
            'City': city,
            'Time': time.strftime('%H:%M'),
            'Period': period,
            'Hour': time.hour + time.minute/60
        })
    
    df = pd.DataFrame(data)
    
    # Create the figure
    fig = go.Figure()
    
    # Add timeline for each city
    for i, (city, row) in enumerate(df.iterrows()):
        # Add the timeline
        fig.add_trace(go.Scatter(
            x=[0, 24],
            y=[i, i],
            mode='lines',
            line=dict(color='gray', width=2),
            showlegend=False
        ))
        
        # Add hour markers
        for hour in range(0, 25, 3):
            fig.add_trace(go.Scatter(
                x=[hour],
                y=[i],
                mode='markers+text',
                marker=dict(size=8, color='gray'),
                text=[str(hour)],
                textposition='top center',
                showlegend=False
            ))
        
        # Add the current time marker
        fig.add_trace(go.Scatter(
            x=[row['Hour']],
            y=[i],
            mode='markers',
            marker=dict(
                size=15,
                color='#8A2BE2',
                symbol='diamond'
            ),
            name=f"{city} - {row['Time']}",
            showlegend=True
        ))
    
    # Add the vertical line for selected time
    if selected_time:
        selected_hour = selected_time.hour + selected_time.minute/60
        fig.add_shape(
            type="line",
            x0=selected_hour,
            y0=-0.5,
            x1=selected_hour,
            y1=len(times)-0.5,
            line=dict(color="#8A2BE2", width=2, dash="dash")
        )
    
    # Update layout
    fig.update_layout(
        title="Time Zone Comparison",
        xaxis_title="Hour of Day",
        yaxis_title="City",
        yaxis=dict(
            ticktext=list(times.keys()),
            tickvals=list(range(len(times))),
            tickmode="array"
        ),
        height=400,
        showlegend=True
    )
    
    return fig

def validate_time_input(time_str: str) -> bool:
    """Validate time input in various formats (HH:MM, HHMM, HMM, HH)"""
    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, time_str))
    
    # Handle different formats
    if len(digits) == 4:  # HHMM format
        hours = int(digits[:2])
        minutes = int(digits[2:])
    elif len(digits) == 3:  # HMM format
        hours = int(digits[0])
        minutes = int(digits[1:])
    elif len(digits) == 2:  # HH format
        hours = int(digits)
        minutes = 0
    else:
        return False
    
    return 0 <= hours <= 23 and 0 <= minutes <= 59

def parse_time_input(time_str: str) -> tuple[int, int]:
    """Parse time input in various formats into hours and minutes"""
    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, time_str))
    
    if len(digits) == 4:  # HHMM format
        return int(digits[:2]), int(digits[2:])
    elif len(digits) == 3:  # HMM format
        return int(digits[0]), int(digits[1:])
    elif len(digits) == 2:  # HH format
        return int(digits), 0
    else:
        raise ValueError("Invalid time format")

def get_time_period_emoji(period: str) -> str:
    """Get emoji for time period"""
    emoji_map = {
        "Morning": "🌅",
        "Afternoon": "☀️",
        "Evening": "🌆",
        "Night": "🌙"
    }
    return emoji_map.get(period, "")

def main():
    # Add custom CSS for button colors
    st.markdown("""
    <style>
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #8A2BE2;
            border-color: #8A2BE2;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #7B1FA2;
            border-color: #7B1FA2;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Add Kuromi ASCII art and theme header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 0.5rem;'>
        <pre style='color: #8A2BE2; font-size: 1.2px; line-height: 0.12; margin: 0; padding: 0; height: 1.5em;'>
   ⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣴⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣶⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣿⣶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣶⣿⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣶⣄⠀⠀⠀⠀⠀⢠⣴⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣶⣿⣿⣿⣿⣾⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⡿⠟⠿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢛⣿⣿⣿⣿⣿⣿⣼⠀⢰⣼⣿⣿⣿⣿⣿⣏⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⠟⠻⠿⣾⡿⠿⠛⠻⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⡏⢹⣶⡄⠀⠀⠀⠀⢴⣾⠛⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣿⣇⠘⠛⠀⢀⣶⣦⠀⠘⠛⢀⣿⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣈⣽⣷⣶⡖⠒⢿⠟⠲⣤⣶⣿⣉⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⠞⠉⢻⣍⣳⣴⠛⢦⣒⣋⣿⠉⠳⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠈⠉⠀⠀⠀⠈⠁⣿⠀⢴⣶⣶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣇⠀⠀⣠⠀⠀⠀⣿⣴⣿⠿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣯⣀⣀⣀⡿⣅⣀⣀⣸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠁⠀⠀⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        </pre>
    </div>
    <div style='background-color: #E6E6FA; padding: 0.5rem; border-radius: 10px; margin-bottom: 1rem;'>
        <h2 style='color: #8A2BE2; margin: 0; padding: 0.25rem; text-align: center;'>Time Zone Coordinator</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'coordinator' not in st.session_state:
        st.session_state.coordinator = TimeZoneCoordinator()
    if 'selected_time' not in st.session_state:
        st.session_state.selected_time = None
    if 'primary_city' not in st.session_state:
        st.session_state.primary_city = None
    if 'comparison_cities' not in st.session_state:
        st.session_state.comparison_cities = set()
    
    # Step 1: Primary city selection
    st.markdown("""
    <div style='background-color: #E6E6FA; padding: 0.5rem; border-radius: 10px; margin-bottom: 1rem;'>
        <h3 style='color: #8A2BE2; margin: 0; padding: 0.25rem;'>1. Select Primary City</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.primary_city:
        st.markdown(f"<p style='color: #8A2BE2;'>Current primary city: <strong>{st.session_state.primary_city}</strong></p>", unsafe_allow_html=True)
    
    # Create a single row for continent headers
    header_cols = st.columns(len(CITIES_BY_CONTINENT))
    for i, (continent, _) in enumerate(CITIES_BY_CONTINENT.items()):
        with header_cols[i]:
            st.markdown(f"<div style='text-align: center;'><h4 style='color: #8A2BE2; margin: 0; padding: 0.25rem;'>{continent}</h4></div>", unsafe_allow_html=True)
    
    # Create columns for city buttons
    city_cols = st.columns(len(CITIES_BY_CONTINENT))
    for i, (continent, cities) in enumerate(CITIES_BY_CONTINENT.items()):
        with city_cols[i]:
            for city in cities:
                button_key = f"primary_{city.lower().replace(' ', '_')}"
                if st.button(
                    city,
                    key=button_key,
                    type="primary" if city == st.session_state.primary_city else "secondary",
                    use_container_width=True
                ):
                    st.session_state.primary_city = city
                    st.session_state.coordinator.set_primary_city(city)
                    st.rerun()
    
    # Step 2: Comparison cities selection
    st.markdown("""
    <div style='background-color: #E6E6FA; padding: 0.5rem; border-radius: 10px; margin-bottom: 1rem;'>
        <h3 style='color: #8A2BE2; margin: 0; padding: 0.25rem;'>2. Select Comparison Cities (up to 4)</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<p style='color: #8A2BE2;'>Selected: {len(st.session_state.comparison_cities)}/4 cities</p>", unsafe_allow_html=True)
    
    # Create a single row for continent headers
    header_cols = st.columns(len(CITIES_BY_CONTINENT))
    for i, (continent, _) in enumerate(CITIES_BY_CONTINENT.items()):
        with header_cols[i]:
            st.markdown(f"<div style='text-align: center;'><h4 style='color: #8A2BE2; margin: 0; padding: 0.25rem;'>{continent}</h4></div>", unsafe_allow_html=True)
    
    # Create columns for city buttons
    city_cols = st.columns(len(CITIES_BY_CONTINENT))
    for i, (continent, cities) in enumerate(CITIES_BY_CONTINENT.items()):
        with city_cols[i]:
            for city in cities:
                if city != st.session_state.primary_city:
                    button_key = f"compare_{city.lower().replace(' ', '_')}"
                    is_selected = city in st.session_state.comparison_cities
                    if st.button(
                        city,
                        key=button_key,
                        type="primary" if is_selected else "secondary",
                        use_container_width=True
                    ):
                        if is_selected:
                            st.session_state.comparison_cities.remove(city)
                        elif len(st.session_state.comparison_cities) < 4:
                            st.session_state.comparison_cities.add(city)
                        else:
                            st.warning("You can only select up to 4 comparison cities")
                        st.rerun()
    
    # Update comparison cities in coordinator
    st.session_state.coordinator.clear_comparison_cities()
    for city in st.session_state.comparison_cities:
        st.session_state.coordinator.add_comparison_city(city)
    
    # Only show Step 3 if at least one comparison city is selected
    if st.session_state.comparison_cities:
        st.markdown("""
        <div style='background-color: #E6E6FA; padding: 0.5rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: #8A2BE2; margin: 0; padding: 0.25rem;'>3. Enter Desired Time in Primary Time Zone</h3>
        </div>
        """, unsafe_allow_html=True)
        
        current_time = datetime.datetime.now(st.session_state.coordinator.local_timezone)
        
        # Time input with flexible format
        time_input = st.text_input(
            "Enter time (e.g., 14:30, 1430, 230, or 14)",
            value=current_time.strftime("%H:%M"),
            help="You can enter time in various formats: HH:MM (14:30), HHMM (1430), HMM (230), or HH (14)"
        )
        
        if time_input:
            if validate_time_input(time_input):
                try:
                    hour, minute = parse_time_input(time_input)
                    selected_time = datetime.datetime.combine(
                        current_time.date(),
                        datetime.time(hour, minute)
                    )
                    st.session_state.selected_time = selected_time
                except ValueError:
                    st.error("Please enter a valid time")
            else:
                st.error("Please enter time in a valid format (HH:MM, HHMM, HMM, or HH)")
        
        # Only show Step 4 if time is selected and valid
        if st.session_state.selected_time:
            st.markdown("""
            <div style='background-color: #E6E6FA; padding: 0.5rem; border-radius: 10px; margin-bottom: 1rem;'>
                <h3 style='color: #8A2BE2; margin: 0; padding: 0.25rem;'>4. Time Comparison</h3>
            </div>
            """, unsafe_allow_html=True)
            
            times = st.session_state.coordinator.get_times(st.session_state.selected_time)
            if times:
                fig = create_timeline_visualization(times, st.session_state.selected_time, st.session_state.coordinator)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display time details without header
                for city, time in times.items():
                    period = st.session_state.coordinator.get_time_period(time)
                    emoji = get_time_period_emoji(period)
                    st.markdown(f"<p style='color: #8A2BE2;'><strong>{city}</strong>: {time.strftime('%H:%M')} {emoji} ({period})</p>", unsafe_allow_html=True)
    else:
        st.info("Please select at least one comparison city to continue")

if __name__ == "__main__":
    main()
