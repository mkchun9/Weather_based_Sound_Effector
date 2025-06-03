import wx
import json
import threading
import time
from pyo import *

class WeatherSonificationApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Weather Data Sonification", size=(500, 200))
        
        # UI
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(panel, label="Enter city name:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.city_input = wx.TextCtrl(panel)
        hbox1.Add(self.city_input, proportion=1)
        self.load_btn = wx.Button(panel, label="Load Weather Data")
        hbox1.Add(self.load_btn, flag=wx.LEFT, border=8)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.ALL, border=10)
        
        vbox.Add(wx.StaticText(panel, label="Volume"), flag=wx.LEFT|wx.TOP, border=10)
        self.vol_slider = wx.Slider(panel, value=50, minValue=0, maxValue=100, style=wx.SL_HORIZONTAL)
        vbox.Add(self.vol_slider, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        panel.SetSizer(vbox)
        
        # pyo 서버 시작
        self.server = Server().boot()
        self.server.start()
        
        # 초기 사운드 설정
        self.osc = None
        self.noise = None
        self.rev = None
        self.pan = None
        
        # 이벤트 연결
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load_weather)
        self.vol_slider.Bind(wx.EVT_SLIDER, self.on_volume_change)
        
        self.weather_data = None
        self.current_hour = 0
        self.running = False
        
        self.Show()
    
    def on_load_weather(self, event):
        city = self.city_input.GetValue().strip()
        if not city:
            wx.MessageBox("Please enter a city name.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # 여기서는 city 이름에 따른 파일명으로 샘플 데이터 로드
        filename = f"{city.lower()}_24h_weather.json"
        try:
            with open(filename, "r") as f:
                self.weather_data = json.load(f)
            wx.MessageBox(f"Loaded weather data for {self.weather_data.get('city', city)}", "Info", wx.OK | wx.ICON_INFORMATION)
        except FileNotFoundError:
            wx.MessageBox(f"Weather data file '{filename}' not found.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        # 사운드 초기화
        self.init_sound()
        
        # 타이머 쓰레드로 24시간 데이터 순환
        if self.running:
            self.running = False
            time.sleep(0.2)  # 잠시 대기
        
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
        
        # 초기값 임의 설정 (온도, 습도 등 기준)
        hour_data = self.weather_data["hourly"][0]
        
        freq = self.temp_to_pitch(hour_data["temp"])
        vol = self.humidity_to_volume(hour_data["humidity"])
        noise_level = self.rain_to_noise(hour_data["rain"])
        rev_mix = self.wind_to_reverb(hour_data["wind_speed"])
        pan_pos = self.wind_deg_to_pan(hour_data["wind_deg"])
        
        self.osc = Sine(freq=freq, mul=vol)
        self.noise = Noise(mul=noise_level)
        self.mix = Mix([self.osc, self.noise], voices=2)
        
        self.rev = Freeverb(self.mix, size=0.8, bal=rev_mix)
        self.pan = Pan(self.rev, outs=2, pan=pan_pos).out()
    
    def run_sonification_loop(self):
        while self.running:
            hour_data = self.weather_data["hourly"][self.current_hour]
            freq = self.temp_to_pitch(hour_data["temp"])
            vol = self.humidity_to_volume(hour_data["humidity"])
            noise_level = self.rain_to_noise(hour_data["rain"])
            rev_mix = self.wind_to_reverb(hour_data["wind_speed"])
            pan_pos = self.wind_deg_to_pan(hour_data["wind_deg"])
            
            # 파라미터 업데이트 (실시간 변화)
            self.osc.freq = freq
            self.osc.mul = vol * (self.vol_slider.GetValue() / 100)
            self.noise.mul = noise_level
            self.rev.bal = rev_mix
            self.pan.pan = pan_pos
            
            self.current_hour = (self.current_hour + 1) % 24
            time.sleep(1)  # 1초 = 1시간의 날씨 변화
    
    # 맵핑 함수들
    def temp_to_pitch(self, temp):
        # 15도 ~ 35도 → 200Hz ~ 800Hz 선형 맵핑
        return 200 + (temp - 15) * (800 - 200) / (35 - 15)
    
    def humidity_to_volume(self, humidity):
        # 30% ~ 100% → 0.05 ~ 0.5 볼륨
        return 0.05 + (humidity - 30) * (0.5 - 0.05) / (100 - 30)
    
    def rain_to_noise(self, rain):
        # 강수량 0 ~ 10mm → 노이즈 0 ~ 0.3 볼륨
        return min(rain / 10, 1) * 0.3
    
    def wind_to_reverb(self, wind_speed):
        # 풍속 0 ~ 10m/s → 리버브 밸런스 0 ~ 0.8
        return min(wind_speed / 10, 1) * 0.8
    
    def wind_deg_to_pan(self, wind_deg):
        # 풍향 0 ~ 360도 → 팬 위치 0(좌) ~ 1(우)
        return (wind_deg % 360) / 360
    
    def on_volume_change(self, event):
        if self.osc:
            base_vol = self.humidity_to_volume(self.weather_data["hourly"][self.current_hour]["humidity"])
            self.osc.mul = base_vol * (self.vol_slider.GetValue() / 100)
    
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
