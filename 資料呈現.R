# ==========================================
# 步驟二：清理後資料結構檢視與統計摘要呈現
# ==========================================

# 確保環境中有前一步驟的資料
if (!exists("sf_crime_3826") | !exists("sf_stores_3826")) {
  stop("找不到清理後的空間資料，請先完整執行 01_data_cleaning.R 檔案！")
}

# 1. 檢視空間資料的欄位結構與前兩筆資料
cat("\n--- 1. 犯罪空間資料欄位與結構 (前兩筆) ---\n")
print(head(sf_crime_3826, 2))

cat("\n--- 2. 超商空間資料欄位與結構 (前兩筆) ---\n")
print(head(sf_stores_3826, 2))

# 2. 表格呈現：統計各行政區、不同案類的犯罪件數
crime_summary <- sf_crime_3826 %>%
  st_drop_geometry() %>%  # 暫時脫離幾何，轉回一般純文字表格計算速度較快
  group_by(行政區, 案類) %>%
  summarise(件數 = n(), .groups = 'drop') %>%
  pivot_wider(names_from = 案類, values_from = 件數, values_fill = 0)

cat("\n--- 3. 各行政區【住宅竊盜 vs 机车窃盗】件數統計摘要 ---\n")
print(crime_summary)

# 3. 表格呈現：統計各行政區的超商總數
store_summary <- sf_stores_3826 %>%
  st_drop_geometry() %>%
  group_by(行政區) %>%
  summarise(超商總數 = n(), .groups = 'drop')

cat("\n--- 4. 各行政區【超商總量】統計摘要 ---\n")
print(store_summary)