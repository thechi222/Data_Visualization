# ==========================================
# 步驟三：進階靜態統計圖表繪製與互動式網頁地圖生成
# ==========================================

# 1. 檢查並自動載入所需套件
if (!require(tidyverse)) install.packages("tidyverse")
if (!require(ggplot2)) install.packages("ggplot2")
if (!require(showtext)) install.packages("showtext")  
if (!require(leaflet)) install.packages("leaflet")
if (!require(leaflet.extras)) install.packages("leaflet.extras")
if (!require(stringr)) install.packages("stringr")
if (!require(ggridges)) install.packages("ggridges")

library(tidyverse)
library(ggplot2)
library(showtext)
library(leaflet)
library(leaflet.extras)
library(sf)
library(stringr)
library(ggridges)

# 啟動 showtext 自動字體對應
showtext_auto()
showtext_opts(dpi = 300)

# 確保環境中有前一步驟的資料
if (!exists("sf_crime_3826") | !exists("sf_stores_3826")) {
  stop("找不到空間資料，請確認是否已依序執行資料轉換與資料呈現檔案！")
}

# 基礎資料清理：過濾 NA 並脫離幾何圖形以加速渲染
sf_crime_filter  <- sf_crime_3826 %>% filter(!is.na(行政區))
sf_stores_filter <- sf_stores_3826 %>% filter(!is.na(行政區))
df_crime_plot <- sf_crime_filter %>% st_drop_geometry()

cat("\n正在生成套用 Color Hunt 配色的 ggplot2 進階靜態圖表...\n")

# ==========================================
# 圖表一：各行政區犯罪案類對比（分組長條圖）
# ==========================================
crime_bar_data <- df_crime_plot %>%
  group_by(行政區, 案類) %>%
  summarise(件數 = n(), .groups = 'drop')

plot_bar <- ggplot(crime_bar_data, aes(x = reorder(行政區, -件數, FUN = sum), y = 件數, fill = 案類)) +
  geom_bar(stat = "identity", position = "dodge", width = 0.7, color = "white") +
  geom_text(aes(label = 件數), position = position_dodge(width = 0.7), vjust = -0.5, size = 3) +
  scale_fill_manual(values = c("住宅竊盜" = "#CCD67F", "機車竊盜" = "#F0E76F")) +
  labs(
    title = "台北市各行政區【住宅竊盜 vs 機車竊盜】件數對比圖",
    subtitle = "資料來源：台北市犯罪與超商距離分析小組",
    x = "行政區 (依總犯罪件數降序排列)", y = "犯罪件數 (件)", fill = "犯罪案類"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5, color = "gray30"),
    axis.text.x = element_text(angle = 45, hjust = 1),
    panel.grid.major.x = element_blank(), legend.position = "top"
  )
print(plot_bar)


# ==========================================
# 圖表二：各區總犯罪量與平均距離（專業雙指標玫瑰圖）
# ==========================================
crime_rose_data <- df_crime_plot %>%
  group_by(行政區) %>%
  summarise(
    總計 = n(), mean_dist = mean(最近超商距離_公尺, na.rm = TRUE), .groups = 'drop'
  ) %>%
  mutate(
    max_total = max(總計), radius_rose = sqrt(總計 / max_total) * 50,
    max_dist = max(mean_dist), dist_radius = sqrt(mean_dist / max_dist) * 50
  )

plot_rose <- ggplot(crime_rose_data) + 
  geom_hline(yintercept = c(0, 12.5, 25, 37.5, 50), color = "lightgrey", linetype = "dashed", alpha = 0.5) +
  geom_col(aes(x = reorder(str_wrap(行政區, 5), 總計), y = radius_rose, fill = 總計), position = "dodge2", alpha = 0.95) +
  coord_polar() +
  geom_segment(aes(x = reorder(str_wrap(行政區, 5), 總計), y = 0, xend = reorder(str_wrap(行政區, 5), 總計), yend = dist_radius), linetype = "dashed", color = "gray12") +
  scale_y_continuous(limits = c(-5, 55), expand = c(0, 0), breaks = c(0, 12.5, 25, 37.5, 50), labels = c("0%", "25%", "50%", "75%", "100%")) + 
  scale_fill_gradientn("總犯罪件數", colours = c("#5B7D3C", "#F2C84B", "#F9A247")) +
  guides(fill = guide_colorsteps(barwidth = 15, barheight = .5, title.position = "top", title.hjust = .5)) + 
  labs(
    title = "台北市各行政區【犯罪量 vs 平均超商距離】玫瑰圖",
    subtitle = "柱狀體積代表總件數；內部虛線長度代表平均距離"
  ) +
  theme_minimal() +
  theme(
    axis.title = element_blank(), axis.ticks = element_blank(),
    axis.text.y = element_text(size = 8), axis.text.x = element_text(color = "gray12", size = 12),
    legend.position = "bottom", plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5, color = "gray30", margin = margin(b = 10))
  )
print(plot_rose)


