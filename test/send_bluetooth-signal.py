#라즈베리파이에서 블루투스 신호를 전송하여 아두이노를 통해 도어락을 제어할 테스트 코드 

import bluetooth

# HC-05 모듈의 MAC 주소 입력
bd_addr = "XX:XX:XX:XX:XX:XX"  # HC-05 MAC 주소
port = 1  # HC-05 기본 포트

def unlock_door():
    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((bd_addr, port))
        print("블루투스 연결 성공")

        # 도어락 열림 명령 전송
        sock.send("unlock")
        print("도어락 열림 명령 전송 완료")
        sock.close()
    except bluetooth.btcommon.BluetoothError as err:
        print(f"연결 실패: {err}")

unlock_door()