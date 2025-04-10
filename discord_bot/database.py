import pymysql
import pymysql.cursors  # 추가된 임포트
import re
import asyncio
from config import (HOST, PORT, USER, PASSWORD, DATABASE, CHARSET)

def get_db_connection():
    return pymysql.connect(
        host=HOST,              # MySQL 서버 호스트
        port=PORT,              # MySQL 포트
        user=USER,              # MySQL 사용자
        password=PASSWORD,      # MySQL 비밀번호
        database=DATABASE,      # 사용할 데이터베이스
        charset=CHARSET,        # 문자셋
        autocommit=True,         # 자동 커밋 설정
        cursorclass=pymysql.cursors.DictCursor  # DictCursor 사용
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
def save_user_info(cursor, id: str, name: str, username: str, userid: str, state: str):
    query = """
        UPDATE devsign_member 
        SET username = %s, userid = %s, state = %s
        WHERE id = %s AND name = %s
    """
    cursor.execute(query, (username, userid, state, id, name))

# DB에서 학번과 이름이 일치하는 사용자 검색
def fetch_matching_users(cursor, stdnum: str, name: str):
    query = "SELECT * FROM devsign_member WHERE stdnum REGEXP %s AND name = %s AND withdrawal = 0"
    cursor.execute(query, ("^.."+stdnum +"....$", name))
    return cursor.fetchall()  # 결과가 없으면 None 반환

# 태그, 사용자 ID, 상태 업데이트
def update_user_info(cursor, id: str, name: str, username: str, userid: str, state: str):
    query = """
        UPDATE devsign_member 
        SET username = %s, userid = %s, state = %s
        WHERE id = %s AND name = %s
    """
    cursor.execute(query, (username, userid, state, id, name))

# 학번으로 조회
async def get_students_by_stdnum(stdnum: str):
    connection = await get_db_connection()  # DB 연결
    try:
        with connection.cursor() as cursor:
            # 학번을 기준으로 사용자 정보 조회
            sql = "SELECT * FROM devsign_member WHERE stdnum REGEXP %s"
            cursor.execute(sql, ("^.."+stdnum +"....$",))
            result = cursor.fetchall()  # 조회된 모든 사용자 정보
            return result
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()

# 졸업 처리 함수
async def update_graduation_status(id: str):
    connection = await get_db_connection()  # DB 연결
    try:
        with connection.cursor() as cursor:
            # 사용자 ID에 대해 졸업 처리
            sql = """
                UPDATE devsign_member
                SET state = '졸업', withdrawal = 1
                WHERE id = %s
            """
            cursor.execute(sql, (id,))
            connection.commit()  # 변경 사항 커밋
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()

async def verify_student_id(student_stdnum, student_userid): 
    """ 학번을 MySQL에서 조회하여 인증 """
    conn = await get_db_connection()
    try:
        cursor = conn.cursor()  # 커서는 이미 dictionary로 반환되므로 cursor()만 사용
        # 사용자 ID로 사용자 정보를 조회
        cursor.execute("SELECT name, stdnum FROM devsign_member WHERE userid = %s AND withdrawal = 0", 
                       (student_userid,))  
        result = cursor.fetchone()
        conn.close()

        if result:
            # 조회된 학번과 입력된 학번을 비교
            if result['stdnum'] == student_stdnum:
                return result['name']  # 인증 성공 시 이름 반환
            else:
                return None  # 인증 실패 시 None 반환
        else:
            return None  # 조회된 결과가 없으면 None 반환

    except Exception as e:
        print(f"❌ DB 오류: {e}")
        return None