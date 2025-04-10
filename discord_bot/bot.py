import discord
from discord.ext import commands, tasks
from config import (
    TOKEN,
    CONTROL_EMOJI,
    AUTHORIZED_CHANNEL,
    AUTHORIZED_ROLE_ID,
    ADMIN_ROLE_ID,
    GATE_CHANNEL,
    DOOR_PIN,
    BT_ADDR,
    BT_PORT)
from gpio_control import setup_gpio, cleanup_gpio
from bluetooth_control import unlock_door_via_bluetooth, lock_door_via_bluetooth
from utils import check_network, wifi_monitor
import asyncio
from datetime import datetime
from database import *

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

AUTHORIZED_TIMER = 60  # 간부진 이모지 반응 대기 시간 (초)

# GPIO 초기화
setup_gpio(DOOR_PIN)

# 관리자 역할을 가진 사용자들에게 DM 보내기 함수


async def send_to_admins(guild, message):
    """관리자 역할을 가진 모든 사용자에게 개인 DM 전송"""
    if guild:
        admins = [member for member in guild.members if any(
            role.id == ADMIN_ROLE_ID for role in member.roles)]
        for admin in admins:
            try:
                await admin.send(message)
            except discord.Forbidden:
                print(f"⚠️ {admin.display_name}님에게 DM을 보낼 수 없습니다.")

# 도어락 자동 잠금 태스크


@tasks.loop(seconds=60)  # 태스크를 60초마다 실행
async def auto_lock_task():
    current_time = datetime.now().strftime("%H:%M")  # 현재 시간을 HH:MM 형식으로 가져옴
    lock_time = "21:00"  # 도어락 잠금 시간
    if current_time == lock_time:
        success = lock_door_via_bluetooth(BT_ADDR, BT_PORT)  # 블루투스로 도어락 잠금
        channel = bot.get_channel(AUTHORIZED_CHANNEL)
        message = "🔒 도어락이 자동으로 잠겼습니다." if success else "⚠️ 도어락이 자동으로 잠기지 못했습니다. 확인해주세요."
        if channel:  # 관리 채널로 알림 발송
            await channel.send(message)
            

@auto_lock_task.before_loop
async def before_auto_lock():
    await bot.wait_until_ready()  # 봇이 준비될 때까지 대기


# 봇 시작 이벤트 (관리자 확인)
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")  # 실행 터미널 출력
    auto_lock_task.start()  # 자동 잠금 태스크 시작
    #bot.loop.create_task(wifi_monitor())  # Wi-Fi 모니터링 실행
    for guild in bot.guilds:
        await send_to_admins(guild, "✅ 봇이 성공적으로 실행되었습니다. 관리 기능이 활성화됩니다.")


