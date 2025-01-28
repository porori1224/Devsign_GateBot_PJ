from bot import bot
from config import TOKEN
from gpio_control import cleanup_gpio 


# 봇 실행 및 종료 처리
def run_bot():
    try:
        admin_channel = None
        bot.run(TOKEN)
    except Exception as e:
        print(f"봇 실행 중 오류 발생: {e}")
    finally:
        cleanup_gpio()


if __name__ == "__main__" :
    run_bot()
