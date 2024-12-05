import os
import requests
from dotenv import load_dotenv

# 환경 변수 파일 경로 명시
load_dotenv("2.env")

# Notion API 설정
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Notion API 헤더
notion_headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Notion 데이터베이스 데이터 가져오기
def fetch_notion_calendar(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    response = requests.post(url, headers=notion_headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching Notion data: {response.status_code}")
        return None

# HTML 테이블 변환
def convert_to_html(data):
    rows = []
    for result in data["results"]:
        props = result["properties"]
        name = props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else "Untitled"
        date = props["Date"]["date"]["start"] if props["Date"]["date"] else "No Date"
        rows.append(f"<tr><td>{date}</td><td>{name}</td></tr>")
    
    html_table = "<table border='1'><tr><th>Date</th><th>Event Name</th></tr>" + "".join(rows) + "</table>"
    return html_table

# HTML 파일 생성
def generate_html_file(content, output_path="calendar.html"):
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(f"<html><body>{content}</body></html>")
    print(f"HTML file generated: {output_path}")

# 실행
if __name__ == "__main__":
    notion_data = fetch_notion_calendar(DATABASE_ID)
    if notion_data:
        html_content = convert_to_html(notion_data)
        generate_html_file(html_content)