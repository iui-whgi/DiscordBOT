import discord
from discord.ext import commands, tasks
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from apikeys import *  # apikeys.py에서 토큰과 채널 ID 불러오기

# Discord Bot 설정
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)

# 공지사항 크롤링 함수
def fetch_notices_ee():
    base_url = "https://home.knu.ac.kr"
    url = base_url + "/HOME/global/sub.htm?nav_code=glo1729572883"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    selector = "#body_content > div.board_list > table > tbody"
    board_body = soup.select_one(selector)

    data = []
    if board_body:
        notices = board_body.find_all("tr")
        for idx, notice in enumerate(notices, start=1):
            title_element = notice.select_one("td.subject a")
            date_element = notice.select_one("td:nth-child(5)")

            if title_element and date_element:
                title = title_element.text.strip()
                date = date_element.text.strip()
                link = base_url + title_element["href"].strip()
                data.append([idx, title, date, link])

    return data


@tasks.loop(seconds=10)
async def check_notices_ee():
    data = fetch_notices_ee()
    new_df = pd.DataFrame(data, columns=["번호", "제목", "게시 날짜", "URL"])

    # 기존 CSV 파일 확인
    if os.path.exists('GB.csv'):
        old_df = pd.read_csv('GB.csv', encoding='utf-8-sig')
    else:
        old_df = pd.DataFrame(columns=["번호", "제목", "게시 날짜", "URL"])

    # 기존 데이터와 비교하여 새로운 제목만 필터링
    new_notices = new_df[~new_df["제목"].isin(old_df["제목"])]

    # 새로운 공지가 있으면 디스코드 채널에 알림
    if not new_notices.empty:
        new_notices_sorted = new_notices.sort_values(by='번호', ascending=False)  # 최신순 정렬
        print("새로운 공지사항이 발견되었습니다:")
        print(new_notices_sorted)

        channel = client.get_channel(GBID)  # 실제 채널 ID로 변경
        if channel is None:
            print("채널을 찾을 수 없습니다. 채널 ID를 확인하세요.")
            return

        for _, row in new_notices_sorted.iterrows():
            embed = discord.Embed(description=f"[💡{row['제목']}]({row['URL']})", color=discord.Color.blue())
            embed.add_field(name="📆 Date", value=row["게시 날짜"], inline=True)
            await channel.send(embed=embed)

        # 기존 CSV에 새로운 공지사항 추가
        updated_df = pd.concat([old_df, new_notices_sorted], ignore_index=True).drop_duplicates(subset=["제목"])
        updated_df = updated_df.sort_values(by="번호", ascending=True)  # 최신 공지가 위로 가도록 정렬
        updated_df.to_csv('GB.csv', index=False, encoding='utf-8-sig')

        print("공지사항 데이터가 업데이트되었습니다.", flush=True)
    else:
        print("새로운 공지사항이 없습니다.", flush=True)


@client.event
async def on_ready():
    print('the bot is now ready for use!')
    print('-----------------------------')
    check_notices_ee.start()  # 봇이 준비되면 공지사항 체크 시작

client.run(BOTTOKEN)
