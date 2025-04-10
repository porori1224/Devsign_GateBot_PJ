import bluetooth  # 블루투스 통신을 위한 패키지

# 블루투스 연결로 도어락 제어
def unlock_door_via_bluetooth(bt_addr, bt_port, retries=10, delay=0.5):
    for attempt in range(1, retries + 1):
        try:
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((bt_addr, bt_port))
            sock.send("unlock")  # 아두이노로 unlock 명령 전송
            sock.close()
            print(f"블루투스 도어락 제어 명령 전송 완료 (시도 {attempt}/{retries})")
            return True  # 성공적으로 실행되면 종료
        except Exception as e:
            print(f"블루투스 제어 실패 (시도 {attempt}/{retries}): {e}")
    return False  # 모든 시도가 실패하면 False 반환

# 블루투스 연결로 도어락 잠금
def lock_door_via_bluetooth(bt_addr, bt_port, retries=10, delay=0.5):
    for attempt in range(1, retries + 1):
        try:
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((bt_addr, bt_port))
            sock.send("lock")  # 아두이노로 lock 명령 전송
            sock.close()
            print(f"블루투스 도어락 잠금 명령 전송 완료 (시도 {attempt}/{retries})")
            return True  # 성공적으로 실행되면 종료
        except Exception as e:
            print(f"블루투스 잠금 실패 (시도 {attempt}/{retries}): {e}")
    return False  # 모든 시도가 실패하면 False 반환
