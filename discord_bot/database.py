import pymysql
import re
from config import (HOST, PORT, USER, PASSWORD, DATABASE, CHARSET)

def get_db_connection():
    return pymysql.connect(
        host=HOST,              # MySQL 서버 호스트
        port=PORT,              # MySQL 포트
        user=USER,              # MySQL 사용자
        password=PASSWORD,      # MySQL 비밀번호
        database=DATABASE,      # 사용할 데이터베이스
        charset=CHARSET,        # 문자셋
        autocommit=True         # 자동 커밋 설정
    )

# 닉네임에서 학번, 이름, 상태(재학/휴학) 추출
def parse_nickname(nickname: str | None) -> tuple[str | None, str | None, str | None]:
    # 닉네임이 None이면 바로 종료
    if nickname is None or nickname.strip() == "":
        return None, None, None

    # DEVSIGN 자체인 경우 무시
    if nickname == "DEVSIGN":
        return None, None, None

    # 첫 번째 공백을 기준으로 학번과 이름 분리
    parts = nickname.split(" ", 1)
    if len(parts) < 2:
        return None, None, None  # 닉네임이 형식에 맞지 않으면 처리 X
    
    stdnum_raw, name = parts
    state = "재학"  # 기본 상태는 재학

    # 이름에서 "(회장)", "(부회장)", "(총무)" 등 제거
    name = re.sub(r"\(.*?\)", "", name).strip()

    # 닉네임이 v로 시작하면 휴학 상태로 설정
    if stdnum_raw.startswith("v"):
        state = "휴학"
        stdnum = stdnum_raw[1:]  # "v" 제거
    else:
        stdnum = stdnum_raw  # 학번 유지

    return stdnum, name, state

# DB에서 학번과 이름이 일치하는 사용자 검색
def get_user_info(cursor, stdnum: str, name: str):
    query = "SELECT id FROM devsign_member WHERE stdnum REGEXP %s AND name = %s AND withdrawal = 0 AND userid IS NULL"
    cursor.execute(query, ("^.."+stdnum +"....$", name))
    return cursor.fetchone()  # 결과가 없으면 None 반환

# 태그, 사용자 ID, 상태 업데이트
def update_user_info(cursor, id: str, name: str, username: str, userid: str, state: str):
    query = """
        UPDATE devsign_member 
        SET username = %s, userid = %s, state = %s
        WHERE id = %s AND name = %s
    """
    cursor.execute(query, (username, userid, state, id, name))
