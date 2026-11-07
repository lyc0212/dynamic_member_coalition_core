# SW3-C 冻结八族独立 TEST：一次执行及阻塞归档

最终科研状态：**BLOCKED**。独立 METHOD_VALID：**NOT_ESTABLISHED**。

32个正式世界、24份预测和32份ACTUAL标签已经生成，协调器四Gate执行完成；最终独立核验未完成，因此不能将本次报告为完整通过的独立基线，也不能以协调器自带METHOD_VALID=True替代独立证明。

## 版本、授权与抽样前修复

起始本地HEAD为c60939aef07af0cd7b4a7c896271140f75333842，初始工作树干净。候选补丁50c6fbc62c2feaa2933e6c2dea64423158c38e517e624e70e0359490b10405f7及三文件基准核对后原样应用；保留阶段A的belief来源和Gate3前诊断封存。

本轮新增当前运行私有读取拒绝回执、运行证据组装、外部资源监测及mock接口测试。用户明确授权本地提交，先建立41fbf4fd5d7035844bcd60b40866ad454fad5880，未推送。

首次外部监测器启动时psutil.disk_usage在Python3.13上抛出SystemError。当时运行时与正式输出均不存在，没有正式抽样，也没有存活Python进程；初次日志保留为PRE_SAMPLE_MONITOR_FAILURE_*。在首次私有抽样前，用标准库shutil查询磁盘并增加异常退出子进程清理，人工3秒子进程监测冒烟通过，随后固定实际执行提交 **e04cf534d1408b8dcd8034f2ea7039c0b0824bd4**。不把这次抽样前启动失败隐去，也不把它描述为第二次私有抽样。

PRESTART_TESTS.log记录26项通过，AUTHORIZED_RELEASE_TESTS.log记录6项通过。mock证据核验明确测试了精确资源字典字段和空权限回执拒绝，没有执行正式抽样或WLS。EXECUTION_PINS.json为2259项扁平指纹，覆盖177项冻结源码/协议、Release工程源码、输入、Python及科学运行时。执行后这些指纹均一致。未更改冻结方法、科学规则、评价器或独立核验器。

## 正式执行与信息隔离

LAUNCH.json登记实际命令、固定输出、2小时整轮墙钟上限、12GiB进程树驻留内存上限、最低2GiB磁盘空间，采样周期约2秒；worker单次超时1800秒。每个子进程执行记录、原始stdout/stderr和SID均保留。

当前运行AppContainer首先读取人工私有canary，绝对和相对路径都得到PermissionError/errno13；无单独WinError时不写成WinError5。此回执仅证明人工canary的访问拒绝，不声称worker实际尝试读取真实测试标签。之后Gate1/2/3原有封存文件写权限负例均由本次同一SID实际执行。共7次worker调用，退出码均0；6份非空权限回执包含读取和封存写入拒绝。STAGED_RUNTIME_PINS.json记录当前受限运行时文件摘要，mutable job/output与不可变依赖应分别理解。

八个族(3,10,5,1,8,2,0,9)公开预检均PASS，未使用备用族。之后首次私有抽样开始，源码与依赖冻结。32个世界按原sample接受合法候选，原始尝试、拒绝、世界配置及身份保存于PRIVATE_MANIFEST.json及private_sealed。32个原始D60对象在同一协调器存活，compare_family通过，未重建环境。

事件01为预检；02为Gate1；03为24份预测可信封存；04为32份ACTUAL标签可信封存；05为协调器评价完成。Gate2之前没有ACTUAL后窗。真实T1后窗仍使用同一环境、C6、tick80合法反馈与KEEP，标签和service_diagnostics在Gate3之前保存。关联阶段只读封存诊断。

所有私有/预测/标签封存文件的SHA256和文件ID、外部可信索引和三Gate锚定在事后只读复核中一致。完整科学独立核验仍因下述错误未成立。这些局部通过不等于METHOD_VALID。

## 独立核验阻塞

