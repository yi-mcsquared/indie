import datetime
import pytz
from typing import List, Dict
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import time
import plotly.graph_objects as go
import plotly.express as px

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
    # Asia
    'tokyo': 'Asia/Tokyo',
    'singapore': 'Asia/Singapore',
    'hong kong': 'Asia/Hong_Kong',
    'beijing': 'Asia/Shanghai',
    'seoul': 'Asia/Seoul',
    # Australia
    'sydney': 'Australia/Sydney',
    'melbourne': 'Australia/Melbourne',
    # Add more cities as needed
}

class TimeZoneCoordinator:
    def __init__(self):
        self.timezones: List[str] = []
        self.city_names: List[str] = []
        # Get the local timezone name
        self.local_timezone = datetime.datetime.now().astimezone().tzinfo
        self.local_timezone_name = time.tzname[0]
        
    def add_city(self, city_name: str) -> bool:
        city_name = city_name.lower().strip()
        if not city_name:
            return False
            
        if city_name in CITY_TO_TIMEZONE:
            timezone = CITY_TO_TIMEZONE[city_name]
            if len(self.timezones) < 3 and timezone not in self.timezones:
                self.timezones.append(timezone)
                self.city_names.append(city_name.title())
                return True
        return False
            
    def clear_timezones(self):
        self.timezones.clear()
        self.city_names.clear()
            
    def get_times(self, base_time: datetime.datetime) -> Dict[str, datetime.datetime]:
        times = {}
        for i, tz in enumerate(self.timezones):
            try:
                if tz in pytz.common_timezones:
                    times[self.city_names[i]] = base_time.astimezone(pytz.timezone(tz))
                else:
                    times[self.city_names[i]] = base_time
            except pytz.exceptions.UnknownTimeZoneError:
                continue
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

def main():
    st.title("Time Zone Coordinator")
    
    # Initialize session state for cities if not exists
    if 'coordinator' not in st.session_state:
        st.session_state.coordinator = TimeZoneCoordinator()
    
    # City input section
    st.header("Enter City Names")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        city1 = st.text_input("City 1", key="city1")
    with col2:
        city2 = st.text_input("City 2", key="city2")
    with col3:
        city3 = st.text_input("City 3", key="city3")
    
    if st.button("Update Timezones"):
        st.session_state.coordinator.clear_timezones()
        invalid_cities = []
        
        for city in [city1, city2, city3]:
            if city and not st.session_state.coordinator.add_city(city):
                invalid_cities.append(city)
        
        if invalid_cities:
            st.warning(f"The following cities are not recognized: {', '.join(invalid_cities)}")
    
    # Display current times
    st.header("Current Times")
    current_time = datetime.datetime.now(st.session_state.coordinator.local_timezone)
    times = st.session_state.coordinator.get_times(current_time)
    
    if times:
        for city, time in times.items():
            period = st.session_state.coordinator.get_time_period(time)
            st.write(f"{city}: {time.strftime('%H:%M')} ({period})")
    
    # Time visualization
    st.header("Time Visualization")
    if times:
        # Create a 24-hour timeline
        hours = [current_time + datetime.timedelta(hours=i) for i in range(24)]
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add traces for each city
        for i, (city, time) in enumerate(times.items()):
            # Get time periods for each hour
            periods = []
            for hour in hours:
                try:
                    timezone = CITY_TO_TIMEZONE[city.lower()]
                    if timezone in pytz.common_timezones:
                        hour_in_tz = hour.astimezone(pytz.timezone(timezone))
                    else:
                        hour_in_tz = hour
                    period = st.session_state.coordinator.get_time_period(hour_in_tz)
                    periods.append(period)
                except Exception:
                    periods.append("Unknown")
            
            # Add scatter plot for the city
            fig.add_trace(go.Scatter(
                x=hours,
                y=[i] * 24,
                mode='markers',
                name=city,
                marker=dict(
                    color=[{
                        "Morning": "yellow",
                        "Afternoon": "orange",
                        "Evening": "red",
                        "Night": "blue"
                    }[p] for p in periods],
                    size=10
                )
            ))
        
        # Update layout
        fig.update_layout(
            title="24-Hour Time Period Visualization",
            xaxis_title="Time",
            yaxis_title="City",
            yaxis=dict(
                ticktext=list(times.keys()),
                tickvals=list(range(len(times))),
                tickmode="array"
            ),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please add at least one city to see the visualization")

if __name__ == "__main__":
    main()
