# 디스코드 사용 패키지
import discord
# discord_bot에 나눈 역할 파일들을 불러옴
from discord.ext import commands
from discord.ext import tasks
from config import TOKEN, CONTROL_EMOJI, AUTHORIZED_CHANNEL, AUTHORIZED_ROLE_ID, ADMIN_ROLE_ID, ADMIN_CHANNEL, GATE_CHANNEL, DOOR_PIN, BT_ADDR, BT_PORT
from gpio_control import setup_gpio, unlock_door, cleanup_gpio
from bluetooth_control import unlock_door_via_bluetooth
# 기타 패키지
import asyncio
import os



# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# GPIO 초기화
setup_gpio(DOOR_PIN)


# 봇 시작 이벤트 (관리자 확인)
@bot.event
async def on_ready():
    admin_channel = bot.get_channel(ADMIN_CHANNEL)
    if admin_channel:
        await admin_channel.send("✅ 봇이 성공적으로 실행되었습니다. 관리 기능이 활성화됩니다.")  # 봇 실행 알림
    print(f'{bot.user} has connected to Discord!')  # 실행 터미널 출력



# 메시지 처리 (간부진 역할)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # 봇이 보낸 메시지는 무시

    # "문열어주세요" 메시지에만 반응
    if message.channel.id == GATE_CHANNEL and message.content.strip() == "문열어주세요":
        # 요청자에게 개인 DM 전송
        await message.author.send("✅ 권한 있는 사용자에게 알림을 보냈습니다.")

        # 간부진 채널에 알림
        channel = bot.get_channel(AUTHORIZED_CHANNEL)
        if channel is not None:
            await channel.send(
                f"{message.author.display_name}님이 문을 열어달라고 요청했습니다.\n"
                f" {CONTROL_EMOJI} 이모지로 반응하여 도어락을 제어할 수 있습니다."
            )
        bot.last_requester_message = message  # 마지막 요청 메시지 저장
    else:
        # 다른 메시지나 다른 채널에서는 무시
        return

    await bot.process_commands(message)


# 이모지 반응에 따른 도어락 제어 (간부진)
@bot.event
async def on_reaction_add(reaction, user):
	# "문열어주세요" 메시지에 올바른 이모지가 추가되었는지 확인
	if (reaction.message.channel.id == GATE_CHANNEL
	and reaction.message.content.strip() == "문열어주세요"
	and reaction.emoji == CONTROL_EMOJI
	):
		guild = reaction.message.guild
		member = guild.get_member(user.id) if guild else None
		
		# 간부진 역할 검증
		if member and any(role.id == AUTHORIZED_ROLE_ID for role in member.roles):
			channel = bot.get_channel(AUTHORIZED_CHANNEL)
			admin_channel = bot.get_channel(ADMIN_CHANNEL)
			
			# 간부진 채널 알림
			if channel is not None:
				await channel.send(f"✅ {user.display_name}님이 도어락을 제어했습니다.")
			else:
				if admin_channel is not None:
					await admin_channel.send("⚠️ 간부진 채널을 찾을 수 없습니다. 설정을 확인하세요.")
				print("⚠️ 간부진 채널을 찾을 수 없습니다. 설정을 확인하세요.")
			
			# 요청 사용자 개인 DM
			if hasattr(bot, 'last_requester_message') and bot.last_requester_message:
				requester = bot.last_requester_message.author
				await requester.send(f"✅ {user.display_name}님이 도어락을 제어했습니다.")
			
			# 도어락 제어 함수 호출
			try:
				unlock_door(DOOR_PIN)
				unlock_doorvia_bluetooth(BT_ADDR, BT_PORT)						
			except Exception as e:
				# 블루투스 제어 실패 시 관리자 채널에 알림 전송
				error_message = (f"⚠️ 블루투스 제어 실패: {e}\n" 
								f"🛠️  확인이 필요합니다.")
				if channel: 
					await channel.send(error_message) # 간부진 채널에 알림
				if admin_channel:
					await admin_channel.send(error_message) # 관리자 채널에 알림)
				print(f"Error in Bluetooth control: {e}")
		
		else:
			# 권한 없는 사용자에게 개인 DM
			try:
				await user.send("🚫 도어락을 제어할 권한이 없습니다. 관리자로부터 권한을 요청하세요.")
			except discord.Forbidden:
				# 개인 DM이 차단된 경우 채널에 알림
				await reaction.message.channel.send(f"⚠️ {user.display_name}님, 도어락을 제어할 권한이 없습니다. 개인 DM 전송이 차단되어 전체 채널에 알립니다.")


# 네트워크 실행 상태 확인
def check_network():
	response = os.system("ping -c 1 google.com > /dev/null 2>&1")
	return response == 0
if not check_network():
	print("⚠️ 네트워크 연결이 끊어졌습니다.")


# 네트워크 점검 태스크
@tasks.loop(minutes = 10)
async def network_check_task():
	if not check_network():
		adminchannel = bot.get_channel(ADMIN_CHANNEL)
		if admin_channel:
			await admin_channel.send("⚠️ 네트워크 연결이 끊어졌습니다. 확인해주세요.")
		
	else:
		print("✅ 네트워크 연결 상태 정상.")


# 봇 오류 시 관리자 알림
@bot.event
async def on_error(event, *args, **kwargs):
    admin_channel = bot.get_channel(ADMIN_CHANNEL)
    if admin_channel:
        await admin_channel.send("⚠️ 이벤트 {event}에서 예외가 발생했습니다.")
    print(f"Error occurred in event: {event}: {args} {kwargs}")


# 연결 종료 시 관리자 알림
@bot.event
async def on_disconnect():
    admin_channel = bot.get_channel(ADMIN_CHANNEL)
    if admin_channel:
        asyncio.creat_task(admin_channel.send("🔌 봇 연결이 끊겼습니다. 연결을 확인해주세요."))
    cleanup_gpio()


# 봇 실행 및 종료 처리
def run_bot():
    try:
        admin_channel = None
        bot.run(TOKEN)
    except Exception as e:
        admin_channel = bot.get_channel(ADMIN_CHANNEL)
        if admin_channel:
            asyncio.run(admin_channel.send(f"⚠️ 봇이 예기치 못한 오류로 종료되었습니다: {e}"))
    finally:
        cleanup_gpio()
        if admin_channel:
            asyncio.run(admin_channel.send("🛠️ 봇이 종료되었습니다. 관리 작업 완료 후 다시 시작하세요."))

