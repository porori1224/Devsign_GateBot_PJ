import bluetooth  # 블루투스 통신을 위한 패키지

# 블루투스 연결로 도어락 제어
def unlock_door_via_bluetooth(bt_addr, bt_port):
    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((bt_addr, bt_port))
        sock.send("unlock")  # 아두이노로 unlock 명령 전송
        sock.close()
        print("블루투스 도어락 제어 명령 전송 완료")    # 실행 터미널에 출력
    
    except Exception as e:
        print(f"블루투스 제어 실패: {e}")