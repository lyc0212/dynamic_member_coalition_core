# SW3-C1 独立真实标签基础设施验收

**SW3_C1_IMPLEMENTATION_VALID_WITH_LIMITATIONS。** 本轮完成抽样编码、固定动作参考执行、公开一致性和预测摘要封存接口。没有生成正式开发或测试数据，没有运行预测质量评价。正式开发族四世界一致性以及盲评进程、权限和封存顺序仍须现场验收。

## 基准和新增文件

本地 `main`，HEAD `fddc4675ece2ea53c271c02a3d540d9653a8d8f8`，开始前工作树干净。新增编码补充、`sw3_c1_manifest.py`、`sw3_c1_private_worlds.py`、`sw3_c1_actual_labels.py`、`sw3_c1_sealing.py`、独立历史参考入口、针对性测试及本目录。402 项冻结源码、协议和历史证据的内容指纹前后一致，见 `SOURCE_PINS.json`。

## 各 Gate

| Gate | 实测结论 | 证据 |
|---|---|---|
| A 编码及抽样 | 四组独立黄金向量全部匹配。12 族排序为 [11,6,4,3,10,5,1,8,2,0,9,7]，分组 dev/test/reserve 为 3/8/1。备用族保留 n=7，使用实际补入的组别。拒绝非法索引、分组、逃逸和重复运动。32 次耗尽由构造测试验证。 | `ENCODING_CONTRACT.json`、`test.log` |
| B 实际标签 | 用原非 Oracle 执行器重放两条历史参考，仅推进至 tick100。VALUE-1 仍活跃，VALUE-2 在 tick95 完成并释放。 | `REFERENCE_COMPARISON.json`、各轮 STEP 和两份 LABEL |
| C 一致性和隔离 | 两条实际参考的 D60 严格一致，且独立比对四份构造视图，拒绝科学差异和嵌套私有字段。预测摘要封存与关联序号的接口负例通过。 | `INFORMATION_ISOLATION.json`、`test.log` |
| D 参考与边界 | 两条参考与历史的控制、位置、bearing 和 WLS 代表估计最大差均为零。恰在 tick100 完成、仍活跃、逃逸及异常的提取规则用人工单元测试核查。 | `REFERENCE_COMPARISON.json`、`test.log` |
| E 预算和冻结 | 记录每轮 WLS、融合、测量计数及两条执行耗时。冻结文件未变。 | `REFERENCE_COMPARISON.json`、`SOURCE_PINS.json` |

## 真实执行路径

`StaggeredEnvironment.prepare_decision()` 从真实物理世界形成公开视图。动作依次为 tick0/20/40 的 C0、tick60 的 C6、tick80 的 KEEP。只向原 `step()` 提交固定 Assignment 与当前 checkpoint ID，原 `Sensing` 生成实际估计，原 belief 在 tick80 合法消费。tick60 正确撤离 T0 并建立 T1 服务段，tick80 保留服务段、服务时钟和左端点，新流从 tick81 开始。两例的事务、事件、进度、端点、消费记录与原证据严格相同。VALUE-2 自然释放后未继续融合，STEP 到达 tick100。标签由任务事件、状态和归档共同决定。

控制分派指向 `NonOracleEnvironment._control_command`。另从各真实执行端点的窗口冻结 belief 和位置重算控制，比较结果见 `INFORMATION_ISOLATION.json`。真实入口没有调用分配器或 SW3 预测器，私有执行 checkpoint 只在执行侧取事务 ID。仅公开 D60 交给公开回调。封存验证覆盖内容篡改与错误顺序，当前序号为接口约束，未证明正式盲评的访问控制。

| 参考 | 前缀 / 标签窗口 WLS | CPU 秒 | 墙钟秒 |
|---|---:|---:|---:|
| VALUE-1 | 61 / 41 | 3.484 | 3.609 |
| VALUE-2 | 61 / 36 | 3.484 | 3.513 |

两例各在预算内。这是两条实际参考的计时。4 份构造视图只验证比较接口，没有作为四世界物理运行证据。正式开发集启动后须逐族逐字段检查。

5 项针对性测试通过，首轮测试夹具的多上下文写法错误已修复并保留原日志。参考命令为 `D:\anaconda3\python.exe -B scripts/run_a2_prediction_sw3_c1_references.py`；测试命令为 `D:\anaconda3\python.exe -B -m unittest discover -s tests -p test_a2_prediction_sw3_c1.py -v`。本轮完成后停止，建议另行授权开发集机制诊断并保留运行时关卡。
