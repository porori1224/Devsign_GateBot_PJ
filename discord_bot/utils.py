import os

# 네트워크 실행 상태 확인
def check_network():
	response_google = os.system("pring -c 1 google.com > /dev/null 2>&1") 
	response_router = os.system("ping -c 1 192.168.1.78 > /dev/null 2>&1")
	if response_router == 0: return "✅ 로컬 네트워크 연결이 정상입니다."
	elif response_google == 0 : return "✅ 인터넷 연결이 정상입니다."
	else: return "⚠️ 네트워크 연결을 확인해주세요."
