import discord
from discord.ext import commands, tasks
from config import (TOKEN, CONTROL_EMOJI, AUTHORIZED_CHANNEL, AUTHORIZED_ROLE_ID, ADMIN_ROLE_ID, GATE_CHANNEL)
from utils import check_network, wifi_monitor
from database import (get_db_connection, parse_nickname, get_user_info, save_or_update_user, 
                      fetch_matching_users, get_students_by_stdnum, update_graduation_status, 
                      delete_data, verify_student_id)
import asyncio
from datetime import datetime

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", help_command=None, intents=intents)

AUTHORIZED_TIMER = 60  # 간부진 이모지 반응 대기 시간 (초)

async def send_to_admins(guild, message):
    if guild:
        admins = [member for member in guild.members if any(role.id == ADMIN_ROLE_ID for role in member.roles)]
        for admin in admins:
            try:
                await admin.send(message)
            except discord.Forbidden:
                print(f"⚠️ {admin.display_name}님에게 DM을 보낼 수 없습니다.")

@tasks.loop(seconds=60)
async def auto_lock_task():
    if datetime.now().strftime("%H:%M") == "21:00":
        channel = bot.get_channel(AUTHORIZED_CHANNEL)
        if channel:
            await channel.send("🔒 도어락이 자동으로 잠겼습니다.")

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    auto_lock_task.start()
    bot.loop.create_task(wifi_monitor())
    for guild in bot.guilds:
        await send_to_admins(guild, "✅ 봇이 성공적으로 실행되었습니다.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)  
    
    if message.channel.id == GATE_CHANNEL and "문" in message.content:
        msg = await message.channel.send("🔔 간부진의 반응을 1분 동안 기다려주세요.")
        channel = bot.get_channel(AUTHORIZED_CHANNEL)
        if channel:
            await channel.send(f"{message.author.display_name}님이 도어락 제어를 요청했습니다.")

        def check_reaction(reaction, user):
            return reaction.message.id == msg.id and str(reaction.emoji) == CONTROL_EMOJI and any(role.id == AUTHORIZED_ROLE_ID for role in user.roles)

        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=AUTHORIZED_TIMER, check=check_reaction)
            if channel:
                await channel.send(f"🚪 {user.display_name}님이 도어락을 제어했습니다.")

        except asyncio.TimeoutError:
            timeout_message = await message.channel.send("⏳ 반응 대기 시간이 초과되었습니다. 학번을 입력하세요.")
            def check_msg(m):
                return m.channel == message.channel and m.author == message.author and m.content.isdigit()
            
            try:
                student_msg = await bot.wait_for("message", timeout=30, check=check_msg)
                student_name = verify_student_id(student_msg.content, student_msg.author.id)
                if student_name:
                    await channel.send(f"✅ 인증 성공: {student_name}님의 학번 인증을 통해 문을 열었습니다.")
                    await message.add_reaction("✅")
                else:
                    await channel.send(f"🚫 인증 실패: 학번이 일치하지 않습니다.")
                    await message.add_reaction("🚫")
            except asyncio.TimeoutError:
                await channel.send(f"⏳ 시간이 초과되었습니다. 인증 취소.")

@bot.command(name="등록")
async def save(ctx):
    for member in ctx.guild.members:
        stdnum, name, state = parse_nickname(member.nick)
        if stdnum and name:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                user = get_user_info(cursor, stdnum, name)
                if user:
                    save_or_update_user(cursor, user['id'], name, str(member.name), str(member.id), state)
                    await ctx.send(f"{name}({stdnum}) 정보 등록 완료!")
            finally:
                cursor.close()
                conn.close()
    await ctx.send("등록 완료!")

def run_bot():
    try:
        bot.run(TOKEN)
    except Exception as e:
        for guild in bot.guilds:
            asyncio.run(send_to_admins(guild, f"⚠️ 봇 오류: {e}"))