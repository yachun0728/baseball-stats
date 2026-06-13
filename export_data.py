"""
匯出真實數據成 JSON，供說明網站的互動圖表使用
"""
import json
import requests
import pandas as pd
from ohtani_analysis import load_data, pitch_type_summary, best_pitch_locations_against_him

OUT_DIR = "site/data"


def export_ohtani():
    df = load_data()

    # 球種表現
    summary = pitch_type_summary(df)
    summary = summary[summary["球數"] >= 10]  # 過濾樣本太少的球種
    pitch_data = summary[["球種", "球數", "揮空率", "平均出球速度", "xwOBA"]].to_dict(orient="records")

    # 最有效球種+位置
    best = best_pitch_locations_against_him(df)
    best_data = best[["球種", "zone", "球數", "揮空率"]].to_dict(orient="records")

    # 整體打席結果統計 (估算進階指標用)
    swings = df[df["description"].isin(
        ["swinging_strike", "foul", "hit_into_play", "swinging_strike_blocked", "foul_tip"]
    )]
    total_pitches = len(df)
    total_swings = len(swings)
    whiffs = df["description"].isin(["swinging_strike", "swinging_strike_blocked", "foul_tip"]).sum()

    balls_in_play = df[df["description"] == "hit_into_play"]
    avg_ev = balls_in_play["launch_speed"].mean()
    barrel_rate = (balls_in_play["launch_speed"] >= 98).mean()  # 簡化版barrel判定示意
    avg_xwoba = df["estimated_woba_using_speedangle"].mean()

    overall = {
        "總球數": int(total_pitches),
        "揮棒率": round(total_swings / total_pitches, 3),
        "揮空率": round(whiffs / total_swings, 3),
        "平均出球速度": round(float(avg_ev), 1),
        "高速擊球比例(>=98mph)示意": round(float(barrel_rate), 3),
        "平均xwOBA": round(float(avg_xwoba), 3),
    }

    with open(f"{OUT_DIR}/ohtani_pitch_summary.json", "w", encoding="utf-8") as f:
        json.dump(pitch_data, f, ensure_ascii=False, indent=2)

    with open(f"{OUT_DIR}/ohtani_best_locations.json", "w", encoding="utf-8") as f:
        json.dump(best_data, f, ensure_ascii=False, indent=2)

    with open(f"{OUT_DIR}/ohtani_overall.json", "w", encoding="utf-8") as f:
        json.dump(overall, f, ensure_ascii=False, indent=2)

    print("已匯出大谷數據")


