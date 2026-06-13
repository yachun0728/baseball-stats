"""
大谷翔平 2025 打擊進階數據分析
- 各球種表現 (打擊率/長打率/揮空率)
- 好球帶熱點圖 (揮棒率、長打、揮空)
- 對他最有效的球種/位置
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
fm.fontManager.addfont("/System/Library/Fonts/STHeiti Medium.ttc")
plt.rcParams["font.family"] = "Heiti TC"
plt.rcParams["axes.unicode_minus"] = False
from pybaseball import statcast_batter

OHTANI_ID = 660271
START = "2025-03-01"
END = "2025-10-01"

PITCH_NAMES = {
    "FF": "四縫線速球", "SI": "二縫線速球", "FC": "卡特球", "SL": "滑球",
    "ST": "橫掃滑球", "CU": "曲球", "CH": "變速球", "FS": "指叉球",
    "KC": "彎曲曲球", "FO": "Forkball",
}


def load_data():
    df = statcast_batter(START, END, OHTANI_ID)
    df = df.dropna(subset=["pitch_type"])
    return df


def pitch_type_summary(df):
    """各球種：揮空率、打擊率、長打率、平均出球速度"""
    rows = []
    for pt, g in df.groupby("pitch_type"):
        n = len(g)
        swings = g["description"].isin(
            ["swinging_strike", "foul", "hit_into_play", "swinging_strike_blocked", "foul_tip"]
        ).sum()
        whiffs = g["description"].isin(["swinging_strike", "swinging_strike_blocked", "foul_tip"]).sum()
        whiff_rate = whiffs / swings if swings > 0 else 0

        # 打席結果（用 events 非空的 row 估算打擊成效）
        balls_in_play = g[g["description"] == "hit_into_play"]
        avg_ev = balls_in_play["launch_speed"].mean()
        avg_la = balls_in_play["launch_angle"].mean()

        # estimate batting outcome value via woba/xwoba if available
        xwoba = g["estimated_woba_using_speedangle"].mean()

        rows.append({
            "pitch_type": pt,
            "球種": PITCH_NAMES.get(pt, pt),
            "球數": n,
            "揮空率": round(whiff_rate, 3),
            "平均出球速度": round(avg_ev, 1) if pd.notna(avg_ev) else None,
            "平均擊球角度": round(avg_la, 1) if pd.notna(avg_la) else None,
            "xwOBA": round(xwoba, 3) if pd.notna(xwoba) else None,
        })
    out = pd.DataFrame(rows).sort_values("球數", ascending=False)
    return out


def zone_heatmap(df, outfile="ohtani_zone_swing.png"):
    """好球帶熱點圖：揮棒率 + 長打分布"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    # 全部來球位置
    ax = axes[0]
    sc = ax.hexbin(df["plate_x"], df["plate_z"], gridsize=20, cmap="Blues")
    ax.set_title("來球位置分布 (投手攻擊熱點)")
    _draw_zone(ax)
    fig.colorbar(sc, ax=ax)

    # 揮棒且形成長打 (double/triple/home_run) 的位置
    ax = axes[1]
    extra_base = df[df["events"].isin(["double", "triple", "home_run"])]
    sc = ax.hexbin(extra_base["plate_x"], extra_base["plate_z"], gridsize=15, cmap="Reds")
    ax.set_title("長打(2B/3B/HR)落點 - 球的位置")
    _draw_zone(ax)
    fig.colorbar(sc, ax=ax)

    plt.tight_layout()
    plt.savefig(outfile, dpi=120)
    print(f"已儲存熱點圖: {outfile}")


def _draw_zone(ax):
    """畫出大谷的好球帶範圍 (strikeZoneTop=3.369, strikeZoneBottom=1.7)"""
    ax.add_patch(plt.Rectangle((-0.83, 1.7), 1.66, 3.369 - 1.7, fill=False, edgecolor="black", linewidth=2))
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(0, 5)
    ax.set_xlabel("plate_x (左右)")
    ax.set_ylabel("plate_z (高低)")


def best_pitch_locations_against_him(df):
    """找出對大谷最有效的球種+位置組合 (高揮空率)"""
    swings = df[df["description"].isin(
        ["swinging_strike", "foul", "hit_into_play", "swinging_strike_blocked", "foul_tip"]
    )].copy()
    swings["whiff"] = swings["description"].isin(
        ["swinging_strike", "swinging_strike_blocked", "foul_tip"]
    ).astype(int)

    # 切分好球帶為 3x3 區域
    def zone_label(row):
        x, z = row["plate_x"], row["plate_z"]
        col = "內" if x < -0.3 else ("外" if x > 0.3 else "中")
        row_ = "高" if z > 2.7 else ("低" if z < 2.0 else "中")
        return f"{row_}{col}"

    swings["zone"] = swings.apply(zone_label, axis=1)

    grp = swings.groupby(["pitch_type", "zone"]).agg(
        球數=("whiff", "count"), 揮空率=("whiff", "mean")
    ).reset_index()
    grp = grp[grp["球數"] >= 10].sort_values("揮空率", ascending=False)
    grp["球種"] = grp["pitch_type"].map(lambda x: PITCH_NAMES.get(x, x))
    return grp.head(10)


if __name__ == "__main__":
    print("抓取大谷翔平 2025 Statcast 數據...")
    df = load_data()
    print(f"共 {len(df)} 顆球\n")

    print("=== 各球種表現 ===")
    summary = pitch_type_summary(df)
    print(summary.to_string(index=False))

    print("\n=== 對他最有效的「球種+位置」組合 (揮空率最高) ===")
    best = best_pitch_locations_against_him(df)
    print(best[["球種", "zone", "球數", "揮空率"]].to_string(index=False))

    zone_heatmap(df)
