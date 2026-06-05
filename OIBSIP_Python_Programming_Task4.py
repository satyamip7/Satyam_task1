import os
import json
import threading
from datetime import datetime
from io import BytesIO
import requests
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk


CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL = "https://openweathermap.org/img/wn/{icon}@2x.png"
GEO_IP_URL = "https://ipapi.co/json/"          # IP-based city detection
HISTORY_FILE = "history.json"                 # local file (safe to keep)


def fetch_json(url, params=None):
    r = requests.get(url, params=params, timeout=12)
    data = r.json()
    if r.status_code != 200:
        msg = data.get("message", "Unknown error")
        raise RuntimeError(f"API Error ({r.status_code}): {msg}")
    return data


class WeatherGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Advanced Weather App (Tkinter)")
        self.geometry("920x560")
        self.minsize(920, 560)

        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            messagebox.showerror(
                "API Key Missing",
                "OPENWEATHER_API_KEY set nahi hai.\n"
                "PyCharm Run Config me: OPENWEATHER_API_KEY=YOUR_KEY add karo."
            )
            self.destroy()
            return

        self.icon_img = None
        self.history = self._load_history()

        self._build_style()
        self._build_ui()
        self._refresh_history_list()

    def _build_style(self):
        try:
            style = ttk.Style(self)
            style.theme_use("clam")
            style.configure("TButton", padding=6)
            style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
            style.configure("Info.TLabel", font=("Segoe UI", 11))
        except Exception:
            pass

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        # Top controls
        top = ttk.Frame(root)
        top.pack(fill="x")

        ttk.Label(top, text="City:", style="Info.TLabel").pack(side="left")
        self.city_var = tk.StringVar()
        self.city_entry = ttk.Entry(top, textvariable=self.city_var, width=30)
        self.city_entry.pack(side="left", padx=8)
        self.city_entry.bind("<Return>", lambda e: self.search())

        ttk.Label(top, text="Units:", style="Info.TLabel").pack(side="left", padx=(12, 0))
        self.units_var = tk.StringVar(value="metric")  # metric/imperial/standard
        self.units_box = ttk.Combobox(
            top, textvariable=self.units_var,
            values=["metric", "imperial", "standard"],
            state="readonly", width=10
        )
        self.units_box.pack(side="left", padx=8)

        self.btn_search = ttk.Button(top, text="Get Weather", command=self.search)
        self.btn_search.pack(side="left", padx=6)

        self.btn_toggle = ttk.Button(top, text="Toggle °C/°F", command=self.toggle_units)
        self.btn_toggle.pack(side="left", padx=6)

        self.btn_loc = ttk.Button(top, text="Use My Location", command=self.use_my_location)
        self.btn_loc.pack(side="left", padx=6)

        # Status line
        self.status_var = tk.StringVar(value="Enter city / use location, then click Get Weather")
        ttk.Label(root, textvariable=self.status_var).pack(fill="x", pady=(8, 0))

        # Middle layout: Left = history, Right = current weather
        mid = ttk.Frame(root)
        mid.pack(fill="x", pady=10)

        # History box
        hist = ttk.Frame(mid)
        hist.pack(side="left", fill="y", padx=(0, 12))

        ttk.Label(hist, text="Search History", style="Header.TLabel").pack(anchor="w")
        self.history_list = tk.Listbox(hist, height=10, width=22)
        self.history_list.pack(fill="y", pady=(6, 0))
        self.history_list.bind("<<ListboxSelect>>", self.on_history_select)

        self.btn_clear_hist = ttk.Button(hist, text="Clear", command=self.clear_history)
        self.btn_clear_hist.pack(anchor="w", pady=(6, 0))

        # Current weather box
        cur = ttk.Frame(mid)
        cur.pack(side="left", fill="x", expand=True)

        self.icon_label = ttk.Label(cur)
        self.icon_label.grid(row=0, column=0, rowspan=7, sticky="nw", padx=(0, 16))

        self.location_var = tk.StringVar(value="Location: -")
        self.updated_var = tk.StringVar(value="Updated: -")
        self.condition_var = tk.StringVar(value="Condition: -")
        self.temp_var = tk.StringVar(value="Temp: -")
        self.humidity_var = tk.StringVar(value="Humidity: -")
        self.wind_var = tk.StringVar(value="Wind: -")
        self.extra_var = tk.StringVar(value="Extra: -")

        for i, var in enumerate([
            self.location_var, self.updated_var, self.condition_var,
            self.temp_var, self.humidity_var, self.wind_var, self.extra_var
        ]):
            ttk.Label(cur, textvariable=var, style="Info.TLabel").grid(row=i, column=1, sticky="w", pady=2)

        cur.columnconfigure(1, weight=1)

        # Forecast table
        bottom = ttk.Frame(root)
        bottom.pack(fill="both", expand=True)

        ttk.Label(bottom, text="Forecast (next ~24 hrs, 3-hour steps):", style="Header.TLabel").pack(anchor="w")

        cols = ("time", "temp", "condition")
        self.tree = ttk.Treeview(bottom, columns=cols, show="headings", height=10)
        self.tree.heading("time", text="Time")
        self.tree.heading("temp", text="Temp")
        self.tree.heading("condition", text="Condition")
        self.tree.column("time", width=180)
        self.tree.column("temp", width=120)
        self.tree.column("condition", width=520)
        self.tree.pack(fill="both", expand=True, pady=(8, 0))

    # ---------- History ----------
    def _load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data[:20]
        except Exception:
            pass
        return []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history[:20], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _add_to_history(self, city: str):
        city = city.strip()
        if not city:
            return
        # de-duplicate
        self.history = [c for c in self.history if c.lower() != city.lower()]
        self.history.insert(0, city)
        self.history = self.history[:20]
        self._save_history()
        self._refresh_history_list()

    def _refresh_history_list(self):
        self.history_list.delete(0, tk.END)
        for c in self.history:
            self.history_list.insert(tk.END, c)

    def clear_history(self):
        self.history = []
        self._save_history()
        self._refresh_history_list()

    def on_history_select(self, _event):
        sel = self.history_list.curselection()
        if not sel:
            return
        city = self.history_list.get(sel[0])
        self.city_var.set(city)
        self.search()

    # ---------- Controls ----------
    def toggle_units(self):
        # metric <-> imperial, keep standard as-is
        u = self.units_var.get().strip()
        if u == "metric":
            self.units_var.set("imperial")
        elif u == "imperial":
            self.units_var.set("metric")
        else:
            # standard -> metric
            self.units_var.set("metric")

    def use_my_location(self):
        self.btn_loc.config(state="disabled")
        self.status_var.set("Detecting your city...")

        def worker():
            try:
                data = fetch_json(GEO_IP_URL)
                city = (data.get("city") or "").strip()
                if not city:
                    raise RuntimeError("City detect nahi hua. Manual city enter karo.")
                self.after(0, lambda: self.city_var.set(city))
                self.after(0, self.search)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Location Error", str(e)))
                self.after(0, lambda: self.status_var.set("Location detection failed"))
            finally:
                self.after(0, lambda: self.btn_loc.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Weather ----------
    def search(self):
        city = self.city_var.get().strip()
        units = self.units_var.get().strip()

        if not city:
            messagebox.showwarning("Input Required", "Please enter a city name.")
            return

        self.btn_search.config(state="disabled")
        self.status_var.set("Fetching data...")

        threading.Thread(target=self._weather_worker, args=(city, units), daemon=True).start()

    def _weather_worker(self, city, units):
        try:
            params = {"q": city, "appid": self.api_key, "units": units}
            current = fetch_json(CURRENT_URL, params)
            forecast = fetch_json(FORECAST_URL, params)

            # icon
            icon_code = (current.get("weather") or [{}])[0].get("icon")
            icon_imgtk = None
            if icon_code:
                icon_resp = requests.get(ICON_URL.format(icon=icon_code), timeout=12)
                icon_resp.raise_for_status()
                img = Image.open(BytesIO(icon_resp.content)).resize((96, 96))
                icon_imgtk = ImageTk.PhotoImage(img)

            self.after(0, lambda: self._update_ui(current, forecast, units, icon_imgtk))
            self.after(0, lambda: self._add_to_history(city))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.status_var.set("Error"))
        finally:
            self.after(0, lambda: self.btn_search.config(state="normal"))

    def _update_ui(self, current, forecast, units, icon_imgtk):
        self.icon_img = icon_imgtk
        self.icon_label.config(image=self.icon_img if self.icon_img else "")

        name = current.get("name", "Unknown")
        country = current.get("sys", {}).get("country", "")
        dt = current.get("dt")
        updated_at = datetime.fromtimestamp(dt).strftime("%Y-%m-%d %H:%M:%S") if dt else "-"

        w = (current.get("weather") or [{}])[0]
        cond = f"{w.get('main', 'N/A')} - {w.get('description', 'N/A')}"

        main = current.get("main", {})
        temp = main.get("temp", "-")
        feels = main.get("feels_like", "-")
        humidity = main.get("humidity", "-")
        pressure = main.get("pressure", "-")

        wind = current.get("wind", {})
        wind_speed = wind.get("speed", "-")

        temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
        wind_unit = "m/s" if units in ["metric", "standard"] else "mph"

        self.location_var.set(f"Location: {name} {f'({country})' if country else ''}")
        self.updated_var.set(f"Updated: {updated_at}")
        self.condition_var.set(f"Condition: {cond}")
        self.temp_var.set(f"Temp: {temp} {temp_unit}   (Feels like: {feels} {temp_unit})")
        self.humidity_var.set(f"Humidity: {humidity}%")
        self.wind_var.set(f"Wind: {wind_speed} {wind_unit}")
        self.extra_var.set(f"Extra: Pressure {pressure} hPa")

        # forecast: next 8 entries (~24 hours)
        for item in self.tree.get_children():
            self.tree.delete(item)

        items = (forecast.get("list") or [])[:8]
        for it in items:
            t = it.get("dt")
            time_str = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M") if t else "-"
            tmain = it.get("main", {}).get("temp", "-")
            w2 = (it.get("weather") or [{}])[0]
            cond2 = f"{w2.get('main', 'N/A')} - {w2.get('description', 'N/A')}"
            self.tree.insert("", "end", values=(time_str, f"{tmain} {temp_unit}", cond2))

        self.status_var.set("Done")


if __name__ == "__main__":
    app = WeatherGUI()
    app.mainloop()#   T a s k   4 :   W e a t h e r   A p p  
 