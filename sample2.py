import wx
import json
import threading
import time
from pyo import *
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

class WeatherSonificationApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Weather Data Sonification", size=(700, 500))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # --- 도시 입력 및 로드 버튼 ---
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(panel, label="Enter city name(ex.Gwangju, Seoul, LA, Vancouver):"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.city_input = wx.TextCtrl(panel)
        hbox1.Add(self.city_input, proportion=1)
        self.load_btn = wx.Button(panel, label="Load Weather Data")
        hbox1.Add(self.load_btn, flag=wx.LEFT, border=8)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.ALL, border=10)
        
        # --- 재생 속도 슬라이더 ---
        hbox_speed = wx.BoxSizer(wx.HORIZONTAL)
        hbox_speed.Add(wx.StaticText(panel, label="Playback speed (sec per hour):"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.speed_slider = wx.Slider(panel, value=1000, minValue=100, maxValue=5000, style=wx.SL_HORIZONTAL)
        hbox_speed.Add(self.speed_slider, proportion=1)
        vbox.Add(hbox_speed, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        # --- 볼륨 슬라이더 ---
        vbox.Add(wx.StaticText(panel, label="Volume"), flag=wx.LEFT|wx.TOP, border=10)
        self.vol_slider = wx.Slider(panel, value=50, minValue=0, maxValue=100, style=wx.SL_HORIZONTAL)
        vbox.Add(self.vol_slider, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        # --- EQ (하이쉘 볼륨) 슬라이더 ---
        vbox.Add(wx.StaticText(panel, label="High-frequency (UV effect) Volume"), flag=wx.LEFT|wx.TOP, border=10)
        self.eq_slider = wx.Slider(panel, value=30, minValue=0, maxValue=100, style=wx.SL_HORIZONTAL)
        vbox.Add(self.eq_slider, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        # --- Delay 시간 슬라이더 ---
        vbox.Add(wx.StaticText(panel, label="Delay Time (wind speed effect)"), flag=wx.LEFT|wx.TOP, border=10)
        self.delay_slider = wx.Slider(panel, value=500, minValue=0, maxValue=2000, style=wx.SL_HORIZONTAL)
        vbox.Add(self.delay_slider, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        # --- 그래프 그릴 영역 ---
        self.figure = Figure(figsize=(5,2))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        vbox.Add(self.canvas, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND|wx.TOP, border=10)
        
        panel.SetSizer(vbox)
        
        # pyo 서버 시작
        self.server = Server().boot()
        self.server.start()
        
        # 사운드 컴포넌트들 초기값 None
        self.osc = None
        self.noise = None
        self.rev = None
        self.pan = None
        self.high_shelf = None
        self.delay = None
        
        self.weather_data = None
        self.current_hour = 0
        self.running = False
        
        # 이벤트 연결
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load_weather)
        self.vol_slider.Bind(wx.EVT_SLIDER, self.on_volume_change)
        self.eq_slider.Bind(wx.EVT_SLIDER, self.on_eq_change)
        self.delay_slider.Bind(wx.EVT_SLIDER, self.on_delay_change)
        self.speed_slider.Bind(wx.EVT_SLIDER, self.on_speed_change)
        
        self.playback_speed = 1.0  # seconds per hour (default 1s)
        
        self.Show()
    
    def on_load_weather(self, event):
        city = self.city_input.GetValue().strip()
        if not city:
            wx.MessageBox("Please enter a city name.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        filename = f"{city.lower()}.json"
        try:
            with open(filename, "r") as f:
                self.weather_data = json.load(f)
            wx.MessageBox(f"Loaded weather data for {self.weather_data.get('city', city)}", "Info", wx.OK | wx.ICON_INFORMATION)
        except FileNotFoundError:
            wx.MessageBox(f"Weather data file '{filename}' not found.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        self.current_hour = 0
        self.init_sound()
        self.update_graph()
        
        if self.running:
            self.running = False
            time.sleep(0.2)
        self.running = True
        threading.Thread(target=self.run_sonification_loop, daemon=True).start()
    
    def init_sound(self):
        if self.osc:
            self.osc.stop()
        if self.noise:
            self.noise.stop()
        if self.rev:
            self.rev.stop()
        if self.pan:
            self.pan.stop()
        if self.high_shelf:
            self.high_shelf.stop()
        if self.delay:
            self.delay.stop()
        
        hour_data = self.weather_data["hourly"][0]
        
        freq = self.temp_to_pitch(hour_data["temp"])
        vol = self.humidity_to_volume(hour_data["humidity"])
        noise_level = self.rain_to_noise(hour_data["rain"])
        rev_mix = self.wind_to_reverb(hour_data["wind_speed"])
        pan_pos = self.wind_deg_to_pan(hour_data["wind_deg"])
        uv_level = hour_data.get("uv_index", 0)  # uv_index 없으면 0
        
        # 기본 사인파 (온도 → 피치, 습도 → 볼륨)
        self.osc = Sine(freq=freq, mul=vol)
        # 노이즈 (강수량 → 노이즈 볼륨)
        self.noise = Noise(mul=noise_level)
        self.mix = Mix([self.osc, self.noise], voices=2)
        
        # 리버브 (풍속 → 리버브 밸런스)
        self.rev = Freeverb(self.mix, size=0.8, bal=rev_mix)
        
        # 하이쉘 EQ (자외선 → 하이 주파수 볼륨 조절)
        self.high_shelf = ButHP(self.rev, freq=3000, mul=self.uv_to_eq(uv_level))
        
        # 딜레이 (풍속, 사용자가 조절 가능)
        self.delay = Delay(self.high_shelf, delay=0.5, feedback=0.3, mul=0.5)
        
        # 팬닝 (풍향 → 스테레오 위치)
        self.pan = Pan(self.delay, outs=2, pan=pan_pos).out()
    
    def run_sonification_loop(self):
        while self.running:
            hour_data = self.weather_data["hourly"][self.current_hour]
            
            freq = self.temp_to_pitch(hour_data["temp"])
            vol = self.humidity_to_volume(hour_data["humidity"])
            noise_level = self.rain_to_noise(hour_data["rain"])
            rev_mix = self.wind_to_reverb(hour_data["wind_speed"])
            pan_pos = self.wind_deg_to_pan(hour_data["wind_deg"])
            uv_level = hour_data.get("uv_index", 0)
            
            delay_time = self.delay_slider.GetValue() / 1000.0  # ms → sec
            
            self.osc.freq = freq
            base_vol = vol * (self.vol_slider.GetValue() / 100)
            self.osc.mul = base_vol
            self.noise.mul = noise_level
            self.rev.bal = rev_mix
            self.high_shelf.mul = self.eq_slider.GetValue() / 100.0
            self.delay.delay = delay_time
            self.pan.pan = pan_pos
            
            self.update_graph(self.current_hour)
            
            self.current_hour = (self.current_hour + 1) % 24
            time.sleep(self.playback_speed)  # 조절 가능한 재생 속도
    
    # --- 맵핑 함수 ---
    def temp_to_pitch(self, temp):
        return 200 + (temp - 15) * (800 - 200) / (35 - 15)
    
    def humidity_to_volume(self, humidity):
        return 0.05 + (humidity - 30) * (0.5 - 0.05) / (100 - 30)
    
    def rain_to_noise(self, rain):
        return min(rain / 10, 1) * 0.3
    
    def wind_to_reverb(self, wind_speed):
        return min(wind_speed / 10, 1) * 0.8
    
    def wind_deg_to_pan(self, wind_deg):
        return (wind_deg % 360) / 360
    
    def uv_to_eq(self, uv_index):
        # UV 0 ~ 10 → EQ gain 0 ~ 1.0 (max)
        return min(uv_index / 10, 1.0)
    
    # --- 이벤트 핸들러 ---
    def on_volume_change(self, event):
        if self.osc:
            base_vol = self.humidity_to_volume(self.weather_data["hourly"][self.current_hour]["humidity"])
            self.osc.mul = base_vol * (self.vol_slider.GetValue() / 100)
    
    def on_eq_change(self, event):
        if self.high_shelf:
            self.high_shelf.mul = self.eq_slider.GetValue() / 100.0
    
    def on_delay_change(self, event):
        if self.delay:
            self.delay.delay = self.delay_slider.GetValue() / 1000.0
    
    def on_speed_change(self, event):
        self.playback_speed = self.speed_slider.GetValue() / 1000.0  # ms → sec
    
    # --- 그래프 업데이트 ---
    def update_graph(self, current_hour=0):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        hours = [h["hour"] for h in self.weather_data["hourly"]]
        temps = [h["temp"] for h in self.weather_data["hourly"]]
        humid = [h["humidity"] for h in self.weather_data["hourly"]]
        rains = [h["rain"] for h in self.weather_data["hourly"]]
        
        ax.plot(hours, temps, label="Temperature (°C)", color="red")
        ax.plot(hours, humid, label="Humidity (%)", color="blue")
        ax.plot(hours, rains, label="Rain (mm)", color="green")
        
        ax.axvline(x=current_hour, color='gray', linestyle='--')
        ax.legend(loc='upper right')
        ax.set_xlabel("Hour")
        ax.set_title(f"Weather Data for Hour {current_hour}")
        
        self.canvas.draw()
    
    def OnClose(self, event):
        self.running = False
        time.sleep(0.3)
        self.server.stop()
        self.server.shutdown()
        self.Destroy()

if __name__ == "__main__":
    app = wx.App()
    frame = WeatherSonificationApp()
    frame.Bind(wx.EVT_CLOSE, frame.OnClose)
    app.MainLoop()
