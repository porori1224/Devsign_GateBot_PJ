# 컴퓨터의 환경 변수 설정을 불러오기 위해 필요한 패키지
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# 환경 변수 및 설정 값
TOKEN  = os.getenv('DISCORD_BOT_TOKEN')
DOOR_PIN = 17

# 역할 및 이모지 설정 값 - 간부진
CONTROL_EMOJI = "🔓"    # 반응 될 이모지
AUTHORIZED_ROLE_ID = 462157893584814092  # 간부진 권한(역할) ID -> 변경 필요
AUTHORIZED_CHANNEL = 1300037630385197107  # 간부진 채널 ID -> 변경 필요

#AUTHORIZED_ROLE_ID = 1304768806782107658  # 간부진 권한(역할) ID -> 테스트 서버
#AUTHORIZED_CHANNEL = 1308471298552238151  # 간부진 채널 ID -> 테스트 서버

# 역할 및 이모지 설정 값 - 관리자
ADMIN_ROLE_ID = 1308312719090389073     # 관리자 권한(역할) ID -> 테스트 서버(추후 변경 예정 건들 ㄴㄴ)
#ADMIN_ROLE_ID = 1306869420416696385     # 관리자 권한(역할) ID -> 테스트 서버
ADMIN_CHANNEL = 1308636329340305428     # 관리자 채널 ID -> 바꾸기(2024-문지기) => 안 바꿔도 될 듯
#ADMIN_CHANNEL = 1306869420416696385     # 관리자 채널 ID -> 테스트 서버

# 문열어주세요 채널
#GATE_CHANNEL = 1308471633018622113 -> 테스트 서버
GATE_CHANNEL = 481620560531423242 # -> 변경 필요

# 블루투스 설정 값
BT_ADDR = "00:18:E4:36:13:7A"  # 블루투스 모듈의 MAC 주소
BT_PORT = 1  # HC-05 기본 포트

