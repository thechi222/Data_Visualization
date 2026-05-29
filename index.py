import os
import subprocess
import sys

# ==============================================================================
# 0. 自動檢查並安裝缺少套件的防呆機制 (已修正 NameError 錯誤)
# ==============================================================================
required_packages = {
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "geopandas": "geopandas",
    "folium": "folium",
    "shapely": "shapely",
}

for ioc_name, pip_name in required_packages.items():
    try:
        __import__(ioc_name)
    except ImportError:
        print(f"偵測到未安裝套件 {pip_name}，正在自動為您安裝...")
        # 修正處：將 pip 加上引號轉為字串
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pip_name]
        )

# 成功導入所有必要套件
import folium
from folium.plugins import MarkerCluster
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# ==============================================================================
# 1. 設定檔案路徑與讀取資料
# ==============================================================================
excel_path = "C:/Users/etien/OneDrive/桌面/視覺化期末/台北犯罪與超商距離分析_20m.xlsx"

if not os.path.exists(excel_path):
    print(f"【錯誤】找不到 Excel 檔案，請檢查路徑是否正確：\n{excel_path}")
    sys.exit()

print("正在讀取 Excel 資料中，請稍候...")
df_crime = pd.read_excel(excel_path, sheet_name="犯罪總表_最近超商距離")
df_stores = pd.read_excel(excel_path, sheet_name="台北超商點位")

# 剔除經緯度或行政區有缺失的無效資料
df_crime = df_crime.dropna(subset=["估算緯度", "估算經度", "行政區"])
df_stores = df_stores.dropna(subset=["latitude", "longitude", "行政區"])

# ==============================================================================
# 2. 初始化 Folium 互動地圖 (採用最適合深夜盲區主題的黑暗底圖)
# ==============================================================================
print("正在繪製互動式地圖...")
taipei_center = [25.05, 121.54]  # 台北市中心點

m = folium.Map(
    location=taipei_center,
    zoom_start=13,
    tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    name="深夜黑暗模式 (推薦)",
)

# 新增標準地圖作為備用切換圖層
folium.TileLayer("OpenStreetMap", name="標準地圖 (OpenStreetMap)").add_to(m)

# 建立圖層群組以便在網頁右上角自由切換開關
group_buffers = folium.FeatureGroup(name="超商 200m 深夜守護圈", show=True).add_to(
    m
)
group_stores = folium.FeatureGroup(name="超商實體點位", show=False).add_to(
    m
)  # 預設不勾選，畫面更乾淨

# 建立犯罪點聚類群組（替代原本密密麻麻的熱力圖，讓視覺更乾淨流暢）
cluster_housing = MarkerCluster(
    name="住宅竊盜點位",
    show=True,
    options={"showCoverageOnHover": False, "spiderfyOnMaxZoom": True},
).add_to(m)
cluster_motor = MarkerCluster(
    name="機車竊盜點位",
    show=True,
    options={"showCoverageOnHover": False, "spiderfyOnMaxZoom": True},
).add_to(m)

# ==============================================================================
# 3. 將資料渲染進地圖圖層
# ==============================================================================

# A. 優化渲染：改用 folium.Circle 繪製 200m 守護圈，大幅提升流暢度，可載入全量超商點位！
print("正在渲染 1700+ 筆超商守護圈（這可能需要幾秒鐘）...")
for _, row in df_stores.iterrows():
    # 點擊守護圈藍色區塊會跳出超商資訊
    popup_text = f"<b>超商名稱：</b>{row['超商名稱']}<br><b>地址：</b>{row['地址']}"
    popup = folium.Popup(popup_text, max_width=300)

    # 繪製半徑 200 公尺的圓形防護罩
    folium.Circle(
        location=[row["latitude"], row["longitude"]],
        radius=200,  # 單位為公尺
        color="#2980b9",
        fill=True,
        fill_color="#3498db",
        fill_opacity=0.12,
        weight=1,
        popup=popup,
    ).add_to(group_buffers)

    # 繪製超商實體點（綠色小核心）
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=2,
        color="#2ecc71",
        fill=True,
        fill_color="#2ecc71",
        fill_opacity=0.8,
    ).add_to(group_stores)

# B. 渲染全部犯罪點位並歸類至 Marker Cluster 聚類中
print("正在渲染犯罪點位與進行聚類分析...")
for _, row in df_crime.iterrows():
    popup_text = f"""
    <b>案類：</b>{row['案類']}<br>
    <b>發生時段：</b>{row['發生時段']}<br>
    <b>最近超商距離：</b>{row['最近超商距離_公尺']} 公尺
    """
    popup = folium.Popup(popup_text, max_width=300)

    if row["案類"] == "住宅竊盜":
        folium.CircleMarker(
            location=[row["估算緯度"], row["估算經度"]],
            radius=4,
            color="#e74c3c",  # 紅色點位
            fill=True,
            fill_color="#e74c3c",
            fill_opacity=0.6,
            weight=1,
            popup=popup,
        ).add_to(cluster_housing)
    elif row["案類"] == "機車竊盜":
        folium.CircleMarker(
            location=[row["估算緯度"], row["估算經度"]],
            radius=4,
            color="#f39c12",  # 橘色點位
            fill=True,
            fill_color="#f39c12",
            fill_opacity=0.6,
            weight=1,
            popup=popup,
        ).add_to(cluster_motor)

# ==============================================================================
# 4. 插入自訂網頁標題與說明控制板 (利用 HTML/CSS 刻製美化)
# ==============================================================================
title_html = """
<div style="position: fixed; top: 10px; left: 50px; width: 380px; height: auto; 
            background-color: rgba(255,255,255,0.9); padding: 15px; border-radius: 8px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.2); z-index: 9999; font-family: 'Microsoft JhengHei', sans-serif;">
    <h3 style="margin-top: 0; color: #2c3e50; font-weight: bold;">台北市深夜超商安全守護對比地圖</h3>
    <p style="font-size: 13px; color: #7f8c8d; line-height: 1.5; margin-bottom: 5px;">
        本互動地圖旨在探討超商的「社會價值轉化」。藍色圓圈代表<b>超商周圍 200 公尺守護圈</b>。
    </p>
    <p style="font-size: 13px; color: #7f8c8d; line-height: 1.5; margin-top: 0;">
        若犯罪點（紅色/橘色）落在藍圈之外，即顯現出缺乏燈火照明與監控的<b style="color:#d9534f;">「深夜安全盲區」</b>。
    </p>
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

# 右上角加入圖層控制選單開關
folium.LayerControl(collapsed=False).add_to(m)

# ==============================================================================
# 5. 輸出網頁為指定名稱 index.html
# ==============================================================================
output_filename = "index.html"
m.save(output_filename)
print("-" * 60)
print(
    f"【成功】網頁製作完成！已成功儲存為 '{output_filename}'。\n您可以直接雙擊開啟該 HTML 檔案瀏覽成果！"
)
print("-" * 60)