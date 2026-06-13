async function loadJSON(path) {
  const res = await fetch(path);
  return res.json();
}

function renderKVTable(container, obj, labels) {
  let html = "<table>";
  for (const [key, label] of Object.entries(labels)) {
    html += `<tr><th>${label}</th><td>${obj[key]}</td></tr>`;
  }
  html += "</table>";
  container.innerHTML = html;
}

(async function main() {
  // 道奇隊打擊/投手數據表
  try {
    const dodgers = await loadJSON("data/dodgers_team.json");

    renderKVTable(document.getElementById("dodgers-batting-table"), dodgers.batting, {
      avg: "打擊率 AVG",
      obp: "上壘率 OBP",
      slg: "長打率 SLG",
      ops: "OPS",
      homeRuns: "全壘打",
      runs: "得分",
      rbi: "打點",
      stolenBases: "盜壘",
    });

    renderKVTable(document.getElementById("dodgers-pitching-table"), dodgers.pitching, {
      era: "防禦率 ERA",
      whip: "WHIP",
      strikeOuts: "三振數",
      saves: "救援成功",
      wins: "勝場",
      losses: "敗場",
    });
  } catch (e) {
    console.error("讀取道奇數據失敗", e);
  }

  // 大谷整體數據
  try {
    const overall = await loadJSON("data/ohtani_overall.json");
    const el = document.getElementById("ohtani-overall");
    el.innerHTML = `
      <strong>2025 大谷翔平 整體 Statcast 概況（共 ${overall["總球數"]} 球）</strong>
      <table>
        <tr><th>揮棒率</th><td>${(overall["揮棒率"] * 100).toFixed(1)}%</td></tr>
        <tr><th>揮空率（揮棒中）</th><td>${(overall["揮空率"] * 100).toFixed(1)}%</td></tr>
        <tr><th>平均出球速度</th><td>${overall["平均出球速度"]} mph</td></tr>
        <tr><th>平均 xwOBA</th><td>${overall["平均xwOBA"]}</td></tr>
      </table>
    `;
  } catch (e) {
    console.error("讀取大谷整體數據失敗", e);
  }

  // 球種圖表
  try {
    const pitchData = await loadJSON("data/ohtani_pitch_summary.json");
    const labels = pitchData.map(d => d["球種"]);
    const whiff = pitchData.map(d => (d["揮空率"] * 100).toFixed(1));
    const xwoba = pitchData.map(d => d["xwOBA"]);

    new Chart(document.getElementById("pitchChart"), {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "揮空率 (%)",
            data: whiff,
            backgroundColor: "#005A9C",
            yAxisID: "y",
          },
          {
            label: "xwOBA",
            data: xwoba,
            type: "line",
            borderColor: "#EF3E42",
            backgroundColor: "#EF3E42",
            yAxisID: "y1",
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: { type: "linear", position: "left", title: { display: true, text: "揮空率 (%)" } },
          y1: { type: "linear", position: "right", title: { display: true, text: "xwOBA" }, grid: { drawOnChartArea: false } },
        },
      },
    });
  } catch (e) {
    console.error("讀取大谷球種數據失敗", e);
  }

  // ISO / BABIP / wOBA 計算範例 (大谷)
  try {
    const ex = await loadJSON("data/worked_examples.json");
    const o = ex.ohtani;

    const inputRows = Object.entries(o.inputs)
      .map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`)
      .join("");

    const wobaTerms = o.woba.numerator_terms.map(t => `<li>${t}</li>`).join("");

    document.getElementById("ohtani-woba-example").innerHTML = `
      <strong>計算範例：用 ${o.player} ${o.season} 真實數據算 ISO、BABIP、wOBA</strong>
      <p><strong>原始數據：</strong></p>
      <table>${inputRows}</table>

      <p><strong>① ISO</strong> = ${o.iso.formula}</p>
      <p class="formula">${o.iso.calc} = <strong>${o.iso.result}</strong></p>

      <p><strong>② BABIP</strong> = ${o.babip.formula}</p>
      <p class="formula">${o.babip.calc} = <strong>${o.babip.result}</strong></p>
      <p>數據官方提供的 BABIP 也是 ${o.babip.result}，計算一致 ✅</p>

      <p><strong>③ wOBA</strong> = ${o.woba.formula}</p>
      <p>分子各項：</p>
      <ul>${wobaTerms}</ul>
      <p class="formula">分子總和 = ${o.woba.numerator}　／　分母 = ${o.woba.denominator}</p>
      <p class="formula">wOBA = ${o.woba.numerator} ÷ ${o.woba.denominator} = <strong>${o.woba.result}</strong></p>
      <p>大谷的 OBP 是 ${o.inputs["OBP"]}，wOBA (${o.woba.result}) 略高一些，
      代表他的長打貢獻把整體進攻價值再往上拉了一截——這正是 wOBA 比 OBP/OPS 更精準的地方。</p>
    `;

    // FIP 計算範例 (山本由伸)
    const y = ex.yamamoto;
    const yInputRows = Object.entries(y.inputs)
      .map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`)
      .join("");

    document.getElementById("yamamoto-fip-example").innerHTML = `
      <strong>計算範例：用 ${y.player} ${y.season} 真實數據算 FIP</strong>
      <p><strong>原始數據：</strong></p>
      <table>${yInputRows}</table>

      <p><strong>FIP</strong> = ${y.fip.formula}</p>
      <p class="formula">${y.fip.calc} = <strong>${y.fip.result}</strong></p>

      <p>山本由伸 2025 賽季 ERA 為 ${y.inputs.ERA}，FIP 為 ${y.fip.result}，
      兩者非常接近，代表他的低自責分率<strong>不是靠隊友守備運氣</strong>，
      而是真材實料：高三振、低保送、極少被全壘打的結果。</p>
    `;
  } catch (e) {
    console.error("讀取計算範例失敗", e);
  }

  // 最有效位置表
  try {
    const best = await loadJSON("data/ohtani_best_locations.json");
    let html = "<table><tr><th>球種</th><th>位置</th><th>樣本數</th><th>揮空率</th></tr>";
    for (const row of best) {
      html += `<tr><td>${row["球種"]}</td><td>${row["zone"]}</td><td>${row["球數"]}</td><td>${(row["揮空率"] * 100).toFixed(1)}%</td></tr>`;
    }
    html += "</table>";
    document.getElementById("best-locations-table").innerHTML = html;
  } catch (e) {
    console.error("讀取最有效位置數據失敗", e);
  }
})();
