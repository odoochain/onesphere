# -*- encoding: utf-8 -*-

# 拧紧类型
import os

TIGHTENING_TEST_TYPE = "tightening"
PROM_TIGHTENING_TEST_TYPE = "promiscuous_tightening"

ALL_TIGHTENING_TEST_TYPE_LIST = [TIGHTENING_TEST_TYPE, PROM_TIGHTENING_TEST_TYPE]

# 测量类型
MEASURE_TYPE = "measure"
MULTI_MEASURE_TYPE = "multi_measure"
PASS_FAIL_TYPE = "pass_fail"

ALL_MEASURE_TYPE_LIST = [MEASURE_TYPE, MULTI_MEASURE_TYPE, PASS_FAIL_TYPE]

# 拧紧工具类型集合
ASSEMBLY_TOOLS_TECH_NAME = [
    "tightening_nut_runner",
    "tightening_wrench",
    "tightening_spindle",
]

# endpoint
MASTER_ROUTING_API = "/rush/v1/mrp.routing.workcenter"

# 导入文件类型
EXCEL_TYPE = ["xlsx", "xls"]
IMG_TYPE = ["jpg", "png", "jpeg"]

ASSEMBLY_CONTROLLERS = [
    ("ModelDesoutterCvi3", "CVI3"),
    ("ModelDesoutterCvi2R", "CVI2-R"),
    ("ModelDesoutterCvi2L", "CVI2-L"),
    ("ModelDesoutterCvi3Twin", "TWIN-CVI3"),
    ("ModelDesoutterConnector", "CVI-CONNECTOR"),
    ("ModelAtlasPF4000", "PF4000"),
    ("ModelAtlasPF6000", "PF6000"),
]
# 工作模式字典
WORK_MODE_DIC = {"normal": "工作模式", "rework": "返工模式", "manual": "手动模式", "trial": "试制模式"}

# 默认螺栓编号拼接规则
DEFAULT_BOLT_NAME_RULES = "${controller_name}_${job}_${batch_count}_${pset}"

ENV_PROCESS_PROPOSAL_DURATION = int(
    os.getenv("ENV_PROCESS_PROPOSAL_DURATION", "30")
)  # 默认拿过去三十天的数据进行工艺建议
ENV_PROCESS_PROPOSAL_ANGLE_MARGIN = int(
    os.getenv("ENV_PROCESS_PROPOSAL_ANGLE_MARGIN", "3")
)  # 默认拿过去三十天的数据进行工艺建议

# 默认曲线id拼接规则
DEFAULT_ENTITY_ID_RULES = "${track_no}_${tool_sn}_${workcenter_code}_${tightening_id}"

# 当前文件夹路径
CURRENT_PATH = os.path.dirname(__file__)

# 默认拧紧结果保留天数
TIGHTENING_RESULT_RETENTION_DAYS = int(
    os.getenv("TIGHTENING_RESULT_RETENTION_DAYS", "365")
)
