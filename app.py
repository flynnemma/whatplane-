import os
import requests
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import time
import threading

# Load environment variables from .env
load_dotenv()

BOUNDS_BOX = os.getenv("BOUNDS_BOX", "51.4,51.6,-0.6,0.2")  # Default: London area
QUERY_DELAY = 30  # seconds

FLIGHT_SEARCH_HEAD = "https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds="
FLIGHT_SEARCH_TAIL = "&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0&ems=1&limit=10"
FLIGHT_SEARCH_URL = FLIGHT_SEARCH_HEAD + BOUNDS_BOX + FLIGHT_SEARCH_TAIL
FLIGHT_LONG_DETAILS_HEAD = "https://data-live.flightradar24.com/clickhandler/?flight="

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "cache-control": "no-store, no-cache, must-revalidate, post-check=0, pre-check=0",
    "accept": "application/json"
}

def get_flights():
    try:
        response = requests.get(FLIGHT_SEARCH_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        flights = []
        for k, v in data.items():
            if isinstance(v, list) and len(v) > 2:
                flights.append({
                    'id': k,
                    'hex': v[0],
                    'lat': v[1],
                    'lon': v[2],
                    'alt_baro': v[4],
                    'spd': v[5],
                    'flight': v[13] if len(v) > 13 else '',
                    'reg': v[9] if len(v) > 9 else ''
                })
        return flights[0] if flights else None
    except Exception as e:
        print(f"Error fetching flights: {e}")
        return None

def get_flight_details(flight_id):
    try:
        url = FLIGHT_LONG_DETAILS_HEAD + str(flight_id)
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching flight details: {e}")
        return None

def format_flight_info(flight, details):
    if not flight:
        return "No flights found overhead."
    info = []
    callsign = flight.get("flight", "N/A")
    reg = flight.get("reg", "N/A")
    alt = flight.get("alt_baro", "N/A")
    spd = flight.get("spd", "N/A")
    info.append(f"Callsign: {callsign}")
    info.append(f"Reg: {reg}")
    info.append(f"Alt: {alt} ft")
    info.append(f"Speed: {spd} kt")
    if details:
        try:
            d = details.get("aircraft", {})
            model = d.get("model", {}).get("text", "")
            info.append(f"Model: {model}")
            origin = details.get("airport", {}).get("origin", {}).get("name", "")
            dest = details.get("airport", {}).get("destination", {}).get("name", "")
            info.append(f"From: {origin}")
            info.append(f"To: {dest}")
        except Exception:
            pass
    return "\n".join(info)

class FlightApp(tk.Tk):
    def __init__(self):
        print("Initializing FlightApp UI...")
        super().__init__()
        print("Tk root initialized.")
        self.title("whatplane?")
        self.geometry("800x480")  # 7" Pi touchscreen
        self.configure(bg="#222244")
        self.label = tk.Label(self, text="Loading...", font=("Arial", 32), fg="#FFA500", bg="#222244", justify="left")
        self.label.pack(expand=True, fill="both")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.running = True
        print("Scheduling update thread...")
        self.after(100, lambda: threading.Thread(target=self.update_loop, daemon=True).start())

    def update_loop(self):
        print("Entered update_loop.")
        while self.running:
            flight = get_flights()
            details = get_flight_details(flight["id"] if flight else None)
            info = format_flight_info(flight, details)
            print(info)
            self.after(0, lambda: self.label.config(text=info))
            for _ in range(QUERY_DELAY):
                if not self.running:
                    break
                time.sleep(1)

    def on_close(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    print("Starting FlightApp...")
    app = FlightApp()
    print("FlightApp initialized, entering mainloop.")
    app.mainloop()
    print("Exited mainloop.")
