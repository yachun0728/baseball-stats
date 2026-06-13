"""
道奇隊數據分析 - 初步探索腳本
使用 MLB Stats API (statsapi.mlb.com) - 官方公開 API，無需 key
"""
import requests
import pandas as pd

DODGERS_ID = 119
SEASON = 2025

BASE = "https://statsapi.mlb.com/api/v1"


def get_standings():
    """取得道奇隊所在分區戰績"""
    r = requests.get(f"{BASE}/standings", params={"leagueId": 104, "season": SEASON})
    r.raise_for_status()
    records = r.json()["records"]
    for div in records:
        for team in div["teamRecords"]:
            if team["team"]["id"] == DODGERS_ID:
                return team
    return None


def get_team_hitting_stats():
    """取得道奇隊整體打擊數據"""
    r = requests.get(
        f"{BASE}/teams/{DODGERS_ID}/stats",
        params={"stats": "season", "group": "hitting", "season": SEASON},
    )
    r.raise_for_status()
    return r.json()["stats"][0]["splits"][0]["stat"]


def get_team_pitching_stats():
    """取得道奇隊整體投手數據"""
    r = requests.get(
        f"{BASE}/teams/{DODGERS_ID}/stats",
        params={"stats": "season", "group": "pitching", "season": SEASON},
    )
    r.raise_for_status()
    return r.json()["stats"][0]["splits"][0]["stat"]


def get_roster_hitting_leaders():
    """取得球員打擊數據排行"""
    r = requests.get(
        f"{BASE}/teams/{DODGERS_ID}/stats",
        params={"stats": "season", "group": "hitting", "season": SEASON, "personId": ""},
    )
    return r.json()


if __name__ == "__main__":
    print(f"=== {SEASON} 道奇隊戰績 ===")
    record = get_standings()
    print(f"勝-負: {record['wins']}-{record['losses']}")
    print(f"勝率: {record['winningPercentage']}")
    print(f"分區排名: {record['divisionRank']}")
    print(f"勝差: {record['gamesBack']}")

    print(f"\n=== {SEASON} 道奇隊打擊數據 ===")
    hitting = get_team_hitting_stats()
    for k in ["avg", "obp", "slg", "ops", "homeRuns", "runs", "rbi", "stolenBases"]:
        print(f"{k}: {hitting.get(k)}")

    print(f"\n=== {SEASON} 道奇隊投手數據 ===")
    pitching = get_team_pitching_stats()
    for k in ["era", "whip", "strikeOuts", "walks", "saves", "wins", "losses"]:
        print(f"{k}: {pitching.get(k)}")
