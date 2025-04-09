import pymysql
import re
from config import (HOST, PORT, USER, PASSWORD, DATABASE, CHARSET)

def get_db_connection():
    """MySQL 데이터베이스 연결을 생성"""
    return pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        charset=CHARSET,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor  # 딕셔너리 형태로 결과 반환
    )

# 닉네임에서 학번, 이름, 상태(재학/휴학) 추출
def parse_nickname(nickname: str) -> tuple[str, str, str]:
    if not nickname or nickname.strip() == "" or nickname == "DEVSIGN":
        return None, None, None

    parts = nickname.split(" ", 1)
    if len(parts) < 2:
        return None, None, None
    
    stdnum_raw, name = parts
    state = "재학"

    name = re.sub(r"\(.*?\)", "", name).strip()
    
    if stdnum_raw.startswith("v"):
        state = "휴학"
        stdnum = stdnum_raw[1:]
    else:
        stdnum = stdnum_raw

    return stdnum, name, state

# 사용자 정보 조회
def get_user_info(cursor, stdnum: str, name: str):
    query = "SELECT id FROM devsign_member WHERE stdnum REGEXP %s AND name = %s AND withdrawal = 0 AND userid IS NULL"
    cursor.execute(query, ("^.."+stdnum +"....$", name))
    return cursor.fetchone()

# 사용자 정보 저장 또는 업데이트
def save_or_update_user(cursor, id: str, name: str, username: str, userid: str, state: str):
    query = """
        UPDATE devsign_member 
        SET username = %s, userid = %s, state = %s
        WHERE id = %s AND name = %s
    """
    cursor.execute(query, (username, userid, state, id, name))

# 학번과 이름으로 사용자 조회
def fetch_matching_users(cursor, stdnum: str, name: str):
    query = "SELECT * FROM devsign_member WHERE stdnum REGEXP %s AND name = %s AND withdrawal = 0"
    cursor.execute(query, ("^.."+stdnum +"....$", name))
    return cursor.fetchall()

# 사용자 정보 업데이트
def update_user_info(cursor, id: str, name: str, username: str, userid: str, state: str):
    query = """
        UPDATE devsign_member 
        SET username = %s, userid = %s, state = %s
        WHERE id = %s AND name = %s
    """
    cursor.execute(query, (username, userid, state, id, name))

# 특정 학번을 가진 사용자 조회
def get_students_by_stdnum(stdnum: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM devsign_member WHERE stdnum REGEXP %s"
            cursor.execute(sql, ("^.."+stdnum +"....$",))
            return cursor.fetchall()
    finally:
        conn.close()

# 사용자 졸업 처리
def update_graduation_status(id: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE devsign_member SET state = '졸업', withdrawal = 1 WHERE id = %s"
            cursor.execute(sql, (id,))
            conn.commit()
    finally:
        conn.close()

# 사용자 삭제 처리
def delete_data(id: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM devsign_member WHERE id = %s"
            cursor.execute(sql, (id,))
            conn.commit()
    finally:
        conn.close()

# 학번 인증
def verify_student_id(student_stdnum, student_userid): 
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, stdnum FROM devsign_member WHERE userid = %s AND withdrawal = 0", (student_userid,))
        result = cursor.fetchone()
        if result and result['stdnum'] == student_stdnum:
            return result['name']
        return None
    finally:
        conn.close()