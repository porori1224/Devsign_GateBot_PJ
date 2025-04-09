import subprocess
import time
import asyncio

# ✅ 1. Wi-Fi 네트워크 목록 (SSID, 비밀번호)
WIFI_NETWORKS = [
    {"ssid": "WiFi_1", "password": "password1"},  # 주 Wi-Fi
    {"ssid": "WiFi_2", "password": "password2"},  # 보조 Wi-Fi
]

# ✅ 2. 네트워크 연결 상태 확인
def check_network():
    try:
        # 구글 서버에 ping 보내기 (인터넷 연결 확인)
        subprocess.run(["ping", "-c", "1", "google.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "✅ 인터넷 연결이 정상입니다."
    except subprocess.CalledProcessError:
        try:
            # 로컬 네트워크 연결 확인
            subprocess.run(["ping", "-c", "1", "192.168.1.1"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "⚠️ 인터넷 연결이 끊겼지만 로컬 네트워크는 연결됨."
        except subprocess.CalledProcessError:
            return "⚠️ 네트워크 연결을 확인해주세요."

# ✅ 3. Wi-Fi 전환 함수
def switch_wifi(ssid, password):
    """
    지정된 Wi-Fi 네트워크로 변경하는 함수
    """
    try:
        print(f"🔄 {ssid}로 연결 시도 중...")

        # ✅ 라즈베리파이의 wpa_supplicant를 이용한 Wi-Fi 전환 (Linux 기반)
        wifi_config = f"""
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
        # 기존 Wi-Fi 설정을 새로운 Wi-Fi로 변경
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as file:
            file.write(wifi_config)

        # ✅ Wi-Fi 서비스 재시작
        subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"], check=True)
        time.sleep(10)  # 연결 안정화 대기

        # ✅ 다시 네트워크 상태 확인
        if check_network() == "✅ 인터넷 연결이 정상입니다.":
            print(f"✅ {ssid}에 성공적으로 연결되었습니다!")
            return True
        else:
            print(f"⚠️ {ssid} 연결 실패. 다른 네트워크 시도 중...")
            return False
    except Exception as e:
        print(f"❌ Wi-Fi 변경 중 오류 발생: {e}")
        return False

# ✅ 4. Wi-Fi 모니터링 루프 (자동 전환)
async def wifi_monitor():
    while True:
        if check_network() == "⚠️ 네트워크 연결을 확인해주세요.":
            print("[경고] 인터넷 연결이 끊어졌습니다. 다른 Wi-Fi로 전환을 시도합니다...")

            for network in WIFI_NETWORKS:
                if switch_wifi(network["ssid"], network["password"]):
                    break  # 연결 성공하면 중단

            # ✅ Wi-Fi 전환이 실패한 경우 재시도
            while check_network() == "⚠️ 네트워크 연결을 확인해주세요.":
                print("⏳ Wi-Fi 연결 재시도 중...")
                time.sleep(10)  

            print("[정보] 인터넷 연결이 복구되었습니다.")
        await asyncio.sleep(10)  # 10초마다 체크

# ✅ 5. 디스코드 봇 시작 이벤트 (Wi-Fi 모니터링 포함)
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    auto_lock_task.start()
    bot.loop.create_task(wifi_monitor())  # Wi-Fi 모니터링 실행
    for guild in bot.guilds:
        await send_to_admins(guild, "✅ 봇이 성공적으로 실행되었습니다.")
