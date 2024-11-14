import discord
from discord.ext import commands
import RPi.GPIO as GPIO
import time


#TOKEN = 'MTI5OTI5ODE1MDE0NTg1MTQxMg.GhKUnJ.G46DFlFNE8nkAyTdougkJ5mNobOK0onhKRu4ZU'
# 봇 토큰 값 노출 시 -> 보안 이슈 발생 => 방법 1. 실행 할 관리자 컴퓨터의 환경변수 등록(로컬) / 방법 2. Repl.it 등의 클라우드 환경 에서의 환경변수 등록 및 사용 => 코드 수정 필요
DOOR_PIN = 17   #도어락 핀 번호 추후 재설정


GPIO.setmode(GPIO.BCM)
GPIO.setup(DOOR_PIN, GPIO.OUT)


def unlock_door():
    GPIO.output(DOOR_PIN, GPIO.HIGH)

bot = commands.Bot(command_prefix = "!")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    if message.content == "문열어주세요":
        await message.add_reaction("🔓")
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == "🔓" and reaction.message.content == "문열어주세요":
        if user.guild_permissions.administrator:
            unlock_door()

bot.run(TOKEN)