正式进程到达check_sw3_method_validity.py，内部先执行audit_sw3_formal.audit。该核验器在lambda敏感性检查抛出ValueError('Sensitivity mismatch')，进程退出码1。协调器已经保存EVALUATION.json，但没有生成成功的INDEPENDENT_METHOD_VALIDITY.json。

只读逐项定位得到唯一敏感性差异：M2、lambda=0.10，保存值0.07500000000000001（0x1.3333333333334p-4）；按精确有理数3/40转为binary64为0.075（0x1.3333333333333p-4），差1.3877787807814457e-17，即1 ULP。READ_ONLY_FAILURE_DIAGNOSIS.json保留两侧原值。这解释了严格相等检查的失败，不构成修改容差、修复核验器或默认METHOD_VALID成立的授权。

独立审计流程在此之前已越过主指标比较，但后续次指标及METHOD_VALID科学来源验证没有完成。本轮没有修改或重跑核验器，也没有再次执行任何正式世界、预测或ACTUAL后窗。是否允许后续仅对既有封存数据进行只读审计修复须由用户另行授权。

另需保留证据范围限制：生产私有清单保存draw、environment_object、checkpoint、公开D60及prefix_cost，不包含逐步前缀STEP的完整重放档案。T1后窗原始first/second、D60/D80和诊断已保存在标签evidence中。不得宣称已经独立重算全部T0前缀物理轨迹。

## 已保存的描述性结果（未获完整独立验收）

32个ACTUAL标签中1个完成、31个未完成。唯一完成为族10、评价槽1、世界0、tick91。正例很少，不能据此充分评价完成类敏感性及一般时间预测能力。

协调器主损失M0=0.34375、M1=0.125、M2=0.1875；M1−M2=-0.0625；严格改善族数0/8。覆盖数分别21/32、32/32、32/32；混合集合数分别0/32、16/32、24/32。协调器保存结果NO_DEMONSTRATED_GAIN，仅为未完成独立验收的描述性输出，最终科研状态仍BLOCKED。

这组保存输出未显示M2优于M1，并体现额外混合预测成本，但不将本轮阻塞包装为正式基线完成，不由此调参、补样或启动STFBS-Lite。

完整冻结次指标、逐族逐世界结果、时间分母及服务诊断位于EVALUATION.json；原始值原样保留，不能将未完成的独立次指标审计写成通过。

## WLS与资源

当前正式封存文件独立加总：MODEL=2175/2296；T0_PREFIX_ACTUAL=1952/1952；T1_WINDOW_ACTUAL=1303/1312；TOTAL_ACTUAL=3255/3264。每世界预算守卫在原生产流程执行。这些是当前数据，不是复用历史人工2175次数。

整轮墙钟340.67秒；2秒采样观测的进程树峰值467570688字节（约445.9MiB），不是操作系统连续峰值保证。逐PID最大CPU样本之和255.890625秒是采样下界；短进程、尾段与轮询间隔可能遗漏，不把它当成精确全树CPU。Gate5事件另有协调器CPU/墙钟原值。磁盘剩余、进程、RSS与Gate进度完整见RESOURCE_SAMPLES.jsonl；本次未触发资源阈值。外部监测器的psutil为既有安装，原生兼容性限制及首次故障已留证。

## 归档与停止

原始正式输出runs/a2_prediction_sw3_test_001；worker回执runs/a2_prediction_sw3_test_001_worker_receipts；外部可信回执runs/a2_prediction_sw3_test_001_trusted；运行时.sw3_formal_runtime_001。均不自动清理、提交或推送。报告AFTER.json、ACCEPTANCE.json、EXECUTION_PINS.json、BEFORE_FINAL.json、原始失败日志及SHA256.json组成归档。

ACTUAL仅指项目内独立物理仿真，不是无人机飞行实验。固定联盟完成预测评价不等于KEEP/SWITCH净收益评价。八族是探索性规模，不能作强显著性或泛化结论。测试标签已揭晓，不能作为据其设计的新方法的全新独立验证集。

本任务已停止。没有科学源码修改、抽样后修复、重试、补样、上传或STFBS-Lite实施。
