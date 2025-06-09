# 🎧 Weather-Sound Interaction System

 날씨 데이터를 기반으로 음향 효과를 실시간으로 변화시키는 사운드 인터랙션 프로젝트입니다. \
온도, 습도, 풍향, 풍속, 자외선, 강수량 등의 기상 요소가 음악의 필터, 리버브, 피치, 볼륨 등 다양한 파라미터에 실시간으로 반영되어 풍부한 음향 효과를 제공합니다.

---

## 🌦️ Weather-Based Sound Effects Chain

| 날씨 요소 | 적용 효과 | 설명 |
|-----------|-----------|------|
| **온도** | 🎚 저역 통과 필터 (Low-Pass Filter, `ButLP`)<br>🎵 피치 (재생 속도) 조절 | 온도가 높을수록 필터 컷오프 주파수가 올라가고, 음악이 밝아지며 빨라집니다. 온도가 낮으면 소리는 어둡고 느려집니다. |
| **습도** | 🌫 리버브 (Freeverb) | 습도가 높을수록 잔향과 공간감이 풍부해집니다. |
| **풍속** | 🌬 트레몰로 (Amplitude Modulation) | 바람이 강할수록 진동 속도가 빨라지고, 소리에 흔들림이 생깁니다. |
| **풍향** | 🧭 3D 공간감 (HRTF) | 풍향에 따라 소리의 위치가 좌우 및 전후로 이동하여 공간감을 형성합니다. |
| **강수량 + 적설량** | 🔊 볼륨 조절 | 비와 눈이 많을수록 소리의 볼륨이 커지고, 사운드가 강하게 느껴집니다. |
| **자외선 지수** | 🎚 하이 셸프 EQ | 자외선 지수가 높을수록 고역대가 강조됩니다. |

---

## 💻 주요 기술 요소

### 🖼️ GUI & 이벤트 처리
- `wxPython`을 사용하여 UI 구성
- 슬라이더, 버튼 등 사용자 인터페이스 제공
- 사용자 입력에 따른 실시간 파라미터 변경

### 🎵 실시간 오디오 엔진 (`pyo`)
- 음악 루프 재생
- 필터 주파수, 볼륨, 속도 등 실시간 조절 가능
- 다양한 이펙트(`Freeverb`, `ButLP`, `Tremolo`, `HRTF` 등등) 연동

### 📊 데이터 시각화
- `matplotlib`를 `wx.Panel`에 임베드하여 날씨 변화를 시각적으로 표현
- 시간대별 온도, 습도, 강수량 그래프 출력
- 현재 재생 지점 표시 기능 포함

### 📁 데이터 처리 및 매핑
- JSON 형식의 날씨 데이터를 파싱
- 각 수치를 사운드 파라미터로 수학적 변환 (스케일링, 범위 제한 등)
- 사용자 설정에 따라 효과 적용 빠르기기 직접 조절 가능

---

## 🔧 설치 및 실행

### 1. 필수 패키지 설치

```bash
pip install wxPython pyo matplotlib
```
⚠️ wxPython은 플랫폼에 따라 설치가 어려울 수 있으니 공식 문서를 참고해주세요. 
---
### 2. 실행

bash
```
python final_with_effect_opt.py
```
or
bash
```
python final_sonification.py
```
---
🎯 주요 기능 요약
| Sound Design Element     | Implementation Detail                                 |
|--------------------------|--------------------------------------------------------|
| Low-Pass Filter          | Temperature-based cutoff frequency (ButLP)             |
| Reverb                   | Humidity-based wet/dry mix and decay (Freeverb)        |
| Tremolo                  | Wind speed-based amplitude modulation                  |
| Spatial Audio (HRTF)     | Wind direction-based stereo/spatial panning            |
| Volume Control           | Based on precipitation and snowfall                    |
| Pitch / Speed Control    | Controlled by temperature                              |
| EQ (High Shelf Boost)    | Based on UV index                                      |

---
📌 참고 사항
OpenWeatherMap API의 인증키를 받아, 실제 날씨 API 연동 또는 과거 날씨 데이터 파일을 활용하여 테스트할 수 있습니다.
---
🙋‍♀️ Contriabution
이 프로젝트에 기여하고 싶다면 Pull Request를 보내주세요! 버그 제보나 개선 아이디어도 환영합니다.