# 컴퓨터의 환경 변수 설정을 불러오기 위해 필요한 패키지
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# 환경 변수 및 설정 값
TOKEN  = os.getenv('DISCORD_BOT_TOKEN')
DOOR_PIN = 17

AUTHORIZED_ROLE_ID = 1304768806782107658    # 간부진 권한(역할) ID
CONTROL_EMOJI = "🔓"
CHANNEL_ID = 1299379824585871382    # 간부진 채널 ID

BT_ADDR = "00:18:E4:36:13:7A"  # 블루투스 모듈의 MAC 주소
BT_PORT = 1  # HC-05 기본 포트