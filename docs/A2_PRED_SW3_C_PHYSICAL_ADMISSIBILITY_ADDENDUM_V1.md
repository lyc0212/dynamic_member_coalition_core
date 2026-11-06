# SW3-C 物理准入补充 V1

基准提交为 `a4f29dcdd24cef3bd7b968a8bedc8973ce7e34b1`。原运行记录保存在 `reports/a2_prediction_sw3_dev_001`。开发族 11、世界 0 的 a=0 航向约为 −0.939 弧度。原环境构造器以 `Arc heading leaves the eastward envelope` 拒绝该候选。补充生效前未生成正式预测或真实标签。

保留原 SHA256 字符串、族划分、尝试编号、位置及速度公式，包括速度角 π(u₃−0.5)。候选生成分布保持原样。最终接受样本改为经过固定物理合法性及同族去重筛选的条件样本，每个世界最多尝试 32 次。

开发、独立测试和备用族统一采用相同规则。先按冻结规则检查有限性、速度域、位置域、无逃逸及去重。对本协议的连续转向配置和零转率匀速目标，若航向绝对值超过 0.5 弧度加 1e-8，则记录 `HEADING_OUT_OF_PHYSICAL_ENVELOPE` 并继续下一尝试。既有拒绝原因包括 `NONFINITE`、`VELOCITY_DOMAIN`、`POSITION_DOMAIN_OR_ESCAPE` 和 `DUPLICATE`。其余候选必须通过原 Target 与 Environment 构造守卫后才可接受。固定模板非法、未识别的异常以及 32 次耗尽均停止当前 DEV。筛选过程不使用预测、观测或完成标签。

原三份 SW3 协议及 M0/M1/M2 保持冻结。预测假设超出真实物理航向包络的情况单独记录，分析其对类别和时间集合的贡献。
