import wx

class EffectOptimizerDialog(wx.Dialog):
    def __init__(self, parent, initial_values):
        super().__init__(parent, title="Optimize Your Effects", size=(400, 400))
        
        self.initial_values = initial_values
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.controls = {}
        
        # 각 효과 파라미터별 슬라이더 추가
        params = {
            "Reverb Balance (0~1)": (0.0, 1.0, 0.01, initial_values.get("rev_bal", 0.5)),
            "Reverb Size (0~1)": (0.0, 1.0, 0.01, initial_values.get("rev_size", 0.7)),
            "Low-Pass Cutoff (300~1200Hz)": (300, 1200, 10, initial_values.get("cutoff_freq", 600)),
            "Tremolo Rate (0.1~5Hz)": (0.1, 5.0, 0.1, initial_values.get("trem_rate", 1.0)),
            "EQ Gain (0~1)": (0.0, 1.0, 0.01, initial_values.get("eq_gain", 0.5)),
        }
        
        for label, (minv, maxv, step, initv) in params.items():
            vbox.Add(wx.StaticText(panel, label=label), flag=wx.TOP|wx.LEFT, border=10)
            slider = wx.Slider(panel, value=int(initv*(1/step)), minValue=int(minv*(1/step)), maxValue=int(maxv*(1/step)), style=wx.SL_HORIZONTAL)
            vbox.Add(slider, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)
            self.controls[label] = (slider, minv, maxv, step)
            
            # 현재 값 표시 텍스트
            val_txt = wx.StaticText(panel, label=f"{initv:.2f}")
            vbox.Add(val_txt, flag=wx.LEFT|wx.BOTTOM, border=10)
            slider.Bind(wx.EVT_SLIDER, lambda evt, lbl=label, txt=val_txt: self.on_slider_change(evt, lbl, txt))
        
        # OK / Cancel 버튼
        hbox_btn = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL)
        hbox_btn.Add(ok_btn)
        hbox_btn.Add(cancel_btn, flag=wx.LEFT, border=10)
        vbox.Add(hbox_btn, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
    
    def on_slider_change(self, event, label, val_txt):
        slider, minv, maxv, step = self.controls[label]
        val = slider.GetValue() * step
        val_txt.SetLabel(f"{val:.2f}")
    
    def get_values(self):
        results = {}
        for label, (slider, minv, maxv, step) in self.controls.items():
            val = slider.GetValue() * step
            key = label.split()[0].lower() 
            if "reverb" in label.lower() and "balance" in label.lower():
                results["rev_bal"] = val
            elif "reverb" in label.lower() and "size" in label.lower():
                results["rev_size"] = val
            elif "cutoff" in label.lower():
                results["cutoff_freq"] = val
            elif "tremolo" in label.lower():
                results["trem_rate"] = val
            elif "eq" in label.lower():
                results["eq_gain"] = val
        return results
