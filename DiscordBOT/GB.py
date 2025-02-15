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

    # 기존 EE.csv 파일이 있는지 확인하고 읽어오기
    if os.path.exists('GB.csv'):
        old_df = pd.read_csv('GB.csv', encoding='utf-8-sig')
        max_old_number = old_df['번호'].min()
    else:
        old_df = pd.DataFrame(columns=["번호", "제목", "게시 날짜", "URL"])
        max_old_number = 0

    # 기존 데이터와 비교하여 새로운 공지 필터링 (번호 또는 제목이 다른 경우)
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

        for index, row in new_notices_sorted.iterrows():
            embed = discord.Embed(description=f"[💡{row['제목']}]({row['URL']})", color=discord.Color.blue())
            embed.add_field(name="📆 Date", value=row["게시 날짜"], inline=True)
            await channel.send(embed=embed)

        # 업데이트된 DataFrame 병합 및 저장 (최신이 최상단)
        combined_df = pd.concat([new_notices_sorted, old_df], ignore_index=True).drop_duplicates(subset=['번호'])
        combined_df = combined_df.sort_values(by='번호', ascending=True)  # 최신 공지가 위로 가도록 정렬
        combined_df.to_csv('GB.csv', index=False, encoding='utf-8-sig')


        print("공지사항 데이터가 업데이트되었습니다.")
            # 가장 오래된 (제일 아래) 행 삭제


        # 변경된 데이터 저장
        combined_df.to_csv('GB.csv', index=False, encoding='utf-8-sig')

        print("가장 오래된 공지사항이 삭제되었습니다.", flush=True)
    else:
        print("새로운 공지사항이 없습니다.", flush=True)

@client.event
async def on_ready():
    print('the bot is now ready for use!')
    print('-----------------------------')
    check_notices_ee.start()  # 봇이 준비되면 공지사항 체크 시작

client.run(BOTTOKEN)




# # Discord에 공지사항 전송
# @tasks.loop(seconds=3)
# async def check_notices_ee():
#     data = fetch_notices_ee()
#     new_df = pd.DataFrame(data, columns=["제목", "게시 날짜", "URL"])

#     if os.path.exists("GB.csv"):
#         old_df = pd.read_csv("GB.csv", encoding="utf-8-sig")
#     else:
#         old_df = pd.DataFrame(columns=["제목", "게시 날짜", "URL"])

#     new_notices = new_df[~new_df["제목"].isin(old_df["제목"])]

#     if not new_notices.empty:
#         new_notices_sorted = new_notices.sort_values(by="게시 날짜", ascending=False)
#         channel = client.get_channel(GBID)  # 공지사항 채널 ID 사용

#         if channel:
#             for _, row in new_notices_sorted.iterrows():
#                 embed = discord.Embed(title="📢 새로운 공지사항", color=discord.Color.blue())
#                 embed.add_field(name="🔹 제목", value=f"[{row['제목']}]({row['URL']})", inline=False)
#                 embed.add_field(name="📆 게시 날짜", value=row["게시 날짜"], inline=True)
#                 await channel.send(embed=embed)

#         combined_df = pd.concat([new_notices_sorted, old_df]).drop_duplicates(subset=["제목"]).sort_values(by="게시 날짜", ascending=False)

#         if len(combined_df) > 100:
#             combined_df = combined_df.iloc[:-1]

#         combined_df.to_csv("GB.csv", index=False, encoding="utf-8-sig")

# @client.event
# async def on_ready():
#     print(f"✅ Discord 봇이 실행되었습니다. 공지사항 채널 ID: {GBID}")
#     check_notices_ee.start()

# client.run(BOTTOKEN)


