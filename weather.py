import wx
from pyo import *

# 샘플 날씨 데이터 (API 연결 전용)
sample_weather_data = {
    "temperature": 25.3,
    "humidity": 60,
    "wind_speed": 3.4,
    "wind_deg": 180,
    "uv_index": 5.7,
    "description": "clear sky"
}

class WeatherSoundApp(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(400, 150))
        
        self.server = Server().boot()
        self.server.start()
        
        # 사운드 생성 (온도 → 피치, 습도 → 볼륨)
        pitch = 440 + (sample_weather_data["temperature"] - 20) * 10
        volume = 0.1 + (sample_weather_data["humidity"] / 100) * 0.9
        self.osc = Sine(freq=pitch, mul=volume).out()
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.slider = wx.Slider(panel, value=int(volume*100), minValue=0, maxValue=100,
                                style=wx.SL_HORIZONTAL)
        self.slider.Bind(wx.EVT_SLIDER, self.on_volume_change)
        
        vbox.Add(wx.StaticText(panel, label=f"Weather: {sample_weather_data['description']}"), flag=wx.ALL, border=10)
        vbox.Add(self.slider, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
        
        panel.SetSizer(vbox)
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Show()
    
    def on_volume_change(self, event):
        val = self.slider.GetValue() / 100
        self.osc.setMul(val)
    
    def on_close(self, event):
        self.server.stop()
        self.server.shutdown()
        self.Destroy()

if __name__ == "__main__":
    app = wx.App()
    WeatherSoundApp(None, title="Weather Sound Art")
    app.MainLoop()