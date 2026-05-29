# 確保有安裝並載入 readxl
if (!require(readxl)) install.packages("readxl")
library(readxl)
library(tidyverse)
library(sf)
setwd("C:/Users/etien/OneDrive/桌面/視覺化期末")
# 1. 直接讀取 Excel 檔案中對應的工作表 (Sheets)
df_crime <- read_excel("台北犯罪與超商距離分析.xlsx", sheet = "犯罪總表_最近超商距離")
df_stores <- read_excel("台北犯罪與超商距離分析.xlsx", sheet = "台北超商點位")

# 2. 資料清理：移除經緯度為空值 (NA) 的資料
df_crime_clean <- df_crime %>% filter(!is.na(估算緯度) & !is.na(估算經度))
df_stores_clean <- df_stores %>% filter(!is.na(latitude) & !is.na(longitude))

# 3. 將資料轉換為地理空間物件 (sf object)
# 原始經緯度為 WGS84 系統，對應的 EPSG 代碼為 4326
sf_crime_wgs84 <- st_as_sf(df_crime_clean, coords = c("估算經度", "估算緯度"), crs = 4326)
sf_stores_wgs84 <- st_as_sf(df_stores_clean, coords = c("longitude", "latitude"), crs = 4326)

# 4. 投影轉換至 TWD97 (EPSG:3826)，以便後續以「公尺」為單位進行 Buffer 空間計算
sf_crime_3826 <- st_transform(sf_crime_wgs84, crs = 3826)
sf_stores_3826 <- st_transform(sf_stores_wgs84, crs = 3826)

cat("【第一步】Excel 資料清理與 TWD97 座標轉換完成！\n")