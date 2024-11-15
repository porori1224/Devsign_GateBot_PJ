import discord
import time
from discord.ext import commands
import RPi.GPIO as GPIO
import bluetooth  # 블루투스 통신을 위한 모듈
import asyncio



TOKEN  = 'MTI5OTI5ODE1MDE0NTg1MTQxMg.GhKUnJ.G46DFlFNE8nkAyTdougkJ5mNobOK0onhKRu4ZU'
DOOR_PIN = 17

AUTHORIZED_ROLE_ID = 1304768806782107658    # 간부진 권한(역할) ID
CONTROL_EMOJI = "🔓"
CHANNEL_ID = 1299379824585871382    # 간부진 채널 ID

BT_ADDR = "XX:XX:XX:XX:XX:XX"  # 블루투스 모듈의 MAC 주소
BT_PORT = 1  # HC-05 기본 포트

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(DOOR_PIN, GPIO.OUT)

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents = intents)



# 도어락 열기 함수 (GPIO 및 블루투스)
def unlock_door():
    try:
        # GPIO로 도어락 제어
        GPIO.output(DOOR_PIN, GPIO.LOW)   # 전류 ON
        time.sleep(3) #3초 동안 전류 흐름
        GPIO.output(DOOR_PIN, GPIO.HIGH)  # 전류 OFF
        print("도어락 열기 명령 전송 완료")   # 실행 터미널에 출력
      
        # 블루투스 연결로 도어락 제어
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((BT_ADDR, BT_PORT))
        sock.send("unlock")  # 아두이노로 unlock 명령 전송
        sock.close()
        print("블루투스 도어락 제어 명령 전송 완료")    # 실행 터미널에 출력
    
    except Exception as e:
      print(f"도어락 제어 실패: {e}")   # 제어 실패 시 오류 메시지가 터미널에 출력



# 봇 시작 이벤트
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')  # 실행 터미널에 출력, 봇이 활성화에 성공



# 메시지 처리
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # 봇이 보낸 메시지는 무시

    if "문열어주세요" in message.content:
      await message.author.send("권한 있는 사용자에게 알림을 보냈습니다.")  # 요청자 개인 DM으로 발송
      
    
    # 지정 채널에 있는 사용자에게 알림 전송(간부진)
    channel = bot.get_channel(CHANNEL_ID)
        
    if channel is not None:
        await channel.send(f"{message.author.display_name}님이 문을 열어달라고 요청했습니다. "
                            f"{CONTROL_EMOJI} 이모지로 반응하여 도어락을 제어할 수 있습니다.")  # 간부진 채널에 DM 발송됨
        bot.last_requester_message = message
                                  
    await bot.process_commands(message)



# 이모지 반응에 따른 도어락 제어
@bot.event
async def on_reaction_add(reaction, user):
   # "문열어주세요" 메시지에 반응한 경우
   if reaction.message.content == "문열어주세요" and reaction.emoji == CONTROL_EMOJI:
      
      
      # 반응을 추가한 사용자가 속한 서버에서 해당 사용자 찾기 -> 간부진 서버에서 이모지 반응을 누른 사용자를 탐색
      guild = reaction.message.guild
      member = guild.get_member(user.id) if guild else None


      # 간부진 역할 검증 -> 간부진 역할 부여자만 도어락 제어 권한이 있음  
      if member and any(role.id == AUTHORIZED_ROLE_ID for role in member.roles):
         channel = bot.get_channel(CHANNEL_ID)

         # 간부진 역할과 간부진 채널에 모두 적합한 사용자가 요청에 이모지를 남겼을 때
         if channel is not None:
            await channel.send(f"{user.display_name}님이 도어락을 제어했습니다.")   # 간부진 채널에 이모지가 남겨졌음을 알림
         else:
            print("간부진 채널을 찾을 수 없습니다. 간부진 채널 아이디를 확인해주세요.") # 간부진 채널 탐색 오류 -> 터미널 출력
         
         # 요청 사용자에게도 개인 DM 발송
         if hasattr(bot, 'last_requester_message') and bot.last_requester_message:  # 문열어주세요 서버의 마지막 메시지(요청)을 기억
            requester = bot.last_requester_message.author   # 마지막 메시지(요청) 발송자를 봇이 인식
            await requester.send(f"{user.display_name}님이 도어락을 제어했습니다.") # 인식된 마지막 요청자에게 도어락이 제어되었음을 개인 DM으로 발송
      
         unlock_door()
      else:
         await reaction.message.channel.send("도어락을 제어할 권한이 없습니다.")    # 간부진 역할자가 아닌 사람이 이모지를 남겼을 때 문열어주세요 채널에 알림



# 봇 오류 시 알림 전송
@bot.event
async def on_error(event, *args, **kwargs):
    # 예외 발생 시 지정(간부진) 채널에 알림 전송
    channel = bot.get_channel(CHANNEL_ID)
    if channel is not None:
        await channel.send("⚠️ 시스템 오류가 발생하여 봇이 작동을 멈췄습니다. 확인이 필요합니다.")



# 연결 종료 시 GPIO 정리
@bot.event
async def on_disconnect():
   GPIO.cleanup

bot.run(TOKEN)

# 봇 실행
#try:
#    bot.run(TOKEN)
#except Exception as e:
    # 예기치 못한 종료 시 간부진 채널에 알림 전송
#    channel = bot.get_channel(CHANNEL_ID)
#    if channel is not None:
#        asyncio.run(channel.send(f"⚠️ 봇이 예기치 못한 오류로 종료되었습니다: {e}"))
#finally:
#    GPIO.cleanup()
