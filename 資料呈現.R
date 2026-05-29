# ==========================================
# 步驟二：清理後資料結構檢視與文字統計摘要呈現
# ==========================================

library(tidyverse)
library(sf)

# 確保環境中有前一步驟的資料
if (!exists("sf_crime_3826") | !exists("sf_stores_3826")) {
  stop("找不到清理後的空間資料，請先完整執行 01_data_cleaning.R (資料轉換.R) 檔案！")
}

# ==========================================
# 1. 資料進階清理與結構檢視
# ==========================================

cat("\n--- 1. 犯罪空間資料欄位與結構 (前兩筆) ---\n")
print(head(sf_crime_3826, 2))

cat("\n--- 2. 超商空間資料欄位與結構 (前兩筆) ---\n")
print(head(sf_stores_3826, 2))

# 【核心修正】排除行政區為 NA 的無效資料，確保統計基底百分之百準確
sf_crime_clean_dist  <- sf_crime_3826 %>% filter(!is.na(行政區))
sf_stores_clean_dist <- sf_stores_3826 %>% filter(!is.na(行政區))


# ==========================================
# 2. 文字統計摘要表格呈現
# ==========================================

# 表格 A：統計各行政區、不同案類的犯罪件數 (依總件數由高到低排序)
crime_summary <- sf_crime_clean_dist %>%
  st_drop_geometry() %>%  # 暫時脫離幾何，轉回一般純文字表格計算速度較快
  group_by(行政區, 案類) %>%
  summarise(件數 = n(), .groups = 'drop') %>%
  pivot_wider(names_from = 案類, values_from = 件數, values_fill = 0) %>%
  mutate(總計 = 住宅竊盜 + 機車竊盜) %>% 
  arrange(desc(總計))

cat("\n--- 3. 各行政區【住宅竊盜 vs 機車竊盜】件數統計摘要 (已排除未知行政區) ---\n")
print(crime_summary)

# 表格 B：統計各行政區的超商總數 (依總數由高到低排序，已修正 932 筆 NA 漏洞)
store_summary <- sf_stores_clean_dist %>%
  st_drop_geometry() %>%
  group_by(行政區) %>%
  summarise(超商總數 = n(), .groups = 'drop') %>% 
  arrange(desc(超商總數))

cat("\n--- 4. 各行政區【超商總量】統計摘要 (已排除未知行政區) ---\n")
print(store_summary)

cat("\n【工作完成】文字統計摘要已成功輸出！接下來請執行「圖表.R」繪製視覺化圖表。\n")