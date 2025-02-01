import discord
from discord.ext import commands, tasks
from config import (TOKEN, CONTROL_EMOJI, AUTHORIZED_CHANNEL, AUTHORIZED_ROLE_ID, ADMIN_ROLE_ID, GATE_CHANNEL, DOOR_PIN, BT_ADDR, BT_PORT)
from gpio_control import setup_gpio, cleanup_gpio
from bluetooth_control import unlock_door_via_bluetooth, lock_door_via_bluetooth
from utils import check_network
import asyncio
from datetime import datetime

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# GPIO 초기화
setup_gpio(DOOR_PIN)

# 관리자 역할을 가진 사용자들에게 DM 보내기 함수
async def send_to_admins(guild, message):
    """관리자 역할을 가진 모든 사용자에게 개인 DM 전송"""
    if guild:
        admins = [member for member in guild.members if any(role.id == ADMIN_ROLE_ID for role in member.roles)]
        for admin in admins:
            try:
                await admin.send(message)
            except discord.Forbidden:
                print(f"⚠️ {admin.display_name}님에게 DM을 보낼 수 없습니다.")

# 도어락 자동 잠금 태스크
@tasks.loop(minutes=1)  # 태스크를 1분마다 실행
async def auto_lock_task():
	current_time = datetime.now().strftime("%H:%M")  # 현재 시간을 HH:MM 형식으로 가져옴
	lock_time = "21:00"  # 도어락 잠금 시간
	if current_time == lock_time:
		success = lock_door_via_bluetooth(BT_ADDR, BT_PORT)  # 블루투스로 도어락 잠금
		channel = bot.get_channel(AUTHORIZED_CHANNEL)
		message = "🔒 도어락이 자동으로 잠겼습니다." if success else "⚠️ 도어락이 자동으로 잠기지 못했습니다. 확인해주세요."
		if channel:	#관리 채널로 알림 발송
			await channel.send(message)
			

# 봇 시작 이벤트 (관리자 확인)
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")  # 실행 터미널 출력
    auto_lock_task.start()  # 자동 잠금 태스크 시작
    for guild in bot.guilds:
        await send_to_admins(guild, "✅ 봇이 성공적으로 실행되었습니다. 관리 기능이 활성화됩니다.")

# 메시지 처리 (간부진 역할)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # 봇이 보낸 메시지는 무시

    # "문열어주세요" 메시지에만 반응
    if message.channel.id == GATE_CHANNEL and message.content.strip() == "문열어주세요":
        channel = bot.get_channel(AUTHORIZED_CHANNEL)
        if channel:
            await channel.send(f"{message.author.display_name}님이 도어락 제어를 요청했습니다.")
        bot.last_requester_message = message  # 마지막 요청 메시지 저장

    await bot.process_commands(message)

# 이모지 반응에 따른 도어락 제어 (간부진)
@bot.event
async def on_reaction_add(reaction, user):
    if (reaction.message.channel.id == GATE_CHANNEL
        and reaction.message.content.strip() == "문열어주세요"
        and reaction.emoji == CONTROL_EMOJI):
        
        guild = reaction.message.guild
        member = guild.get_member(user.id) if guild else None

        if member and any(role.id == AUTHORIZED_ROLE_ID for role in member.roles):
            success = unlock_door_via_bluetooth(BT_ADDR, BT_PORT)
            
            channel = bot.get_channel(AUTHORIZED_CHANNEL)
            if channel:
                await channel.send(f"✅ {user.display_name}님이 도어락을 제어했습니다.")

            if not success:
                error_message = "⚠️ 블루투스 제어 실패. 확인이 필요합니다."
                await send_to_admins(guild, error_message)
                if channel:
                    await channel.send(error_message)
        else:
            try:
                await user.send("🚫 도어락을 제어할 권한이 없습니다. 관리자로부터 권한을 요청하세요.")
            except discord.Forbidden:
                await reaction.message.channel.send(
                    f"⚠️ {user.display_name}님, 도어락을 제어할 권한이 없습니다. 개인 DM 전송이 차단되었습니다."
                )

# 네트워크 점검 태스크
@tasks.loop(minutes=10)
async def network_check_task():
    for guild in bot.guilds:
        if not check_network():
            await send_to_admins(guild, "⚠️ 네트워크 연결이 끊어졌습니다. 확인해주세요.")

# 봇 실행 및 종료 처리
def run_bot():
    try:
        bot.run(TOKEN)
    except Exception as e:
        for guild in bot.guilds:
            asyncio.run(send_to_admins(guild, f"⚠️ 봇이 예기치 못한 오류로 종료되었습니다: {e}"))
    finally:
        cleanup_gpio()
        for guild in bot.guilds:
            asyncio.run(send_to_admins(guild, "🛠️ 봇이 종료되었습니다. 관리 작업 완료 후 다시 시작하세요."))

