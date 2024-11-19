# 라즈베리파이의 GPIO 전류 제어를 위한 필요 패키지
import RPi.GPIO as GPIO
import time

# GPIO 설정
def setup_gpio(door_pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(door_pin, GPIO.OUT)


# 도어락 열기 함수 (GPIO 및 블루투스)
def unlock_door(door_pin):
    try:
        # GPIO로 도어락 제어
        GPIO.output(door_pin, GPIO.LOW)   # 전류 ON
        time.sleep(1) # 1초 동안 전류 흐름
        GPIO.output(door_pin, GPIO.HIGH)  # 전류 OFF
        print("도어락 열기 명령 전송 완료")   # 실행 터미널에 출력
    
    except Exception as e:
      print(f"도어락 제어 실패: {e}")   # 제어 실패 시 오류 메시지가 터미널에 출력


def cleanup_gpio():
    GPIO.cleanup()