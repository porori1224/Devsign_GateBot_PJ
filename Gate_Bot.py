import discord
from discord.ext import commands
import RPi.GPIO as GPIO
from bluetooth import BluetoothSocket, RFCOMM

#TOKEN  = 'MTI5OTI5ODE1MDE0NTg1MTQxMg.GhKUnJ.G46DFlFNE8nkAyTdougkJ5mNobOK0onhKRu4ZU'
DOOR_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(DOOR_PIN, GPIO.OUT)

def unlock_door():
    GPIO.output(DOOR_PIN, GPIO.HIGH)

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents = intents)

#AUTHORIZED_ROLE_ID = 1304768806782107658
#CONTROL_EMOJI = ""
#CHANNEL_ID = 1299379824585871382


def unlock_door():
   try:
      #sock = BluetoothSocket(RFCOMM)
      #sock.connect((DOORLCK_BLUETOOTH_ADDRESS, 1))
      
      #sock.send("unlock")
      GPIO.output(DOOR_PIN, GPIO.HIGH)
      print("도어락 열기 명령 전송 완료")
      
      #sock.close()
   except Exception as e:
      print(f"도어락 제어 실패: {e}")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
   if message.author == bot.user:
      return  # 봇이 보낸 메시지는 무시

   if "문열어주세요" in message.content:
      await message.author.send("권한 있는 사용자에게 알림을 보냈습니다.")
      
        # 지정 채널에 있는 사용자에게 알림 전송(간부진)
      channel = bot.get_channel(CHANNEL_ID)
      if channel is not None:
         await channel.send(f"{message.author.display_name}님이 문을 열어달라고 요청했습니다. "
                               f"{CONTROL_EMOJI} 이모지로 반응하여 도어락을 제어할 수 있습니다.")
         bot.last_requester_message = message
                                  
   await bot.process_commands(message)
    
@bot.event
async def on_reaction_add(reaction, user):
   # "문열어주세요" 메시지에 반응한 경우
   if reaction.message.content == "문열어주세요" and reaction.emoji == CONTROL_EMOJI:
      
      # 반응을 추가한 사용자가 속한 서버에서 해당 사용자 찾기
      guild = reaction.message.guild
      member = guild.get_member(user.id) if guild else None
        
      if member and any(role.id == AUTHORIZED_ROLE_ID for role in member.roles):
         channel = bot.get_channel(CHANNEL_ID)
         
         if channel is not None:
            await channel.send(f"{user.display_name}님이 도어락을 제어했습니다.")
         else:
            print("간부진 채널을 찾을 수 없습니다. 간부진 채널 아이디를 확인해주세요.")
         
         # 요청 사용자에게도 개인 DM 발송
         if hasattr(bot, 'last_requester_message') and bot.last_requester_message:
            requester = bot.last_requester_message.author
            await requester.send(f"{user.display_name}님이 도어락을 제어했습니다.")
      
         unlock_door()
      else:
         await reaction.message.channel.send("도어락을 제어할 권한이 없습니다.")

@bot.event
async def on_disconnect():
   GPIO.cleanup

bot.run(TOKEN)