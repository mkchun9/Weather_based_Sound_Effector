import wx
import json
import threading
import time
from pyo import *

class WeatherSonificationApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Weather Data Sonification_opt(Sound Design&Programming/20251144_MInkyoungChun)", size=(700, 900))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # --- 지역 선택 및 로드 버튼 ---
        vbox.Add(wx.StaticText(panel, label="Select Region:"), flag=wx.LEFT|wx.TOP, border=10)
        self.region_list = wx.ListBox(panel, choices=["Seoul", "Gwangju", "LosAngeles", "Vancouver","Dynamic","Winter_Sample",'SmoothSeasonalKorea','KoreaSeasonalCycle'])
        vbox.Add(self.region_list, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        self.load_btn = wx.Button(panel, label="Load Weather Data")
        vbox.Add(self.load_btn, flag=wx.ALL, border=10)
        
        # --- 음악 파일 경로 및 재생 버튼 ---
        hbox_music = wx.BoxSizer(wx.HORIZONTAL)
        hbox_music.Add(wx.StaticText(panel, label="Music file path:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.music_path_input = wx.TextCtrl(panel,value='7rings.mp3')
        hbox_music.Add(self.music_path_input, proportion=1)
        self.play_music_btn = wx.Button(panel, label="Play Music")
        hbox_music.Add(self.play_music_btn, flag=wx.LEFT, border=8)
        vbox.Add(hbox_music, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        # --- 재생 속도 슬라이더 ---
        vbox.Add(wx.StaticText(panel, label="Playback speed (sec per hour)"), flag=wx.LEFT|wx.TOP, border=10)
        self.speed_slider = wx.Slider(panel, value=1000, minValue=100, maxValue=5000, style=wx.SL_HORIZONTAL)
        vbox.Add(self.speed_slider, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)

        # --- 그래프 영역 ---
        import matplotlib
        matplotlib.use('WXAgg')
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
        self.figure = Figure(figsize=(5,2))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        vbox.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        
        # --- 날씨 요약 표시 텍스트박스 ---
        vbox.Add(wx.StaticText(panel, label="Weather Summary:"), flag=wx.LEFT|wx.TOP, border=10)
        self.weather_summary = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(-1,90))
        vbox.Add(self.weather_summary, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        
        # --- 효과 고정용 표시박스 ---
        effect_box = wx.StaticBox(panel, label="Current Fixed Effect Values")
        effect_sizer = wx.StaticBoxSizer(effect_box, wx.VERTICAL)
        
        self.optimized_effects = {
            "rev_bal": 0.5,
            "rev_size": 0.7,
            "cutoff_freq": 600,
            "trem_rate": 1.0,
            "eq_gain": 0.5
        }
        self.pending_effects = self.optimized_effects.copy()  # 미확정 값
        
        self.effect_texts = {}
        for name in ["rev_bal", "rev_size", "cutoff_freq", "trem_rate", "eq_gain"]:
            txt = wx.StaticText(panel, label=f"{name}: {self.optimized_effects[name]:.2f}")
            effect_sizer.Add(txt, flag=wx.LEFT|wx.TOP, border=5)
            self.effect_texts[name] = txt
        
        self.effect_status_text = wx.StaticText(panel, label="Effects Auto-Update: ON")
        effect_sizer.Add(self.effect_status_text, flag=wx.LEFT|wx.TOP, border=5)
        
        self.fixed_hour_text = wx.StaticText(panel, label="Fixed Hour: None")
        effect_sizer.Add(self.fixed_hour_text, flag=wx.LEFT|wx.TOP, border=5)
        
        vbox.Add(effect_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        # --- 버튼들 ---
        self.optimize_btn = wx.Button(panel, label="Find your optimized effects")
        self.fix_effect_btn = wx.Button(panel, label="Fix Effect Values")
        self.toggle_effect_btn = wx.Button(panel, label="Toggle Effects Auto-Update")
        self.unfix_effect_btn = wx.Button(panel, label="Unfix Effect Values")
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.optimize_btn, flag=wx.EXPAND|wx.RIGHT, border=5)
        btn_sizer.Add(self.fix_effect_btn, flag=wx.EXPAND|wx.RIGHT, border=5)
        btn_sizer.Add(self.unfix_effect_btn, flag=wx.EXPAND|wx.RIGHT, border=5)
        btn_sizer.Add(self.toggle_effect_btn, flag=wx.EXPAND)
        vbox.Add(btn_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
        
        self.server = Server().boot()
        self.server.start()
        
        #변수 초기화
        self.music_player = None
        self.rev = None
        self.pan = None
        self.high_shelf = None
        
        self.weather_data = None
        self.current_hour = 0
        self.running = False
        self.playback_speed = 1.0
        
        self.current_pan_pos = 0.5
        self.pan_speed = 0.01
        
        self.filter_lp = None
        self.tremolo = None
        self.hrtf = None
        
        self.auto_update_effects = True
        self.fixed_hour = None  # 고정된 시간 (None이면 고정 안됨)
        
        # 이벤트 바인딩
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load_weather)
        self.play_music_btn.Bind(wx.EVT_BUTTON, self.on_play_music)
        self.speed_slider.Bind(wx.EVT_SLIDER, self.on_speed_change)
        self.optimize_btn.Bind(wx.EVT_BUTTON, self.on_open_optimizer)
        self.fix_effect_btn.Bind(wx.EVT_BUTTON, self.on_fix_effects)
        self.unfix_effect_btn.Bind(wx.EVT_BUTTON, self.on_unfix_effects)
        self.toggle_effect_btn.Bind(wx.EVT_BUTTON, self.on_toggle_effect_update)
        
        self.Show()
    
    def on_load_weather(self, event):
        region = self.region_list.GetStringSelection()
        if not region:
            wx.MessageBox("Please select a region.", "Error", wx.OK | wx.ICON_ERROR)
            return
        filename = f"{region.lower()}.json"
        try:
            with open(os.path.join('data',filename), "r", encoding="utf-8") as f:
                self.weather_data = json.load(f)
            wx.MessageBox(f"Loaded weather data for {self.weather_data.get('city', region)}", "Info", wx.OK | wx.ICON_INFORMATION)
        except FileNotFoundError:
            wx.MessageBox(f"Weather data file '{filename}' not found.", "Error", wx.OK | wx.ICON_ERROR)
            return
        self.current_hour = 0
        self.fixed_hour = None
        self.init_effects_chain()
        self.update_graph()
        self.update_weather_summary(0)
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
        if self.music_player:
            self.music_player.stop()
            self.music_player = None
        try:
            self.music_player = SfPlayer(music_path, loop=True, mul=0.5)
        except Exception as e:
            wx.MessageBox(f"Error loading music file: {e}", "Error", wx.OK | wx.ICON_ERROR)
            return
        self.init_effects_chain()
        self.music_player.out()
    
    def init_effects_chain(self):
        if not self.music_player:
            return

        # 중복 인스턴스 종료
        for eff in [self.rev, self.filter_lp, self.tremolo, self.hrtf, self.pan, self.high_shelf]:
            if eff:
                eff.stop()

        hour_data = self.weather_data["hourly"][0] if self.weather_data else {
            "temp": 10, "humidity": 50, "rain": 0, "snow": 0, 
            "wind_speed": 1, "wind_deg": 0, "uvi": 0
        }

        # 기본 파라미터 설정
        rev_bal = min(max(hour_data["humidity"] / 100, 0.0), 1.0)
        rev_size = min(max(hour_data["humidity"] / 100, 0.3), 0.9)
        cutoff_freq = 300 + (hour_data['temp'] - 10) * 40 
        trem_rate = 0.1 + (hour_data["wind_speed"]/10) * 5 #0.1~5.1Hz
        #trem_rate = 0.1 + (wind_speed / 10) * 5  # 풍속이 0~10에서 0.1~5.1Hz
        azimuth = hour_data["wind_deg"] % 360
        elevation = 20 if hour_data["wind_speed"] > 5 else 0
        pan_pos = (hour_data["wind_deg"] % 360) / 360 * 2 - 1
        eq_gain = min(hour_data.get("uvi", 0) / 10, 1.0)

        # 이펙트 체인 구성
        self.filter_lp = ButLP(self.music_player, freq=cutoff_freq)
        self.rev = Freeverb(self.filter_lp, size=rev_size, bal=rev_bal)
        self.lfo = Sine(freq=trem_rate, mul=0.5, add=0.5)
        self.tremolo = self.rev * self.lfo
        self.high_shelf = EQ(self.tremolo, freq=5000, boost=eq_gain)
        self.pan = Pan(self.high_shelf, outs=2, pan=pan_pos)
        self.hrtf = HRTF(self.pan, azimuth=azimuth, elevation=elevation)

        self.rev.out()
        self.filter_lp.out()
        self.pan.out()
        self.high_shelf.out()
        self.tremolo.out()
        self.hrtf.out()
    
    def run_sonification_loop(self):
        total_hours = len(self.weather_data['hourly'])
        
        
        while self.running:
            if not self.weather_data or not self.music_player:
                time.sleep(0.5)
                continue
            
            hour_data = self.weather_data["hourly"][self.current_hour]
            
            temp = hour_data["temp"]
            pitch_ratio = max(0.7, min(1.3, 0.7 + (temp - 10) * 0.02)) 
            #기준점 10도, 0.02: 온도 1도당 pitch_ratio 변화량

            
            rain = hour_data.get("rain", 0)
            snow = hour_data.get("snow", 0)
            vol = max((rain + snow) / 10, 0.2)
            
            humidity = hour_data["humidity"]
            rev_bal = min(max(humidity / 100, 0.0), 1.0)
            rev_size = min(max(humidity / 100, 0.3), 0.9)

            
            wind_speed = hour_data["wind_speed"]
            wind_deg = hour_data["wind_deg"] % 360
            
            uvi = hour_data.get("uvi", 0)
            eq_gain = min(uvi / 10, 1.0)
            
            cutoff_freq = 300 + (temp - 10) * 40
            self.filter_lp.freq = cutoff_freq

            
            trem_rate = 0.1 + (wind_speed / 10) * 5
            
            # 부드러운 파라미터 변화
            wx.CallAfter(setattr, self.music_player, "speed", pitch_ratio)
            wx.CallAfter(setattr, self.music_player, "mul", vol * 0.8)
            wx.CallAfter(setattr, self.rev, "bal", rev_bal)
            wx.CallAfter(setattr, self.rev, "size", rev_size)
            wx.CallAfter(setattr, self.filter_lp, "freq", cutoff_freq)
            wx.CallAfter(setattr, self.tremolo, "freq", trem_rate)

            #pan_pos = (wind_deg % 360) / 360 * 2 - 1
            #wx.CallAfter(setattr, self.pan, "pan", pan_pos)

            eq_gain = min(uvi / 10, 1.0)
            wx.CallAfter(setattr, self.high_shelf, "boost", eq_gain)

            wx.CallAfter(setattr, self.hrtf, "azimuth", wind_deg)

            
            self.update_graph(self.current_hour)
            self.update_weather_summary(self.current_hour)
            self.current_hour = (self.current_hour + 1) % total_hours
            
            time.sleep(self.playback_speed)

    
    def update_graph(self, current_hour=0):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        hours = [h["hour"] for h in self.weather_data["hourly"]]
        temps = [h["temp"] for h in self.weather_data["hourly"]]
        humid = [h["humidity"] for h in self.weather_data["hourly"]]
        rains = [h.get("rain", 0) for h in self.weather_data["hourly"]]
        snows = [h.get("snow", 0) for h in self.weather_data["hourly"]]
        wind_speeds = [h.get("wind_speed", 0) for h in self.weather_data["hourly"]]
        wind_degs = [h.get("wind_deg", 0) for h in self.weather_data["hourly"]]
        uvis = [h.get("uvi", 0) for h in self.weather_data["hourly"]]
        ax.plot(hours, temps, label="Temperature (°C)", color="red")
        #ax.plot(hours, humid, label="Humidity (%)", color="blue")
        ax.plot(hours, rains, label="Rain (mm)", color="green")
        ax.plot(hours, snows, label="Snow (mm)", color="cyan")
        ax.plot(hours, wind_speeds, label="Wind Speed (m/s)", color="orange")
        #ax.plot(hours, wind_degs, label="Wind Direction (°)", color="purple")
        ax.plot(hours, uvis, label="UV Index", color="magenta")
        ax.axvline(x=current_hour, color='gray', linestyle='--')
        ax.legend(loc='upper right')
        ax.set_xlabel("Hour")
        ax.set_title(f"Weather Data for Hour {current_hour}")
        self.canvas.draw()
    
    def update_weather_summary(self, current_hour=0):
        hour_data = self.weather_data["hourly"][current_hour]
        desc = hour_data.get("weather", [{}])[0].get("description", "No data")
        summary = (f"{current_hour} Hour: {desc.capitalize()}\n"
                   f"Temp: {hour_data['temp']} °C            "
                   f"Humidity: {hour_data['humidity']} %\n"
                   f"Wind Speed: {hour_data['wind_speed']} m/s       "
                   f"Wind Direction: {hour_data['wind_deg']}°\n"
                   f"Rain: {hour_data.get('rain',0)} mm          "
                   f"Snow: {hour_data.get('snow',0)} mm\n"
                   f"UV Index: {hour_data.get('uvi',0)}")
        self.weather_summary.SetValue(summary)
    
    def on_speed_change(self, event):
        self.playback_speed = self.speed_slider.GetValue() / 1000.0
    
    def on_open_optimizer(self, event):
        import effect_optimizer  # effect_optimizer.py 
        dlg = effect_optimizer.EffectOptimizerDialog(self, self.pending_effects)
        if dlg.ShowModal() == wx.ID_OK:
            self.pending_effects = dlg.get_values()
            self.update_pending_effect_texts()
        dlg.Destroy()
    
    def on_fix_effects(self, event):
        self.optimized_effects = self.pending_effects.copy()
        self.fixed_hour = self.current_hour
        self.update_effect_texts()
        self.fixed_hour_text.SetLabel(f"Fixed Hour: {self.fixed_hour}")
        wx.MessageBox(f"Effect values and weather data fixed at hour {self.fixed_hour}.", "Info", wx.OK|wx.ICON_INFORMATION)
    
    def on_unfix_effects(self, event):
        self.fixed_hour = None
        self.fixed_hour_text.SetLabel("Fixed Hour: None")
        wx.MessageBox("Effect and weather data fixation released. Now auto-updating.", "Info", wx.OK|wx.ICON_INFORMATION)
    
    def on_toggle_effect_update(self, event):
        self.auto_update_effects = not self.auto_update_effects
        status = "ON" if self.auto_update_effects else "OFF"
        self.effect_status_text.SetLabel(f"Effect Auto-Update: {status}")
        wx.MessageBox(f"Effect Auto-Update is now {status}.", "Info", wx.OK|wx.ICON_INFORMATION)

    def update_effect_texts(self):
        for key, val in self.optimized_effects.items():
            if key in self.effect_texts:
                if key == "cutoff_freq":
                    self.effect_texts[key].SetLabel(f"{key}: {val:.0f} Hz")
                elif key == "trem_rate":
                    self.effect_texts[key].SetLabel(f"{key}: {val:.2f} Hz")
                else:
                    self.effect_texts[key].SetLabel(f"{key}: {val:.2f}")

    def update_pending_effect_texts(self):
        # 여기선 optimized_effects만 UI에 표시 중이라 따로 구현 안함
        pass

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
