# -*- encoding: utf-8 -*-

import os

# 拧紧结果颜色
OK_BG_COLOR = "#C8E6C9"
OK_COLOR = "#256029"
NOK_BG_COLOR = "#FFCDD2"
NOK_COLOR = "#C63737"
OTHER_BG_COLOR = "#D3D1D1"

# 下载结果文件类型
CSV_TYPE = "csv"
EXCEL_TYPE = "excel"

DOWNLOAD_RESULT_ONLY = "result"
DOWNLOAD_ALL = "result,curve"

ENV_DOWNLOAD_TIGHTENING_RESULT_ENCODE = os.getenv(
    "ENV_DOWNLOAD_TIGHTENING_RESULT_ENCODE", "utf-8"
)

ENV_DOWNLOAD_TIGHTENING_RESULT_LIMIT = int(
    os.getenv("ENV_DOWNLOAD_TIGHTENING_RESULT_LIMIT", "1000")
)

CURVE_KEYS_V1 = ["cur_m", "cur_w", "cur_t"]
CURVE_KEYS_V2 = ["torque", "angle", "time"]
