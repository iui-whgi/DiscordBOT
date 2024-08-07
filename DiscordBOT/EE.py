import discord
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os

from apikeys import *

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='!', intents=intents)

def fetch_notices_ee():
    # 웹페이지 URL
    base_url = 'https://see.knu.ac.kr'
    url = base_url + '/content/board/notice.html'

    # 웹페이지 요청
    response = requests.get(url)
    response.encoding = 'utf-8'  # 인코딩을 'utf-8'로 설정
    response.raise_for_status()  # 요청이 성공했는지 확인

    # BeautifulSoup으로 HTML 파싱
    soup = BeautifulSoup(response.text, 'html.parser')

    # 주어진 CSS 선택자를 사용하여 공지사항 목록 추출
    selector = '#content > div > div > div.board_list > div.board_body > table > tbody'
    board_body = soup.select_one(selector)

    # 공지사항 데이터를 저장할 리스트 초기화
    data = []

    if board_body:
        notices = board_body.find_all('tr')  # 각 공지사항은 table row로 표시되어 있습니다.

        # 공지사항 데이터 추출
        for notice in notices:
            cells = notice.find_all('td')
            if cells and cells[0].text.strip():  # 번호 칼럼이 존재하는지 확인
                number = int(cells[0].text.strip())  # 공지 번호를 정수로 변환
                category_span = notice.select_one('td.left a span')
                category = category_span.text.strip() if category_span else '카테고리 없음'
                title = category_span.find_next_sibling(text=True).strip() if category_span else '제목 없음'
                date = cells[3].text.strip()  # 날짜
                link = notice.select_one('td.left a')['href'] if notice.select_one('td.left a') else '링크 없음'  # 공지사항 링크
                full_link = base_url + link if link != '링크 없음' else '링크 없음'  # 전체 링크 생성
                data.append([number, category, title, date, full_link])

    return data

@tasks.loop(seconds=5)  # 5초마다 웹사이트를 체크합니다.
async def check_notices_ee():
    # 공지사항 데이터 가져오기
    data = fetch_notices_ee()

    # DataFrame으로 변환
    new_df = pd.DataFrame(data, columns=['번호', '카테고리', '제목', '날짜', 'URL'])

    # 기존 EE.csv 파일이 있는지 확인하고 읽어오기
    if os.path.exists('EE.csv'):
        old_df = pd.read_csv('EE.csv', encoding='utf-8-sig')
        # DB에서 제일 상단(가장 최신)의 번호 확인
        max_old_number = old_df['번호'].max()
    else:
        old_df = pd.DataFrame(columns=['번호', '카테고리', '제목', '날짜', 'URL'])
        max_old_number = 0

    # 새로운 공지사항 확인 (제일 상단 번호보다 높은 번호의 공지사항만)
    new_notices = new_df[new_df['번호'] > max_old_number]

    # 새로운 공지가 있으면 디스코드 채널에 알림
    if not new_notices.empty:
        new_notices_sorted = new_notices.sort_values(by='번호', ascending=False)
        print("새로운 공지사항이 발견되었습니다:")
        print(new_notices_sorted)

        channel = client.get_channel(EEID)  # 실제 채널 ID로 변경
        if channel is None:
            print("채널을 찾을 수 없습니다. 채널 ID를 확인하세요.")
            return

        for index, row in new_notices_sorted.iterrows():
            embed = discord.Embed(description=f"[💡{row['제목']}]({row['URL']})", color=discord.Color.blue())
            embed.add_field(name="📆 Date", value=row["날짜"], inline=True)
            await channel.send(embed=embed)

        # 업데이트된 DataFrame 병합 및 저장 (새로운 공지가 최상단에 위치하도록)
        combined_df = pd.concat([new_notices_sorted, old_df]).drop_duplicates(subset=['번호']).sort_values(by='번호', ascending=False)
        combined_df.to_csv('EE.csv', index=False, encoding='utf-8-sig')

        print("공지사항 데이터가 업데이트되었습니다.")
    else:
        print("새로운 공지사항이 없습니다.")

@client.event
async def on_ready():
    print('the bot is now ready for use!')
    print('-----------------------------')
    check_notices_ee.start()  # 봇이 준비되면 공지사항 체크 시작

@client.event
async def on_member_join(member):
    print('hello ' + str(member))
    await member.send('Test')

client.run(BOTTOKEN)
