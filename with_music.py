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
        super().__init__(None, title="Weather Data Sonification with Music", size=(700, 600))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # --- 도시 입력 및 로드 버튼 ---
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(panel, label="Enter city name:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.city_input = wx.TextCtrl(panel)
        hbox1.Add(self.city_input, proportion=1)
        self.load_btn = wx.Button(panel, label="Load Weather Data")
        hbox1.Add(self.load_btn, flag=wx.LEFT, border=8)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.ALL, border=10)
        
        # --- 음악 파일 입력 및 재생 버튼 ---
        hbox_music = wx.BoxSizer(wx.HORIZONTAL)
        hbox_music.Add(wx.StaticText(panel, label="Music file path:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.music_path_input = wx.TextCtrl(panel)
        hbox_music.Add(self.music_path_input, proportion=1)
        self.play_music_btn = wx.Button(panel, label="Play Music")
        hbox_music.Add(self.play_music_btn, flag=wx.LEFT, border=8)
        vbox.Add(hbox_music, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
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
        
        # 사운드 컴포넌트 초기값
        self.music_player = None
        self.rev = None
        self.delay = None
        self.high_shelf = None
        self.pan = None
        
        self.weather_data = None
        self.current_hour = 0
        self.running = False
        
        # 기본 재생 속도 (초)
        self.playback_speed = 1.0
        
        # 이벤트 연결
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load_weather)
        self.play_music_btn.Bind(wx.EVT_BUTTON, self.on_play_music)
        self.vol_slider.Bind(wx.EVT_SLIDER, self.on_volume_change)
        self.eq_slider.Bind(wx.EVT_SLIDER, self.on_eq_change)
        self.delay_slider.Bind(wx.EVT_SLIDER, self.on_delay_change)
        self.speed_slider.Bind(wx.EVT_SLIDER, self.on_speed_change)
        
        self.Show()
    
    def on_load_weather(self, event):
        city = self.city_input.GetValue().strip()
        if not city:
            wx.MessageBox("Please enter a city name.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        filename = f"{city.lower()}.json"
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.weather_data = json.load(f)
            wx.MessageBox(f"Loaded weather data for {self.weather_data.get('city', city)}", "Info", wx.OK | wx.ICON_INFORMATION)
        except FileNotFoundError:
            wx.MessageBox(f"Weather data file '{filename}' not found.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        self.current_hour = 0
        self.init_effects_chain()
        self.update_graph()
        
        if self.running:
            self.running = False
            time.sleep(0.2)
        self.running = True
        threading.Thread(target=self.run_sonification_loop, daemon=True).start()
    
    def on_play_music(self, event):
        music_path = self.music_path_input.GetValue().strip()
        if not music_path:
            wx.MessageBox("Please enter a music file path.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # 음악 재생 중이면 종료
        if self.music_player:
            self.music_player.stop()
            self.music_player = None
        
        try:
            self.music_player = SfPlayer(music_path, loop=True, mul=0.5)
        except Exception as e:
            wx.MessageBox(f"Error loading music file: {e}", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # 효과 체인 연결 (기존 이펙트가 있으면 제거 후 새로 연결)
        self.init_effects_chain()
        self.music_player.out()
    
    def init_effects_chain(self):
        # 음악 플레이어 없으면 종료
        if not self.music_player:
            return
        
        # 기존 이펙트 종료
        if self.rev:
            self.rev.stop()
        if self.delay:
            self.delay.stop()
        if self.high_shelf:
            self.high_shelf.stop()
        if self.pan:
            self.pan.stop()
        
        # 날씨 데이터 초기값 또는 기본값
        hour_data = self.weather_data["hourly"][0] if self.weather_data else {
            "temp":25, "humidity":50, "rain":0, "wind_speed":1, "wind_deg":0, "uv_index":0
        }
        
        # 효과 파라미터 계산
        rev_bal = self.wind_to_reverb(hour_data["wind_speed"])
        delay_time = self.delay_slider.GetValue() / 1000.0  # ms to sec
        eq_gain = self.uv_to_eq(hour_data.get("uv_index",0))
        pan_pos = self.wind_deg_to_pan(hour_data["wind_deg"])
        
        # 이펙트 체인 구성
        self.rev = Freeverb(self.music_player, size=0.8, bal=rev_bal)
        self.delay = Delay(self.rev, delay=delay_time, feedback=0.3, mul=0.5)
        self.high_shelf = ButHP(self.delay, freq=3000, mul=eq_gain)
        self.pan = Pan(self.high_shelf, outs=2, pan=pan_pos)
        
        self.pan.out()
    
    def run_sonification_loop(self):
        while self.running:
            if not self.weather_data or not self.music_player:
                time.sleep(0.5)
                continue
            
            hour_data = self.weather_data["hourly"][self.current_hour]
            
            rev_bal = self.wind_to_reverb(hour_data["wind_speed"])
            delay_time = self.delay_slider.GetValue() / 1000.0
            eq_gain = self.uv_to_eq(hour_data.get("uv_index",0))
            pan_pos = self.wind_deg_to_pan(hour_data["wind_deg"])
            base_vol = self.humidity_to_volume(hour_data["humidity"])
            
            # 효과 파라미터 실시간 업데이트
            self.rev.bal = rev_bal
            self.delay.delay = delay_time
            self.high_shelf.mul = eq_gain
            self.pan.pan = pan_pos
            self.music_player.mul = base_vol * (self.vol_slider.GetValue() / 100)
            
            self.update_graph(self.current_hour)
            
            self.current_hour = (self.current_hour + 1) % 24
            time.sleep(self.playback_speed)
    
    # 맵핑 함수들
    def humidity_to_volume(self, humidity):
        return 0.05 + (humidity - 30) * (0.5 - 0.05) / (100 - 30)
    
    def wind_to_reverb(self, wind_speed):
        return min(wind_speed / 10, 1) * 0.8
    
    def uv_to_eq(self, uv_index):
        return min(uv_index / 10, 1.0)
    
    def wind_deg_to_pan(self, wind_deg):
        return (wind_deg % 360) / 360
    
    # 슬라이더 이벤트 핸들러
    def on_volume_change(self, event):
        if self.music_player:
            hour_data = self.weather_data["hourly"][self.current_hour]
            base_vol = self.humidity_to_volume(hour_data["humidity"])
            self.music_player.mul = base_vol * (self.vol_slider.GetValue() / 100)
    
    def on_eq_change(self, event):
        if self.high_shelf:
            self.high_shelf.mul = self.eq_slider.GetValue() / 100.0
    
    def on_delay_change(self, event):
        if self.delay:
            self.delay.delay = self.delay_slider.GetValue() / 1000.0
    
    def on_speed_change(self, event):
        self.playback_speed = self.speed_slider.GetValue() / 1000.0
    
    # 그래프 업데이트 (이전과 동일)
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