@bot.event
async def on_message(message):
    if message.author.bot:
        return  # 봇이 보낸 메시지는 무시

    await bot.process_commands(message)  # 명령어 처리 추가

    if message.channel.id == GATE_CHANNEL and "문" in message.content.strip():
        msg = await message.channel.send("🔔 간부진의 반응을 1분 동안 기다려주세요.")

        # 간부진 채널에 도어락 제어 요청 알림
        channel = bot.get_channel(AUTHORIZED_CHANNEL)
        if channel:
            await channel.send(f"{message.author.display_name}님이 도어락 제어를 요청했습니다.")

        def check_reaction(reaction, user):
            return (
                reaction.message.id == msg.id  # ✅ 특정 메시지(msg)에 대한 반응인지 확인
                # ✅ 반응이 특정 이모지(CONTROL_EMOJI)인지 확인
                and str(reaction.emoji) == CONTROL_EMOJI
                # ✅ 반응을 단 사용자가 특정 역할을 가지고 있는지 확인
                and any(role.id == AUTHORIZED_ROLE_ID for role in user.roles)
            )

        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=AUTHORIZED_TIMER, check=check_reaction)
            channel = bot.get_channel(AUTHORIZED_CHANNEL)  # 간부진 채널 가져오기
            if channel:
                # 도어락 개방 명령어 입력란
                await channel.send(f"🚪 {user.display_name}님이 도어락을 제어했습니다.")

                success = unlock_door_via_bluetooth(BT_ADDR, BT_PORT)
                if not success:
                    error_message = "⚠️ 블루투스 제어 실패. 확인이 필요합니다."
                    await send_to_admins(message.guild, error_message)
                    if channel:
                        await channel.send(error_message)

        except asyncio.TimeoutError:
            timeout_message = await message.channel.send("⏳ 반응 대기 시간이 초과되었습니다. 학번을 입력하여 제어할 수 있습니다.")

            def check_msg(m):
                return m.channel == message.channel and m.author == message.author and m.content.isdigit()

            try:
                student_msg = await bot.wait_for("message", timeout=30, check=check_msg)
                student_stdnum = student_msg.content
                student_id = student_msg.author.id  # 메시지 보낸 사람의 사용자 ID
                student_name = verify_student_id(
                    student_stdnum, student_id)  # 사용자 ID도 함께 전달

                channel = bot.get_channel(AUTHORIZED_CHANNEL)

                if student_name:
                    await student_msg.delete()  # 인증 성공 시 사용자 메시지 삭제
                    await msg.delete()  # 봇이 보낸 메시지도 삭제
                    await timeout_message.delete()  # 시간 초과 메시지 삭제
                    # 도어락 개방 명령어 입력란
                    await channel.send(f"✅ 인증 성공: {student_name}님의 학번 인증을 통해 문을 열었습니다.")
                    # await message.channel.send(f"✅ 인증 성공: {student_name}님, 문을
                    # 열었습니다.")

                    success = unlock_door_via_bluetooth(BT_ADDR, BT_PORT)
                    if not success:
                        error_message = "⚠️ 블루투스 제어 실패. 확인이 필요합니다."
                        await send_to_admins(message.guild, error_message)
                        if channel:
                            await channel.send(error_message)

                    # "문열어주세요" 메시지에 이모지 추가
                    await message.add_reaction("✅")  # 인증 성공 시 봇이 직접 이모지 반응 남김

                    # unlock_door_via_bluetooth(BT_ADDR, BT_PORT)
                else:
                    await student_msg.delete()  # 인증 성공 시 사용자 메시지 삭제
                    await msg.delete()  # 봇이 보낸 메시지도 삭제
                    await timeout_message.delete()  # 시간 초과 메시지 삭제
                    await channel.send(f"🚫 인증 실패: 학번으로 도어락 제어에 실패했습니다.({student_id})")
                    # await message.channel.send(f"🚫 인증 실패: 학번이 일치하지 않습니다.")

                    # "문열어주세요" 메시지에 이모지 추가
                    await message.add_reaction("🚫")  # 봇이 메시지에 직접 이모지 반응을 남김

            except asyncio.TimeoutError:
                await msg.delete()  # 봇이 보낸 메시지도 삭제
                await timeout_message.delete()  # 시간 초과 메시지 삭제
                await channel.send(f"⏳ 시간이 초과되었습니다. 인증 취소.")
                await message.channel.send(f"⏳ 시간이 초과되었습니다. 인증 취소.")

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
            asyncio.run(
                send_to_admins(
                    guild,
                    f"⚠️ 봇이 예기치 못한 오류로 종료되었습니다: {e}"))
    finally:
        cleanup_gpio()
        for guild in bot.guilds:
            asyncio.run(
                send_to_admins(
                    guild,
                    "🛠️ 봇이 종료되었습니다. 관리 작업 완료 후 다시 시작하세요."))

# 웹에서 등록 후 데이터(사용자ID 등) 일괄 업데이트


@bot.command(name="등록")
async def save(ctx):
    print("✅ !등록 명령어가 실행됨")  # 디버깅 로그 추가

    # 사용자가 관리자 역할 또는 간부진 역할을 가지고 있는지 확인
    if not any(role.id == ADMIN_ROLE_ID or role.id ==
               AUTHORIZED_ROLE_ID for role in ctx.author.roles):
        await ctx.send("이 명령어는 관리자와 간부진만 사용할 수 있습니다.")
        return

    # 서버에서 사용자 닉네임 가져오기
    for member in ctx.guild.members:
        # 닉네임 파싱
        stdnum, name, state = parse_nickname(member.nick)
        if stdnum and name:
            # DB 연결
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # DB에서 해당 유저 찾기
                user = get_user_info(cursor, stdnum, name)
                if user:
                    save_user_info(
                        cursor, user['id'], name, str(
                            member.name), str(
                            member.id), state)  # ✅ user['id'] 사용
                    await ctx.send(f"{name}({stdnum}) 정보 등록 완료!")
            finally:
                cursor.close()
                conn.close()

#


