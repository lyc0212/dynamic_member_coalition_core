# 冻结H1成对复验协议（待另行授权）

本文件为准备产物，不是执行授权。原V1.3全文见 ORIGINAL_D1A_V1_3_REFERENCE.txt；本次准备V0.2全文亦附档。GATE_ACCEPTANCE_MATRIX.json 原样保留原V1.3的六项Gate定义及其依赖。准备简表对G1/G3的概括不替代原定义。

## 固定条件

同一原A2-SWITCH公开D60与历史种子；D60—D120；H1、KEEP、受约束SWITCH与原身份逐字段相同。D80/D100继续用R，不使用私有未来。零角度扰动、原传感器、原G/Q/时钟、原收益与控制均不变。旧三组运行及3765次MODEL WLS仅作工程历史；原正差额不作为新结果。

## 下次授权后的执行前关口

负责人明确批准一次复验，固定实际执行版本和源码依赖指纹。只用新目录 reports/stfbs_lite_d1a_h1_revalidation_001（若已存在立即停止）。外部批准记录字段：status=APPROVED_FOR_ONE_H1_REVALIDATION、experiment=D1_A_FROZEN_H1、authorized_by、实际head、完整source_pins路径→SHA256、output_dir、limits（见SHARED_BUDGET_CONTRACT）。还需固定world_digest/public_digest和PLAN_SELECTION身份供独立复核；驱动由原档逐字段强制核对。该记录必须来自新的负责人授权，本轮未生成。

未来命令形态：D:/anaconda3/python.exe -B scripts/stfbs_d1a_run.py --execute-frozen-h1 --approval-manifest <外部批准文件> --output-dir <新目录>。本轮不执行此命令。

## 顺序与判据

按G0/G1/G2来源、合成差分与计划关口核验，再各执行一条KEEP/SWITCH。两者共用一个Budget，每条分支有独立缓存、观测、MODEL反馈与belief。独立审计必须接收原Branch和事先注册的外部上下文；每条result经唯一类型边界进入verify/service/audit。完整历史覆盖、终止处理tick、ACTUAL前缀身份与MODEL身份不能只凭摘要判定。

G4只能在G3成立后接受：J=completion+flow+late+effort+terminal-change_cost；ΔJ=各分量配对差之和-改派费配对差。按独立逐帧及事件会计、Fraction精确二进制核算与原浮点累计残差分开报告。继承的D60前沉没费用不重复进入增量；自然释放不另收费，终端惩罚仅D120结算。任何控制、位移、belief、服务、生命周期或会计差异均不能静默放宽。

G5复核每条前后计数与整组总计，分开MODEL观测、MODEL策略评价、ACTUAL=0；记录实际CPU、外部墙钟、缓存与融合次数。全部原Gate证据齐全、独立核验通过后才可提出D1_A_MODEL_PAIR_VALIDATED。当前六Gate的新H1运行一律NOT_RUN。

失败不重试、不换H1、不换计划、不增加预算。保留RAW/PARTIAL、异常栈、分支和审计阶段、NOT_RUN检查及已经花费的成本，不发布有效新收益差额。完成复验后仍需独立科研审查。
