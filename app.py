import os
import requests
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import time
import threading
from PIL import Image, ImageTk
import io

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
        return None

def get_flight_details(flight_id):
    try:
        url = FLIGHT_LONG_DETAILS_HEAD + str(flight_id)
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

def format_flight_info(flight, details):
    if not flight:
        return "No flights found overhead."
    info = []
    callsign = flight.get("flight", "N/A")
    reg = flight.get("reg", "N/A")
    alt = flight.get("alt_baro", "N/A")
    spd = flight.get("spd", "N/A")
    info.append(f"[TITLE]Callsign[/TITLE] {callsign}")
    info.append(f"[TITLE]Reg[/TITLE] {reg}")
    info.append(f"[TITLE]Alt[/TITLE] {alt} ft")
    info.append(f"[TITLE]Speed[/TITLE] {spd} kt")
    if details:
        try:
            d = details.get("aircraft", {})
            model = d.get("model", {}).get("text", "")
            info.append(f"[TITLE]Model[/TITLE] {model}")
            origin = details.get("airport", {}).get("origin", {}).get("name", "")
            dest = details.get("airport", {}).get("destination", {}).get("name", "")
            info.append(f"[TITLE]From[/TITLE] {origin}")
            info.append(f"[TITLE]To[/TITLE] {dest}")
            airline = details.get("airline", {}).get("name", "")
            if airline:
                info.append(f"[TITLE]Airline[/TITLE] {airline}")
        except Exception:
            pass
    return "\n".join(info)

class FlightApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("whatplane?")
        self.attributes("-fullscreen", True)
        # self.geometry("800x480")  # 7" Pi touchscreen (now fullscreen)
        self.configure(bg="#181828")
        # --- Main content frame for side-by-side layout ---
        self.content_frame = tk.Frame(self, bg="#181828")
        self.content_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Configure grid layout
        self.content_frame.columnconfigure(0, weight=3)  # Text takes 3/4 space
        self.content_frame.rowconfigure(0, weight=1)     # Single row takes all vertical space
        
        # Text frame on left
        self.text_frame = tk.Frame(self.content_frame, bg="#181828")
        self.text_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        # Image label inside text_frame, initially hidden
        self.image_label = tk.Label(self.text_frame, bg="#222244", fg="white", text="Image Area\n(Loading...)", font=("Arial", 10), wraplength=180)
        self.image_label.pack_forget()
        
        # Add a subtle bottom bar for branding (neon accent)
        self.footer = tk.Label(
            self,
            text="✈ whatplane?",
            font=("Segoe UI", 16, "italic"),
            fg="#00ffe7",
            bg="#101018",
            anchor="e",
            padx=25,
            pady=10,
            borderwidth=0,
            highlightthickness=0
        )
        self.footer.pack(side="bottom", fill="x")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.running = True
        self.after(100, lambda: threading.Thread(target=self.update_loop, daemon=True).start())

    def update_loop(self):
        while self.running:
            flight = get_flights()
            details = get_flight_details(flight["id"] if flight else None)
            info = format_flight_info(flight, details)
            # Update all labels for neon+shadow effect
            # Custom: parse info and colorize titles
            def colorize(text, title_color="#ffae00", detail_color="#00ffe7"):
                lines = text.split("\n")
                colored = []
                for line in lines:
                    if line.startswith("[TITLE]"):
                        # Find end of title marker
                        end = line.find("[/TITLE]")
                        if end != -1:
                            title = line[7:end]
                            detail = line[end+8:]
                            colored.append((title, detail))
                        else:
                            colored.append((line, ""))
                    else:
                        colored.append(("", line))
                return colored
            colored_info = colorize(info)
            # Update labels: join with newlines, color titles differently
            def make_colored_text(colored_info, title_color="#ffae00", detail_color="#00ffe7"):
                # Use tk.Text for color, but fallback to simple text for tk.Label
                # Here, join as: title (color) + detail (default)
                return "\n".join([
                    f"{title}: {detail}" if title else detail
                    for title, detail in colored_info
                ])
            # For main label, colorize titles
            # To color titles, use tk.Text widget instead of tk.Label
            # But for now, set all text, then try to colorize titles if possible
            def update_main_label():
                try:
                    # --- Plane Image ---
                    if details:
                        img_url = None
                        try:
                            img_url = details.get("aircraft", {}).get("images", {}).get("large", [{}])[0].get("src")
                        except Exception:
                            img_url = None
                        self.image_label.config(bd=8, relief="solid", bg="#222244")
                        if img_url:
                            try:
                                response = requests.get(img_url, timeout=10)
                                img_data = response.content
                                pil_img = Image.open(io.BytesIO(img_data))
                                pil_img = pil_img.resize((200, 120), Image.LANCZOS)
                                tk_img = ImageTk.PhotoImage(pil_img)
                                self.image_label.configure(image=tk_img, text="")
                                self.image_label.image = tk_img
                            except Exception as e:
                                self.image_label.configure(image=None, text="Image error", fg="red")
                                self.image_label.image = None
                        else:
                            self.image_label.configure(image=None, text="No image", fg="red")
                            self.image_label.image = None
                        self.image_label.pack_forget()
                        self.image_label.pack(side="top", pady=(10, 10), anchor="nw")
                        self.image_label.lift()
                        # --- Clear all info widgets except image_label ---
                        for widget in self.text_frame.winfo_children():
                            if widget != self.image_label:
                                widget.destroy()
                        try:
                            text_widget = tk.Text(self.text_frame, font=("Segoe UI", 18, "bold"), fg="#00ffe7", bg="#181828", height=10, borderwidth=0, highlightthickness=0, wrap="word")
                            text_widget.tag_configure("title", foreground="#ffae00")
                            text_widget.tag_configure("detail", foreground="#00ffe7")
                            for title, detail in colored_info:
                                if title:
                                    text_widget.insert("end", f"{title}: ", "title")
                                    text_widget.insert("end", f"{detail}\n", "detail")
                                else:
                                    text_widget.insert("end", f"{detail}\n", "detail")
                            text_widget.config(state="disabled")
                            text_widget.pack(expand=True, fill="both")
                        except Exception as e:
                            for widget in self.text_frame.winfo_children():
                                if widget != self.image_label:
                                    widget.destroy()
                            fallback = tk.Label(self.text_frame, text=make_colored_text(colored_info), font=("Segoe UI", 34, "bold"), fg="#00ffe7", bg="#181828", justify="left")
                            fallback.pack(expand=True, fill="both")
                    else:
                        # No flight: clear info area, hide image
                        self.image_label.pack_forget()
                        for widget in self.text_frame.winfo_children():
                            if widget != self.image_label:
                                widget.destroy()
                except Exception as e:
                    for widget in self.text_frame.winfo_children():
                        if widget != self.image_label:
                            widget.destroy()
                    fallback = tk.Label(self.text_frame, text=make_colored_text(colored_info), font=("Segoe UI", 34, "bold"), fg="#00ffe7", bg="#181828", justify="left")
                    fallback.pack(expand=True, fill="both")
            self.after(0, update_main_label)
            for _ in range(QUERY_DELAY):
                if not self.running:
                    break
                time.sleep(1)

    def on_close(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = FlightApp()
    app.mainloop()