@bot.command(name="업데이트")
async def update(ctx):

    # 사용자가 관리자 역할 또는 간부진 역할을 가지고 있는지 확인
    if not any(role.id == ADMIN_ROLE_ID or role.id ==
               AUTHORIZED_ROLE_ID for role in ctx.author.roles):
        await ctx.send("이 명령어는 관리자와 간부진만 사용할 수 있습니다.")
        return

    # 서버에서 사용자 닉네임 가져오기
    for member in ctx.guild.members:
        # 닉네임 파싱
        stdnum, name, state = parse_nickname(member.nick)
        if stdnum and name:
            # DB 연결
            conn = get_db_connection()  # database.py에서 가져온 함수로 연결
            cursor = conn.cursor(pymysql.cursors.DictCursor)  # ✅ DictCursor 사용

            try:
                # DB에서 해당 유저 찾기
                users = fetch_matching_users(cursor, stdnum, name)

                if not users:
                    await ctx.send(f"{name}({stdnum}) 사용자를 찾을 수 없습니다.")
                    continue

                if len(users) == 1:
                    # 검색된 데이터가 하나면 바로 업데이트
                    user = users[0]  # ✅ 수정: 리스트에서 데이터 꺼내기
                    update_user_info(
                        cursor, user['id'], name, str(
                            member.name), str(
                            member.id), state)
                    conn.commit()
                    await ctx.send(f"{name}({stdnum}) 정보 업데이트 완료!")
                else:
                    # 검색된 데이터가 여러 개라면 목록을 보여주고 선택 요청
                    message = f"{name}({stdnum}) 검색 결과 여러 개의 사용자가 있습니다. 업데이트할 ID를 입력하세요:\n"
                    for user in users:
                        message += f"- ID: {user['id']}, 학번: {user['stdnum']}, 이름: {user['name']}, 상태: {user['state']}\n"

                    await ctx.send(message)

                    def check(msg):
                        return msg.author == ctx.author and msg.content.isdigit()

                    while True:  # 반복문으로 잘못된 ID 입력을 처리
                        try:
                            msg = await bot.wait_for("message", check=check, timeout=60)
                            selected_id = msg.content.strip()

                            if not any(str(user['id']) ==
                                       selected_id for user in users):
                                await ctx.send("잘못된 ID를 입력하셨습니다. 다시 시도해주세요.")
                                continue  # 잘못된 ID 입력 시 다시 입력 받기

                            # 해당 ID로 업데이트 실행
                            update_user_info(
                                cursor, selected_id, name, str(
                                    member.name), str(
                                    member.id), state)
                            conn.commit()
                            await ctx.send(f"사용자 ID : {selected_id} / {name}({stdnum})[{user['stdnum']}] 정보가 업데이트되었습니다.")
                            break  # 올바른 ID가 입력되면 반복 종료

                        except asyncio.TimeoutError:
                            await ctx.send("시간 초과로 요청이 취소되었습니다.")
                            break  # 시간이 초과되면 반복 종료

            finally:
                cursor.close()
                conn.close()


@bot.command(name="졸업")
async def graduate(ctx, stdnum: str):
    # 학번으로 해당 사용자들을 조회
    students = get_students_by_stdnum(stdnum)

    if not students:
        await ctx.send(f"{stdnum}학번에 해당하는 사용자가 없습니다.")
        return

    # 해당 학번을 가진 사용자 목록 출력
    await ctx.send(f"학번 {stdnum}에 해당하는 사용자들:\n")
    for student in students:
        await ctx.send(f"ID: {student['id']}, 이름: {student['name']}, 상태: {student['state']}")

    while True:  # 졸업 처리할 사용자 ID를 계속 입력 받음
        # 사용자가 졸업 처리할 사용자 ID 입력받기
        await ctx.send("졸업 처리할 사용자 ID를 입력하세요. '종료'를 입력하면 종료됩니다.")

        def check(message):
            return message.author == ctx.author

        try:
            # 30초 대기
            user_id_message = await bot.wait_for('message', check=check, timeout=30.0)
            user_id = user_id_message.content

            if user_id.lower() == '종료':  # '아니오'가 입력되면 종료
                await ctx.send("졸업 처리 종료.")
                break

            # 졸업 처리 함수 호출
            update_graduation_status(user_id)
            await ctx.send(f"사용자 {user_id}의 상태를 졸업으로 변경하고 탈퇴 처리 완료.")

        except asyncio.TimeoutError:
            await ctx.send("시간 초과로 사용자 ID를 입력하지 못했습니다.")
            break  # 시간 초과시 종료
