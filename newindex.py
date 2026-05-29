import os
import subprocess
import sys

# ==============================================================================
# 0. 自動檢查並安裝缺少套件的防呆機制
# ==============================================================================
required_packages = {
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "plotly": "plotly",
}

for ioc_name, pip_name in required_packages.items():
    try:
        __import__(ioc_name)
    except ImportError:
        print(f"偵測到未安裝套件 {pip_name}，正在自動為您安裝...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. 設定檔案路徑與讀取資料
# ==============================================================================
excel_path = "C:/Users/etien/OneDrive/桌面/視覺化期末/台北犯罪與超商距離分析_20m.xlsx"

if not os.path.exists(excel_path):
    if os.path.exists("台北犯罪與超商距離分析_20m.xlsx"):
        excel_path = "台北犯罪與超商距離分析_20m.xlsx"
    else:
        print("【錯誤】找不到 Excel 檔案，請確認檔案路徑是否正確。")
        sys.exit(1)

print(f"成功找到資料來源：{excel_path}，正在載入數據...")

try:
    df_crime_total = pd.read_excel(excel_path, sheet_name="犯罪總表_最近超商距離")
    df_district_summary = pd.read_excel(excel_path, sheet_name="行政區案類摘要")
    df_distance_group = pd.read_excel(excel_path, sheet_name="距離分組摘要")
    df_type_summary = pd.read_excel(excel_path, sheet_name="案類摘要")
except Exception as e:
    print(f"【錯誤】讀取 Excel 工作表時發生問題：{e}")
    sys.exit(1)

# ==============================================================================
# 2. 定義全域字體與樣式
# ==============================================================================
GLOBAL_FONT = dict(family="Microsoft JhengHei, sans-serif", size=14, color="#2d3748")
TITLE_FONT = dict(family="Microsoft JhengHei, sans-serif", size=19, color="#1a202c")

# ==============================================================================
# 3. 圖表一：行政區案類摘要 (新增由高到低排序)
# ==============================================================================
print("正在繪製圖表一：行政區犯罪件數堆疊長條圖...")

fig1 = px.bar(
    df_district_summary,
    x="行政區",
    y="件數",
    color="案類",
    color_discrete_map={"住宅竊盜": "#3182CE", "機車竊盜": "#DD6B20"}, 
    barmode="stack"
)

fig1.update_layout(
    title=dict(text="<b>台北市各行政區犯罪案類件數統計</b>", font=TITLE_FONT, x=0.5),
    font=GLOBAL_FONT,
    # 這裡加上 categoryorder='total descending' 來自動計算堆疊總和並由高到低排序
    xaxis=dict(title="<b>行政區</b>", tickfont=dict(size=12), tickangle=0, categoryorder='total descending'),
    yaxis=dict(title="<b>犯罪件數 (件)</b>"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=100, b=50, l=50, r=50),
    paper_bgcolor="white",
    plot_bgcolor="#f7fafc"
)

# ==============================================================================
# 4. 圖表二：距離分組摘要（綠色安全與漸層紅危險配色）
# ==============================================================================
print("正在繪製圖表二：分組環域特徵甜甜圈圖...")

cat_order = ['0-20m', '20-100m', '100-200m', '200-500m', '500-1000m', '1000m以上']
df_distance_group['距離分組'] = pd.Categorical(df_distance_group['距離分組'], categories=cat_order, ordered=True)
df_distance_group = df_distance_group.sort_values('距離分組')

fig2 = go.Figure(data=[go.Pie(
    labels=df_distance_group["距離分組"],
    values=df_distance_group["件數"],
    hole=0.55,
    sort=False, 
    marker=dict(
        colors=["#48BB78", "#FFC7C7", "#FF8A8A", "#E53E3E", "#760031", "#42001C"], 
        line=dict(color='#ffffff', width=2)
    ), 
    insidetextfont=dict(family="Microsoft JhengHei", size=13), 
    outsidetextfont=dict(family="Microsoft JhengHei", size=13, color="#2d3748"),
    textinfo="label+percent"
)])

fig2.update_layout(
    title="<b>犯罪案件與最近超商距離之空間比例分佈（環域特徵識別）</b><br><sup>解讀焦點：打破高牆長條圖！圓餅特徵直接破題 ── 有 17.5% 的犯罪（綠色區塊）被鎖在超商極近的 20m 黃金守護圈內。</sup>",
    font=GLOBAL_FONT,
    template="plotly_white",
    annotations=[dict(
        text='<b>17.5%</b><br><span style="font-size:13px; color:#48BB78;">犯罪集中在<br>20m內</span>', 
        x=0.5, y=0.5, 
        font=dict(family="Microsoft JhengHei", size=18, color="#48BB78"), 
        showarrow=False
    )],
    height=500,
    showlegend=True,
    legend=dict(
        orientation="v", 
        yanchor="middle", 
        y=0.5, 
        xanchor="right", 
        x=-0.1
    ),
    margin=dict(t=100, b=50, l=150, r=40)
)

# ==============================================================================
# 5. 圖表三：空間因果比例 
# ==============================================================================
print("正在繪製圖表三：二分法守護圈與盲區比例圖...")

def classify_blind_spot(row):
    if row["距離分組"] == "0-20m":
        return "超商20m防護圈內 (安全島)"
    else:
        return "超商20m防護圈外 (安全盲區)"

df_distance_group["盲區分類視覺化"] = df_distance_group.apply(classify_blind_spot, axis=1)
df_pie_data = df_distance_group.groupby("盲區分類視覺化")["件數"].sum().reset_index()

color_link = {
    "超商20m防護圈內 (安全島)": "#76ABAE",    
    "超商20m防護圈外 (安全盲區)": "#DE5454"   
}
colors = [color_link[label] for label in df_pie_data["盲區分類視覺化"]]

fig3 = go.Figure(data=[go.Pie(
    labels=df_pie_data["盲區分類視覺化"],
    values=df_pie_data["件數"],
    hole=0.62,
    marker=dict(colors=colors, line=dict(color='#ffffff', width=3)),
    textinfo='label+percent',
    insidetextorientation='horizontal',
    hovertemplate="空間定義: %{label}<br>案件數量: %{value} 件<br>比例: %{percent}<extra></extra>"
)])

fig3.update_layout(
    title="<b>全北市犯罪案件與超商守望範圍之空間因果比例（總體特徵）</b><br><sup>解讀焦點：嚴格定義 20m 範圍下，17.5% 落在安全島（綠色），而高達 82.5% 在安全盲區（紅色）。</sup>",
    font=GLOBAL_FONT,
    template="plotly_white",
    annotations=[dict(
        text='<b>82.5%</b><br><span style="font-size:14px; color:#DE5454;">落在<br>安全盲區</span>', 
        x=0.5, y=0.5, 
        font=dict(family="Microsoft JhengHei", size=18, color="#DE5454"), 
        showarrow=False
    )],
    height=500,
    showlegend=False,
    margin=dict(t=100, b=50, l=40, r=40)
)


# ==============================================================================
# 6. 圖表四：核心政策發現（四象限氣泡風險矩陣 - 動態校準升級版）
# ==============================================================================
print("正在繪製圖表四：四象限氣泡風險矩陣（動態十字平均線與座標範圍版）...")

def calc_blind_ratio(df_raw_sub, df_summary_sub):
    blind = (
        df_raw_sub.groupby("行政區")
        .apply(lambda x: (x["是否在20公尺內"] == "否").sum() / len(x) * 100)
        .reset_index()
    )
    blind.columns = ["行政區", "盲區比例"]
    merged = df_summary_sub.merge(blind, on="行政區")
    merged = merged.rename(columns={"件數": "件數", "平均最近距離_公尺": "平均最近距離"})
    return merged

# 準備三個視角的 DataFrame
df_total = df_district_summary.groupby("行政區").agg(總件數=("件數", "sum"), 平均最近距離=("平均最近距離_公尺", "mean")).reset_index()
blind_total = df_crime_total.groupby("行政區").apply(lambda x: (x["是否在20公尺內"] == "否").sum() / len(x) * 100).reset_index()
blind_total.columns = ["行政區", "盲區比例"]
df_total = df_total.merge(blind_total, on="行政區").rename(columns={"總件數": "件數"})

df_house = calc_blind_ratio(df_crime_total[df_crime_total["案類"] == "住宅竊盜"], df_district_summary[df_district_summary["案類"] == "住宅竊盜"])
df_moto = calc_blind_ratio(df_crime_total[df_crime_total["案類"] == "機車竊盜"], df_district_summary[df_district_summary["案類"] == "機車竊盜"])

# 動態取得每個資料集的 X 與 Y 軸最完美顯示範圍 (留一點邊界)
def get_axis_range(df):
    max_x = df["件數"].max()
    max_y = df["平均最近距離"].max()
    return [-max_x * 0.08, max_x * 1.15], [-max_y * 0.08, max_y * 1.15]

range_total_x, range_total_y = get_axis_range(df_total)
range_house_x, range_house_y = get_axis_range(df_house)
range_moto_x,  range_moto_y  = get_axis_range(df_moto)

# 建立動態更新象限背景色與十字線的函數
def create_shapes_and_lines(mean_x, mean_y):
    return [
        # 左上：深夜真空帶
        dict(type="rect", x0=-1000, y0=mean_y, x1=mean_x, y1=2000, fillcolor="rgba(155, 100, 180, 0.12)", line_width=0, layer="below"),
        # 右下：都市吸引島
        dict(type="rect", x0=mean_x, y0=-1000, x1=5000, y1=mean_y, fillcolor="rgba(56, 189, 219, 0.12)", line_width=0, layer="below"),
        # 右上：雙重風險區
        dict(type="rect", x0=mean_x, y0=mean_y, x1=5000, y1=2000, fillcolor="rgba(255, 160, 80, 0.09)", line_width=0, layer="below"),
        # 左下：相對安全區
        dict(type="rect", x0=-1000, y0=-1000, x1=mean_x, y1=mean_y, fillcolor="rgba(80, 200, 140, 0.09)", line_width=0, layer="below"),
        # 十字分隔線
        dict(type="line", x0=mean_x, x1=mean_x, y0=-1000, y1=2000, line_width=1.5, line_dash="dash", line_color="#7A8FCC"),
        dict(type="line", x0=-1000, x1=5000, y0=mean_y, y1=mean_y, line_width=1.5, line_dash="dash", line_color="#7A8FCC"),
    ]

fig4 = go.Figure()

# ── 氣泡繪製函式 ──────────────────────────────────────────
def add_bubble_trace(df, name, visible):
    blind_vals = df["盲區比例"].values
    raw_size = blind_vals + 6
    sizeref   = 2.0 * max(raw_size) / (45.0 ** 2)
    hover_text = [
        f"<b>{row['行政區']}</b><br>犯罪件數：{int(row['件數'])} 件<br>平均距離：{row['平均最近距離']:.1f} 公尺<br><b>盲區比例：{row['盲區比例']:.1f}%</b>"
        for _, row in df.iterrows()
    ]
    return go.Scatter(
        x=df["件數"], y=df["平均最近距離"], mode="markers+text",
        text=df["行政區"], textposition="top center", name=name,
        marker=dict(
            size=raw_size, sizemode="area", sizeref=sizeref, color=blind_vals,
            colorscale=[[0.0, "#AEE2FF"], [0.4, "#7B9EFF"], [0.7, "#9B50C8"], [1.0, "#5A0080"]],
            cmin=75, cmax=95, showscale=True, opacity=0.85, line=dict(width=1.5, color="white"),
            colorbar=dict(title=dict(text="盲區比例 (%)", font=dict(family="Microsoft JhengHei", size=12)), thickness=14, len=0.6, x=1.02)
        ),
        textfont=dict(family="Microsoft JhengHei", color="#1a202c", size=12),
        visible=visible, hovertemplate="%{customdata}<extra></extra>", customdata=hover_text,
    )

# 依序加入三個 Trace
fig4.add_trace(add_bubble_trace(df_total, "總體案件", True))
fig4.add_trace(add_bubble_trace(df_house, "住宅竊盜", False))
fig4.add_trace(add_bubble_trace(df_moto,  "機車竊盜", False))

# ── 相對座標象限標籤（不受 X/Y 軸縮放影響）─────────────────────────────
story_annotations = [
    dict(x=0.01, y=0.99, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False, text="<b>深夜真空帶</b><br><span style='font-size:10px; color:#9333EA;'>低件數・高距離・高盲區</span>", font=dict(family="Microsoft JhengHei", size=13, color="#6B21A8"), align="left"),
    dict(x=0.99, y=0.01, xref="paper", yref="paper", xanchor="right", yanchor="bottom", showarrow=False, text="<b>都市吸引島</b><br><span style='font-size:10px; color:#0284C7;'>高件數・低距離・低盲區</span>", font=dict(family="Microsoft JhengHei", size=13, color="#0369A1"), align="right"),
    dict(x=0.99, y=0.99, xref="paper", yref="paper", xanchor="right", yanchor="top", showarrow=False, text="<b>雙重風險區</b>", font=dict(family="Microsoft JhengHei", size=11, color="#92400E"), align="right"),
    dict(x=0.01, y=0.01, xref="paper", yref="paper", xanchor="left", yanchor="bottom", showarrow=False, text="<b>相對安全區</b>", font=dict(family="Microsoft JhengHei", size=11, color="#065F46"), align="left"),
    dict(x=0.5, y=-0.25, xref="paper", yref="paper", xanchor="center", yanchor="top", showarrow=False, text="<i>泡泡大小 = 盲區比例（超商20m外案件佔比）；顏色越深紫代表防禦缺口越嚴重</i>", font=dict(family="Microsoft JhengHei", size=11, color="#718096"), align="center"),
]

# ── 動態更新選單按鈕 ──────────────────────────────────────────
fig4.update_layout(
    updatemenus=[dict(
        type="buttons", direction="right", active=0, x=0.5, xanchor="center", y=-0.13, yanchor="top",
        buttons=[
            dict(label="  總體案件  ", method="update", args=[
                {"visible": [True, False, False]},
                {"shapes": create_shapes_and_lines(df_total["件數"].mean(), df_total["平均最近距離"].mean()),
                 "xaxis.range": range_total_x, "yaxis.range": range_total_y}
            ]),
            dict(label="  住宅竊盜  ", method="update", args=[
                {"visible": [False, True, False]},
                {"shapes": create_shapes_and_lines(df_house["件數"].mean(), df_house["平均最近距離"].mean()),
                 "xaxis.range": range_house_x, "yaxis.range": range_house_y}
            ]),
            dict(label="  機車竊盜  ", method="update", args=[
                {"visible": [False, False, True]},
                {"shapes": create_shapes_and_lines(df_moto["件數"].mean(), df_moto["平均最近距離"].mean()),
                 "xaxis.range": range_moto_x, "yaxis.range": range_moto_y}
            ]),
        ],
        font=dict(family="Microsoft JhengHei", size=13), bgcolor="#EEF2FF", bordercolor="#6366F1", borderwidth=1.5, pad=dict(l=10, r=10, t=6, b=6)
    )],
    title=dict(text="<b>台北市行政區犯罪風險矩陣</b><br><sup>X軸=案件熱度・Y軸=超商距離（環境防禦力）・泡泡大小與顏色=盲區嚴重度</sup>", font=TITLE_FONT, x=0.5),
    xaxis=dict(title="<b>犯罪總件數（案件熱度）</b>", gridcolor="#E2E8F0", range=range_total_x, tickfont=dict(family="Microsoft JhengHei")),
    yaxis=dict(title="<b>離超商平均距離（公尺 / 環境防禦力）</b>", gridcolor="#E2E8F0", range=range_total_y, tickfont=dict(family="Microsoft JhengHei")),
    shapes=create_shapes_and_lines(df_total["件數"].mean(), df_total["平均最近距離"].mean()),
    annotations=story_annotations,
    width=1050, height=680, margin=dict(t=110, b=170, l=65, r=100),
    paper_bgcolor="white", plot_bgcolor="#FAFBFF", showlegend=False,
)

# ==============================================================================
# 7. 輸出為網頁 HTML 檔案與報告文字整合
# ==============================================================================
html_output_path = "台北犯罪與超商距離分析報告.html"
print(f"正在將四個完整圖表與期末報告結論寫法整合輸出至：{html_output_path}...")

div_fig1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')
div_fig2 = fig2.to_html(full_html=False, include_plotlyjs=False)
div_fig3 = fig3.to_html(full_html=False, include_plotlyjs=False)
div_fig4 = fig4.to_html(full_html=False, include_plotlyjs=False)

html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>台北市犯罪空間點位與便利商店距離關係分析</title>
    <style>
        body {{ font-family: 'Microsoft JhengHei', sans-serif; background-color: #f7fafc; color: #2d3748; margin: 0; padding: 40px 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
        h1 {{ text-align: center; color: #1a365d; margin-bottom: 10px; }}
        .subtitle {{ text-align: center; color: #718096; font-size: 16px; margin-bottom: 40px; }}
        .chart-section {{ margin-bottom: 50px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff; }}
        .insight-box, .insight-box-danger {{ background-color: #f0f7f7; border-left: 5px solid #76ABAE; padding: 20px; margin-top: 20px; border-radius: 0 8px 8px 0; }}
        .insight-box-danger {{ background-color: #fff5f5; border-left: 5px solid #DE5454; }}
        ul {{ padding-left: 20px; line-height: 1.8; }}
        li {{ margin-bottom: 10px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>台北市犯罪空間點位與便利商店距離關係</h1>
    <div class="subtitle">視覺化數據儀表板</div>

    <div class="chart-section">
        {div_fig1}
        <div class="insight-box">
            <h3 style="margin: 0 0 10px 0; color: #4B777A; font-size: 18px;">行政區犯罪總量對比</h3>
            <p style="margin: 0; line-height: 1.6; color: #4A4466; font-size: 14.5px;">
                堆疊長條圖顯示，<b>中山區、士林區、萬華區</b>在犯罪總量上名列前茅。然而，單看總量容易產生傳統政策決策的「總量盲點」，必須進一步解構空間距離。
            </p>
        </div>
    </div>

    <div class="chart-section">
        {div_fig2}
        <div class="insight-box">
            <h3 style="margin: 0 0 10px 0; color: #4B777A; font-size: 18px;">環域特徵識別（細分數據）</h3>
            <p style="margin: 0; line-height: 1.6; color: #4A4466; font-size: 14.5px;">
                細分環域數據顯示，台北市高達 <b>17.5%</b> 的竊盜案發生在超商極近距離的 0-20 公尺內，建構了核心的 <b>17.5% 集中區</b>，突顯出研究超商防衛空間的急迫性。
            </p>
        </div>
    </div>

    <div class="chart-section">
        {div_fig3}
        <div class="insight-box">
            <h3 style="margin: 0 0 10px 0; color: #4B777A; font-size: 18px;">總體空間因果關係（二分法守護圈）</h3>
            <p style="margin: 0; line-height: 1.6; color: #4A4466; font-size: 14.5px;">
                <b>比例修正優化發現：</b> 將環域數據整合為嚴格的 20m 二分法後，可以強烈對比出<b>安全島（17.5%）</b>與<b>安全盲區（82.5%）</b>的差距。限縮在超商門口 20m 的極短距離下，超商發揮了點狀的防護與嚇阻作用，但也暴露出離開這個極限距離後防禦力驟降的現象。
            </p>
        </div>
    </div>

    <div class="chart-section">
        {div_fig4}
        <div class="insight-box-danger">
            <h3 style="margin: 0 0 10px 0; color: #9b2c2c; font-size: 18px;">核心政策發現 【深夜真空帶】 vs 【都市吸引島】</h3>
            <p style="margin: 0; line-height: 1.6; color: #4A4466; font-size: 14.5px;">
                💡 <b>互動提示：</b>您可以使用圖表下方的橫向單選按鈕，即時切換檢視「總體案件」、「住宅竊盜」與「機車竊盜」的個別象限風險矩陣分佈。<br><br>
                <b>1. 【環境防禦真空區域】 ── 文山區、中正區（低件數、高盲區）：</b><br>
                文山與中正區在長條圖中雖是治安前段班，但四象限圖揭開了隱藏現實：<b>只要一發生犯罪，這兩區有極高比例是狠狠落在 20m 範圍外的黑暗死角！</b> 這裡缺乏超商的極近距離監視，是都市防禦的「深夜真空帶」，也是社會安全網最需硬體補強的政策核心。<br><br>
                <b>2. 【犯罪時空聚合熱點】 ── 中山區、大安區、萬華區（高件數、低盲區）：</b><br>
                超商極度密集，民間便利商店網絡已經在此布下密不透風的實體防禦節點。這裡高居不下的犯罪率並非缺乏照明，而是因為高度商業化、繁華人流吸引犯罪者前來。政策上在此處應該加強的是「警力巡邏」，而非盲目加裝靜態硬體設施。
            </p>
        </div>
    </div>

    <div class="insight-box" style="margin-top: 40px;">
        <h3 style="color: #4B777A; margin-top: 0; font-size: 18px;">數據如何支持你的研究目標？（結論寫法建議）</h3>
        <ul style="color: #4A4466; font-size: 14.5px;">
            <li><b>目標一：超商充當深夜安全守護點</b><br>在嚴格限縮 20m 距離後，我們能精準定位超商的絕對影響範圍。離開 20m 範圍即失去保護，表示「提升超商周邊巡邏頻率」與「落實超商夜間亮點計畫」才能有效延伸這 20m 的實體防衛力。</li>
            <li><b>目標二：打破總量迷思，翻轉政策資源配置</b><br>強烈建議在期末報告結論中指出：治安政策不應只補助「犯罪件數多」的地區（都市吸引島），而應優先在文山區、中正區等「深夜真空帶」加裝公家監視器或提升夜間路燈密度，以填補民間超商 20m 以外無法覆蓋的黑暗死角。</li>
        </ul>
    </div>
</div>
</body>
</html>
"""

with open(html_output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("\n" + "="*50)
print(f" 四象限背景大面積填色完成！按鈕已成功移至圖表下方！")
print(f" 網頁檔案儲存路徑：{os.path.abspath(html_output_path)}")
print("="*50)