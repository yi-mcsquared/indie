import datetime
import pytz
from typing import List, Dict
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import time
from matplotlib.widgets import Cursor

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

class TimeZoneApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Time Zone Coordinator")
        self.coordinator = TimeZoneCoordinator()
        self.city_entries = []
        self.current_time_line = None
        self.dragging = False
        self.setup_ui()
        
    def setup_ui(self):
        # City input frame
        input_frame = ttk.LabelFrame(self.root, text="Enter City Names", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Create three city input boxes
        for i in range(3):
            frame = ttk.Frame(input_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            label = ttk.Label(frame, text=f"City {i+1}:")
            label.pack(side="left", padx=5)
            
            entry = ttk.Entry(frame)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            self.city_entries.append(entry)
        
        # Update button
        update_btn = ttk.Button(input_frame, text="Update Timezones", command=self.update_timezones)
        update_btn.pack(pady=10)
        
        # Add helper text
        helper_text = "Available cities include: New York, London, Paris, Tokyo, Singapore, Sydney, etc."
        helper_label = ttk.Label(input_frame, text=helper_text, wraplength=400)
        helper_label.pack(pady=5)
        
        # Time display frame
        time_frame = ttk.LabelFrame(self.root, text="Time Display", padding="10")
        time_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.time_label = ttk.Label(time_frame, text="")
        self.time_label.pack()
        
        # Visualization frame
        viz_frame = ttk.LabelFrame(self.root, text="Time Visualization", padding="10")
        viz_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.fig = Figure(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Connect mouse events
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        
        # Start time updates
        self.update_time()
        
    def on_click(self, event):
        if event.inaxes:
            self.dragging = True
            self.update_time_line(event.xdata)
            
    def on_release(self, event):
        self.dragging = False
        
    def on_motion(self, event):
        if self.dragging and event.inaxes:
            self.update_time_line(event.xdata)
            
    def update_time_line(self, x):
        if not hasattr(self, 'ax') or not self.ax:
            return
            
        # Remove existing line if it exists
        if self.current_time_line:
            self.current_time_line.remove()
            
        # Create new vertical line
        self.current_time_line = self.ax.axvline(x=x, color='red', linestyle='--', linewidth=2)
        
        # Convert matplotlib date to datetime
        selected_time = mdates.num2date(x)
        times = self.coordinator.get_times(selected_time)
        
        time_text = "Selected times:\n"
        for city, time in times.items():
            period = self.coordinator.get_time_period(time)
            time_text += f"{city}: {time.strftime('%H:%M')} ({period})\n"
            
        self.time_label.config(text=time_text)
        self.canvas.draw()
        
    def update_timezones(self):
        self.coordinator.clear_timezones()
        invalid_cities = []
        
        for entry in self.city_entries:
            city = entry.get().strip()
            if city and not self.coordinator.add_city(city):
                invalid_cities.append(city)
        
        if invalid_cities:
            messagebox.showwarning(
                "Invalid Cities",
                f"The following cities are not recognized: {', '.join(invalid_cities)}\n"
                "Please check the spelling or try a different city."
            )
        
        self.update_visualization()
            
    def update_time(self):
        current_time = datetime.datetime.now(self.coordinator.local_timezone)
        times = self.coordinator.get_times(current_time)
        
        # Update the time line position if not dragging
        if not self.dragging and hasattr(self, 'ax') and self.ax:
            self.update_time_line(mdates.date2num(current_time))
        
        # Schedule next update
        self.root.after(1000, self.update_time)
        
    def update_visualization(self):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        
        current_time = datetime.datetime.now(self.coordinator.local_timezone)
        times = self.coordinator.get_times(current_time)
        
        if not times:
            self.canvas.draw()
            return
            
        # Create a 24-hour timeline
        hours = [current_time + datetime.timedelta(hours=i) for i in range(24)]
        hours_num = [mdates.date2num(h) for h in hours]
        
        # Plot each timezone
        for i, (city, time) in enumerate(times.items()):
            # Plot the timezone line
            self.ax.plot(hours_num, [i] * 24, '-', label=city)
            
            # Add time period indicators
            for hour, hour_num in zip(hours, hours_num):
                try:
                    timezone = CITY_TO_TIMEZONE[city.lower()]
                    if timezone in pytz.common_timezones:
                        hour_in_tz = hour.astimezone(pytz.timezone(timezone))
                    else:
                        hour_in_tz = hour
                    period = self.coordinator.get_time_period(hour_in_tz)
                    color = {
                        "Morning": "yellow",
                        "Afternoon": "orange",
                        "Evening": "red",
                        "Night": "blue"
                    }[period]
                    self.ax.scatter(hour_num, i, color=color, s=100)
                except Exception:
                    continue
        
        # Set up the plot
        self.ax.set_yticks(range(len(times)))
        self.ax.set_yticklabels(times.keys())
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.ax.legend()
        self.fig.tight_layout()
        
        # Add current time line
        self.update_time_line(mdates.date2num(current_time))
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = TimeZoneApp(root)
    root.mainloop()