def export_dodgers_team():
    DODGERS_ID = 119
    SEASON = 2025
    BASE = "https://statsapi.mlb.com/api/v1"

    r = requests.get(f"{BASE}/teams/{DODGERS_ID}/stats",
                      params={"stats": "season", "group": "hitting", "season": SEASON})
    hitting = r.json()["stats"][0]["splits"][0]["stat"]

    r = requests.get(f"{BASE}/teams/{DODGERS_ID}/stats",
                      params={"stats": "season", "group": "pitching", "season": SEASON})
    pitching = r.json()["stats"][0]["splits"][0]["stat"]

    data = {
        "season": SEASON,
        "team": "Los Angeles Dodgers",
        "batting": {k: hitting.get(k) for k in ["avg", "obp", "slg", "ops", "homeRuns", "runs", "rbi", "stolenBases"]},
        "pitching": {k: pitching.get(k) for k in ["era", "whip", "strikeOuts", "saves", "wins", "losses"]},
    }

    with open(f"{OUT_DIR}/dodgers_team.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("已匯出道奇隊數據")


def export_worked_examples():
    """匯出進階指標的逐步計算範例 (大谷打擊 wOBA/ISO/BABIP, 山本由伸投手 FIP)"""
    BASE = "https://statsapi.mlb.com/api/v1"
    SEASON = 2025

    # 大谷 2025 打擊數據
    r = requests.get(f"{BASE}/people/660271/stats", params={"stats": "season", "group": "hitting", "season": SEASON})
    h = r.json()["stats"][0]["splits"][0]["stat"]

    AB, H, B2, B3, HR = h["atBats"], h["hits"], h["doubles"], h["triples"], h["homeRuns"]
    BB, IBB, HBP, SF, SO = h["baseOnBalls"], h["intentionalWalks"], h["hitByPitch"], h["sacFlies"], h["strikeOuts"]
    B1 = H - B2 - B3 - HR
    uBB = BB - IBB

    # ISO
    iso = round(float(h["slg"]) - float(h["avg"]), 3)

    # BABIP
    babip_denom = AB - SO - HR + SF
    babip = round((H - HR) / babip_denom, 3)

    # wOBA (FanGraphs 2013 通用權重，僅供教學示意)
    weights = {"uBB": 0.69, "HBP": 0.72, "1B": 0.89, "2B": 1.27, "3B": 1.62, "HR": 2.10}
    woba_num = (weights["uBB"] * uBB + weights["HBP"] * HBP + weights["1B"] * B1
                + weights["2B"] * B2 + weights["3B"] * B3 + weights["HR"] * HR)
    woba_denom = AB + BB - IBB + SF + HBP
    woba = round(woba_num / woba_denom, 3)

    ohtani_example = {
        "player": "大谷翔平 (Shohei Ohtani)",
        "season": SEASON,
        "inputs": {
            "打數 AB": AB, "安打 H": H, "一安 1B": B1, "二安 2B": B2, "三安 3B": B3, "全壘打 HR": HR,
            "保送 BB": BB, "故意四壞 IBB": IBB, "觸身球 HBP": HBP, "高飛犧牲打 SF": SF, "三振 SO": SO,
            "AVG": h["avg"], "SLG": h["slg"], "OBP": h["obp"],
        },
        "iso": {"formula": "SLG - AVG", "calc": f"{h['slg']} - {h['avg']}", "result": iso},
        "babip": {
            "formula": "(H - HR) / (AB - SO - HR + SF)",
            "calc": f"({H} - {HR}) / ({AB} - {SO} - {HR} + {SF}) = {H-HR} / {babip_denom}",
            "result": babip,
        },
        "woba": {
            "formula": "(0.69×uBB + 0.72×HBP + 0.89×1B + 1.27×2B + 1.62×3B + 2.10×HR) / (AB + BB - IBB + SF + HBP)",
            "numerator_terms": [
                f"0.69 × {uBB}(uBB) = {round(weights['uBB']*uBB, 2)}",
                f"0.72 × {HBP}(HBP) = {round(weights['HBP']*HBP, 2)}",
                f"0.89 × {B1}(1B) = {round(weights['1B']*B1, 2)}",
                f"1.27 × {B2}(2B) = {round(weights['2B']*B2, 2)}",
                f"1.62 × {B3}(3B) = {round(weights['3B']*B3, 2)}",
                f"2.10 × {HR}(HR) = {round(weights['HR']*HR, 2)}",
            ],
            "numerator": round(woba_num, 2),
            "denominator": woba_denom,
            "result": woba,
        },
    }

    # 山本由伸 2025 投手數據 (FIP 範例)
    r = requests.get(f"{BASE}/people/808967/stats", params={"stats": "season", "group": "pitching", "season": SEASON})
    p = r.json()["stats"][0]["splits"][0]["stat"]

    ip_str = p["inningsPitched"]  # e.g. "173.2" -> 173 + 2/3 局
    ip_whole, ip_frac = ip_str.split(".")
    ip = int(ip_whole) + int(ip_frac) / 3
    p_hr, p_bb, p_hbp, p_k = p["homeRuns"], p["baseOnBalls"], p["hitByPitch"], p["strikeOuts"]
    FIP_CONSTANT = 3.10  # 近年聯盟常數約在 3.0~3.2 之間，此處取教學用近似值

    fip_num = 13 * p_hr + 3 * (p_bb + p_hbp) - 2 * p_k
    fip = round(fip_num / ip + FIP_CONSTANT, 2)

    yamamoto_example = {
        "player": "山本由伸 (Yoshinobu Yamamoto)",
        "season": SEASON,
        "inputs": {
            "投球局數 IP": ip_str, "被全壘打 HR": p_hr, "保送 BB": p_bb,
            "觸身球 HBP": p_hbp, "三振 K": p_k, "ERA": p["era"], "FIP常數": FIP_CONSTANT,
        },
        "fip": {
            "formula": "(13×HR + 3×(BB+HBP) - 2×K) / IP + 常數(3.10)",
            "calc": f"(13×{p_hr} + 3×({p_bb}+{p_hbp}) - 2×{p_k}) / {ip:.3f} + 3.10"
                    f" = ({13*p_hr} + {3*(p_bb+p_hbp)} - {2*p_k}) / {ip:.3f} + 3.10"
                    f" = {fip_num} / {ip:.3f} + 3.10",
            "result": fip,
        },
    }

    with open(f"{OUT_DIR}/worked_examples.json", "w", encoding="utf-8") as f:
        json.dump({"ohtani": ohtani_example, "yamamoto": yamamoto_example}, f, ensure_ascii=False, indent=2)

    print("已匯出計算範例")


if __name__ == "__main__":
    export_ohtani()
    export_dodgers_team()
    export_worked_examples()
