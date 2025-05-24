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
    base_url = 'https://see.knu.ac.kr'
    url = base_url + '/content/board/notice.html'

    response = requests.get(url)
    response.encoding = 'utf-8'
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    selector = '#content > div > div > div.board_list > div.board_body > table > tbody'
    board_body = soup.select_one(selector)

    data = []

    if board_body:
        notices = board_body.find_all('tr')

        for notice in notices:
            cells = notice.find_all('td')
            if cells and cells[0].text.strip():
                number = int(cells[0].text.strip())
                category_span = notice.select_one('td.left a span')
                category = category_span.text.strip() if category_span else '카테고리 없음'
                title_text = category_span.find_next_sibling(string=True) if category_span else None
                title = title_text.strip() if title_text else '제목 없음'       
                
                date = cells[3].text.strip()

                # ✅ 링크 처리 수정
                link_tag = notice.find('td', class_='left').find('a')
                link = link_tag.get('href') if link_tag and link_tag.has_attr('href') else None

                if link:
                    # 혹시라도 link에 "?"나 이상한 문자가 포함되었을 경우 제거
                    link = link.strip()
                    if link.startswith('/'):
                        full_link = f"{base_url}{link}"
                    else:
                        full_link = url +link
                else:
                    full_link = '링크 없음'

                print(f"DEBUG: {title} -> {full_link}")  # 디버깅용 출력

                # ✅ Markdown 링크 수정
                formatted_link = f"[{title}](<{full_link}>)"

                data.append([number, category, formatted_link, date, full_link])

    return data




@tasks.loop(seconds=20)  # 5초마다 웹사이트를 체크합니다.
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
        new_notices_sorted = new_notices.sort_values(by='번호', ascending=True)
        print("새로운 공지사항이 발견되었습니다:")
        print(new_notices_sorted)

        channel = client.get_channel(EEID)  # 실제 채널 ID로 변경
        if channel is None:
            print("채널을 찾을 수 없습니다. 채널 ID를 확인하세요.")
            return

        for index, row in new_notices_sorted.iterrows():
            embed = discord.Embed(
                description=f"💡 {row['제목']}",  # 제목 앞에 💡 추가
                color=discord.Color.blue()
            )
            embed.add_field(name="📅 Date", value=row["날짜"], inline=True)
            await channel.send(embed=embed)



        # 업데이트된 DataFrame 병합 및 저장 (새로운 공지가 최상단에 위치하도록)
        combined_df = pd.concat([new_notices_sorted, old_df]).drop_duplicates(subset=['번호']).sort_values(by='번호', ascending=False)
        combined_df.to_csv('EE.csv', index=False, encoding='utf-8-sig')

        print("공지사항 데이터가 업데이트되었습니다.")
        # 가장 오래된 (제일 아래) 행 삭제
        # combined_df = combined_df.iloc[:-1]

        # 변경된 데이터 저장
        combined_df.to_csv('EE.csv', index=False, encoding='utf-8-sig')

        print("가장 오래된 공지사항이 삭제되었습니다.", flush=True)
    else:
        print("새로운 공지사항이 없습니다.", flush=True)

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
