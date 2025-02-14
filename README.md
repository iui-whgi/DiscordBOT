# DiscordBOT
디스코드 경북대 전자공학부/컴퓨터공학부 알림 봇

1. EE.py 실행
bash
복사
편집
nohup python3 EE.py > EE.log 2>&1 &
2. CS.py 실행
bash
복사
편집
nohup python3 CS.py > CS.log 2>&1 &
설명
nohup → 터미널을 꺼도 프로세스가 종료되지 않도록 함.
> EE.log 2>&1 → 실행 로그를 EE.log 파일에 저장.
& → 백그라운드에서 실행.



```
nohup python3 CS.py > CS.log 2>&1 &
pkill -f CS.py
```

cd ~/Desktop/isaacsim/workspace
git init
git remote add origin https://github.com/airobotics01/iui_whgi.git

git remote -v
git add .
git commit -m "Initial commit: 로컬 코드 업로드"
git branch -M main
git push -u origin main



git add . && git commit -m "First Commit" && git branch -M main && git push -u origin main




git config --global user.name "iui-whgi"
git config --global user.email "stommy147@gmail.com"

git config --global --list




## 0214 .pem파일뭐지..?기억안나네 딱히 필요없는듯 ?


