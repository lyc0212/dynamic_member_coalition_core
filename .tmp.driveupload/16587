# SW3-C 正式 Release 候选阶段 A 验收

状态为 SW3_FORMAL_TEST_RELEASE_CANDIDATE_READY_NOT_AUTHORIZED。当前HEAD为7084e73a2e38bc38578ebfcd61a7dd7a425944dd，GitHub连接器确认与main一致。当前为含阶段A工程修复的未提交工作树；不能将HEAD单独当作未来正式运行版本。

## belief 与 Gate 3 诊断

ProductionPhysics.prepare 在D60提交C6之前深拷贝T1 belief，记录公开切口摘要、checkpoint及原环境对象身份。verify_pauses 检查原对象、checkpoint、D60内容及prior。finish 只从同一个原环境推进至D80，在合法消费后深拷贝updated，校验measurement/available为60至80、consumed为80，再提交KEEP。

ProductionAdapter.finish 调用新增工程证据检查器，复用原diagnose计算，并在写原始标签时一并保存prior、updated、原切口及消费来源。诊断数据在Gate3封存前生成。associate只读取已封存service_diagnostics，生产记录缺失诊断则拒绝。MOCK标签不要求伪造真实belief。原extract_label和主损失均未修改。

定向测试使用既有VALUE2实际物理归档，只读重建诊断，验证prior/updated来源、缺失和错配拒绝、消费时序、生产finish写入顺序、标签完成时间保持，以及封存后诊断篡改拒绝。没有执行任何新的物理STEP或WLS。

首次定向测试发现diagnose中的NumPy int64不能直接由标准JSON写入。工程检查器现在将诊断转换成标准JSON数值，数值与科学判定保持原样。初次日志保留targeted_tests.log。候选生成脚本还曾在写补丁前出现引号语法错误，修正后生成，未触及实际解锁代码。

## 隔离候选补丁

FORMAL_UNLOCK_CANDIDATE.diff为唯一候选文件，SHA256见CANDIDATE_BASE.json。补丁基于当前阶段A工程工作树的逐文件摘要，不可仅依赖初始HEAD应用。git apply --check通过，本轮未实际应用。

补丁将CLI、Coordinator正式组合和物理guard统一到受控Release调用作用域。只有FORMAL_RUN+PRODUCTION作为正式组合，人工组合仍为IMPLEMENTATION_TEST+ARTIFICIAL。生产方法在作用域之外继续拒绝；普通formal_authorized布尔参数不授予权限。新的作用域与runtime源码只存在于补丁和isolated_mock证据副本，实际工作树的CLI、Coordinator和物理三重硬锁均保持关闭。

隔离验证只编译候选类和函数，并将后端注入为fake。候选运行时测试中的世界和公告为空人工JSON，stage/native/worker/adapter/Coordinator全部为fake依赖，未加载或调用真实sample和物理后窗。隔离副本不含可执行的完整生产科学依赖。原型候选作用域测试验证离开作用域后拒绝恢复。未来不能把Python私有命名约定当作对恶意可信端代码的安全防护，信任边界仍为可信协调端对受限worker。

## 独立有效性判定

新增check_sw3_method_validity.py使用现有可信索引和独立统计审计。人工封存链路核验成功时只报告artificial_evidence_valid，正式METHOD_VALID为null、formal_status为NOT_RUN。正式模式缺少执行来源、预检、受限进程、权限、源文件、ACTUAL诊断或WLS账本证据则拒绝。正式路径复核原始标签来源、世界身份、原环境及checkpoint、D60/D80诊断重算、前缀与后窗预算。没有把evaluate固定METHOD_VALID=True当成权威结论，也没有修改该冻结函数。

证据核验使用历史人工封存文件，正式路径的实际验证仍待阶段B产生真实证据后完成。共享底层可信封存核验及原诊断函数，主统计公式仍由现有独立审计器重算。

## 回归与范围

本轮最终定向测试9/9、当前硬锁及V2回归5/5、受影响FI回归17/17。所有177项冻结科学指纹保持一致。未重跑AppContainer历史链路，未更改权限和科学worker；formal_worker只补充可信进程创建元数据字段created。原始证据与失败重测日志均保留。

阶段A新增MODEL WLS、ACTUAL WLS均为0。正式世界、D60、预测及ACTUAL标签均未生成。原handoff、junction和历史归档未修改。未执行Git提交、推送或切换。

## 未来阶段 B 的独立授权和确定步骤

用户须单独明确授权应用候选、接受32个live D60环境长期驻留及正式运行资源未完整实测的风险、一次性生成八族私有世界并按四Gate执行，以及失败后不自动补样或重跑。

取得授权后，先核对候选基准与补丁SHA256，在实际工作树应用补丁，再核查三入口组合与177项科学指纹，生成扁平EXECUTION_PINS.json及实际生效源码/依赖清单。该清单必须包含受控开放后的文件，不能直接把阶段A包含嵌套字段的SOURCE_AND_DEPENDENCY_PINS.json作为runtime的--pins输入。

计划正式输出为runs/a2_prediction_sw3_test_001，受限运行时为.sw3_formal_runtime_001，worker回执为runs/a2_prediction_sw3_test_001_worker_receipts，可信回执为runs/a2_prediction_sw3_test_001_trusted。均须不存在。基础world和announcements沿用configs/a2_value2_two_target_v1.json与configs/a2_value2_public_announcements_v1.json，由冻结族清单和原sample产生正式私有样本，禁止复用旧OPEN结果。

候选CLI接口为--mode FORMAL_RUN --world <冻结world> --announcements <冻结公告> --workspace <唯一新runtime> --output <唯一正式输出> --pins <受控版本的扁平文件指纹映射>。版本、资源监测、外部运行护栏、可信索引描述符及独立METHOD_VALID输入证据须在首个正式抽样前登记。阶段B仍需记录实际资源与完整WLS，运行后独立核验统计及方法有效性，不能把此处的mock启动通过等同于正式完成。

本轮结束于阶段A，当前正式执行仍为HARD_CLOSED。
