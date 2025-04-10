import subprocess
import time
import asyncio

# 네트워크 실행 상태 확인
def check_network():
    try:
        # 구글 서버에 ping 보내기
        subprocess.run(["ping", "-c", "1", "google.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "✅ 인터넷 연결이 정상입니다."
    except subprocess.CalledProcessError:
        try:
            # 로컬 라우터에 ping 보내기
            subprocess.run(["ping", "-c", "1", "192.168.1.78"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "⚠️ 인터넷 연결이 끊겼지만 로컬 네트워크는 연결됨."
        except subprocess.CalledProcessError:
            return "⚠️ 네트워크 연결을 확인해주세요."

# Wi-Fi 모니터링 루프 (끊겼을 때 복구될 때까지 대기)
async def wifi_monitor():
    while True:
        if check_network() == "⚠️ 네트워크 연결을 확인해주세요.":
            print("[경고] 인터넷 연결이 끊어졌습니다. 다시 연결을 시도합니다...")
            while check_network() == "⚠️ 네트워크 연결을 확인해주세요.":
                time.sleep(3)  # 3초마다 재시도
            print("[정보] 인터넷 연결이 복구되었습니다.")
        await asyncio.sleep(10)  # 10초마다 체크
