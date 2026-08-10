# CS Paper Deadlines — merged calendar feed

`labmate.cloud`의 8개 분야(보안·암호 SC, 데이터베이스 DB, 컴퓨터 시스템 DS, 그래픽스·비전 CG,
네트워크 NW, 인공지능 AI, 소프트웨어공학 SE, 수학·통계 MATH) **투고 마감(paper submission
deadline)만** 병합·중복제거한 단일 캘린더. GitHub Action이 12시간마다 갱신.

## 애플 캘린더 구독 (자동 갱신)
캘린더 앱 → **파일 → 새로운 캘린더 구독…** → 아래 URL 붙여넣기 → 자동 새로고침 "매일":

```
https://raw.githubusercontent.com/espressolee/paper-deadlines/main/paper-deadlines.ics
```

Safari 주소창에 붙여넣으면 구독창이 바로 뜨는 형태:
```
webcal://raw.githubusercontent.com/espressolee/paper-deadlines/main/paper-deadlines.ics
```

## 분야 바꾸기
`merge_deadlines.py`의 `CODES` 편집 (labmate 페이지에서 분야 필터 클릭 → "캘린더 피드 URL 복사"로 `?sub=` 코드 확인).

## 수동 갱신
`python merge_deadlines.py` 또는 Actions 탭 → update-deadlines → Run workflow.

출처: https://labmate.cloud/ko/conferences
