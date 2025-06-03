import json
import time
from pyo import *

# JSON 파일에서 24시간 날씨 데이터 불러오기
def load_weather_data(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['hourly']

# 날씨 변수 맵핑 함수
def temp_to_pitch(temp):
    return 200 + (temp - 15) * (800 - 200) / (35 - 15)

def humidity_to_volume(humidity):
    return 0.05 + (humidity - 30) * (0.5 - 0.05) / (100 - 30)

def rain_to_noise(rain):
    return min(rain / 10, 1) * 0.3

def wind_to_reverb(wind_speed):
    return min(wind_speed / 10, 1) * 0.8

def wind_deg_to_pan(wind_deg):
    return (wind_deg % 360) / 360

def sonify_weather(hourly_data):
    s = Server().boot()
    s.start()

    # 초기 데이터
    hour_data = hourly_data[0]
    freq = temp_to_pitch(hour_data['temp'])
    vol = humidity_to_volume(hour_data['humidity'])
    noise_level = rain_to_noise(hour_data['rain'])
    rev_mix = wind_to_reverb(hour_data['wind_speed'])
    pan_pos = wind_deg_to_pan(hour_data['wind_deg'])

    osc = Sine(freq=freq, mul=vol)
    noise = Noise(mul=noise_level)
    mix = Mix([osc, noise], voices=2)
    rev = Freeverb(mix, size=0.8, bal=rev_mix)
    pan = Pan(rev, outs=2, pan=pan_pos).out()

    try:
        for i in range(len(hourly_data)):
            hour_data = hourly_data[i]
            freq = temp_to_pitch(hour_data['temp'])
            vol = humidity_to_volume(hour_data['humidity'])
            noise_level = rain_to_noise(hour_data['rain'])
            rev_mix = wind_to_reverb(hour_data['wind_speed'])
            pan_pos = wind_deg_to_pan(hour_data['wind_deg'])

            osc.freq = freq
            osc.mul = vol
            noise.mul = noise_level
            rev.bal = rev_mix
            pan.pan = pan_pos

            print(f"Hour {i}: Temp={hour_data['temp']}°C, Humidity={hour_data['humidity']}%, Rain={hour_data['rain']}mm, Wind={hour_data['wind_speed']}m/s")
            time.sleep(1)  # 1초마다 1시간 데이터 재생
    except KeyboardInterrupt:
        print("Sonification stopped by user.")
    finally:
        s.stop()
        s.shutdown()

if __name__ == "__main__":
    filename = "seoul.json"  # JSON 파일 경로 입력
    hourly_data = load_weather_data(filename)
    sonify_weather(hourly_data)