# ==========================================
# 圖表三：各行政區犯罪距離分佈（脊線圖 Ridgeline Plot）
# ==========================================
plot_ridge <- ggplot(df_crime_plot, aes(x = 最近超商距離_公尺, y = reorder(行政區, -最近超商距離_公尺, FUN = median), fill = stat(x))) +
  geom_density_ridges_gradient(scale = 2, rel_min_height = 0.01, color = "white", alpha = 0.85) +
  scale_fill_gradientn(name = "超商距離 (m)", colours = c("#9FA1FC", "#B2CBFE", "#D9F8DF")) +
  coord_cartesian(xlim = c(0, 500)) + 
  labs(
    title = "台北市各行政區【犯罪距離超商】分佈脊線圖",
    subtitle = "山峰越高代表該距離犯罪越密集；過濾顯示 500 公尺內",
    x = "最近超商距離 (公尺)", y = "行政區 (依中位數距離排序)"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5, color = "gray30", margin = margin(b = 15)),
    axis.text.y = element_text(face = "bold", size = 11), legend.position = "right"
  )
print(plot_ridge)


# ==========================================
# 圖表四：24小時犯罪時段趨勢圖

# ==========================================
time_trend_data <- df_crime_plot %>%
  filter(!is.na(發生時段) & !is.na(案類)) %>%
  group_by(發生時段, 案類) %>%
  summarise(件數 = n(), .groups = 'drop')

# 確保 X 軸時段按照 00 到 24 排序
time_levels <- sort(unique(time_trend_data$發生時段))
time_trend_data$發生時段 <- factor(time_trend_data$發生時段, levels = time_levels)

plot_time_trend <- ggplot(time_trend_data, aes(x = 發生時段, y = 件數, color = 案類, fill = 案類, group = 案類)) +
  # 半透明面積底色
  geom_area(alpha = 0.35, position = "identity") +
  # 繪製粗趨勢線
  geom_line(size = 1.2) +
  # 加上資料點圓圈
  geom_point(size = 3, shape = 21, fill = "white", stroke = 1.2) +
  # 搭配你先前選擇的大地色系，線條用深色、面積用淺色
  scale_color_manual(values = c("住宅竊盜" = "#5B7D3C", "機車竊盜" = "#F9A247")) +
  scale_fill_manual(values = c("住宅竊盜" = "#CCD67F", "機車竊盜" = "#F2C84B")) +
  labs(
    title = "台北市 24 小時犯罪時段趨勢對比",
    subtitle = "住宅竊盜與機車竊盜的高風險發生時段分佈",
    x = "發生時段", y = "犯罪總件數 (件)", color = "犯罪案類", fill = "犯罪案類"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5, color = "gray30", margin = margin(b = 15)),
    axis.text.x = element_text(angle = 45, hjust = 1, face = "bold"),
    axis.text.y = element_text(face = "bold"),
    panel.grid.minor = element_blank(),
    legend.position = "top"
  )
print(plot_time_trend)


# ==========================================
# 自動儲存所有高清圖表
# ==========================================
ggsave("03_各區案類對比_長條圖.png", plot = plot_bar, width = 10, height = 6, dpi = 300, device = "png", bg = "white")
ggsave("04_各區總量分佈_玫瑰圖.png", plot = plot_rose, width = 9, height = 9, dpi = 300, device = "png", bg = "white")
ggsave("05_各區距離分佈_脊線圖.png", plot = plot_ridge, width = 10, height = 7, dpi = 300, device = "png", bg = "white")
# 儲存新的趨勢圖 (檔名也順便更新了)
ggsave("06_24小時犯罪趨勢_面積圖.png", plot = plot_time_trend, width = 10, height = 6, dpi = 300, device = "png", bg = "white")


# ==========================================
# Part 2. 空間環域分析與 Leaflet 互動式地圖
# ==========================================
cat("\n正在進行空間環域分析並生成 Leaflet 網頁地圖...\n")

sf_stores_filter$buffer_200m <- st_buffer(sf_stores_filter$geometry, dist = 200)

sf_buffers_wgs84 <- sf_stores_filter %>% 
  st_set_geometry("buffer_200m") %>% 
  st_transform(crs = 4326)

sf_crime_map <- st_transform(sf_crime_filter, crs = 4326)

crime_coords <- st_coordinates(sf_crime_map)
crime_lng <- crime_coords[, 1]
crime_lat <- crime_coords[, 2]

map_output <- leaflet() %>%
  addTiles(group = "OpenStreetMap") %>%
  addPolygons(
    data = head(sf_buffers_wgs84, 500),
    color = "#CCD67F", weight = 1, fillOpacity = 0.15, group = "超商 200m 環域範圍"
  ) %>%
  addHeatmap(
    lng = crime_lng, lat = crime_lat, radius = 12, blur = 18, minOpacity = 0.4, group = "犯罪熱力圖"
  ) %>%
  addCircleMarkers(
    data = sf_crime_map[sample(1:nrow(sf_crime_map), 150), ],
    radius = 3.5, color = "#A77F60", fillOpacity = 0.8,
    popup = ~paste0("<b>行政區:</b> ", 行政區, "<br>",
                    "<b>案類:</b> ", 案類, "<br>",
                    "<b>最近超商距離:</b> ", round(最近超商距離_公尺, 1), " 公尺"),
    group = "犯罪事件抽樣點"
  ) %>%
  addLayersControl(
    overlayGroups = c("犯罪熱力圖", "超商 200m 環域範圍", "犯罪事件抽樣點"),
    options = layersControlOptions(collapsed = FALSE)
  )

print(map_output)

cat("\n【完成】\n 長條/玫瑰/脊線/24小時趨勢面積圖 \n2. 互動地圖已生成於 Viewer 視窗。\n")