# Windows GQ科研运行入口

本入口提取自W4-R1已验证运行链；不修改科学公式、原选择器或原审计规则，不依赖W1～W4历史产物运行。需Windows x64、Python>=3.10、NumPy及SciPy。实际工程回归环境：D:/anaconda3/python.exe，Python3.13.5、NumPy2.1.3、SciPy1.15.3。无需WSL/Linux/Docker。

从项目根目录PowerShell运行（每次使用不存在的新输出目录）：

```powershell
python -B scripts/run_gq_windows.py --scene configs/gq_windows_single_target.json --output runs/gq_R_001 --evaluator R --timeout 180
python -B scripts/run_gq_windows.py --scene configs/gq_windows_single_target.json --output runs/gq_S_001 --evaluator S_NEW --timeout 180
python -B scripts/run_gq_windows.py --scene configs/gq_windows_single_target.json --output runs/gq_both_001 --evaluator both --max-candidates 12 --timeout 180
```

both依次创建两个独立环境，不混用真实状态或缓存。运行物理身份含每运行新UUID；预测和实际流分离。示例输入按字节从已通过W4输入整理，SHA和来源见同目录provenance.json；CLI实际只读取指定场景，不读取历史结果或赢家。场景格式沿用原OnlineEnvironment私有执行输入：config/positions_initial/targets/initial_assignment/sensor_declaration_schedule/measurement_model，原环境、请求和审计继续做合法性核验。

`--max-candidates`默认12，超限失败，不截取候选。`--max-decisions`默认不截断，完整模式运行至真实TERMINAL；若显式上限在终止前达到，则保存失败和部分证据，不能称完整episode成功。`--timeout`默认180秒，覆盖子进程导入、真实计算、审计和子进程输出，父进程准备源码摘要和最终摘要尾部不包含；这是简单外部墙钟保护，不是CPU/内存硬限额，超时保存TIMEOUT，不自动重试。当前worker不创建额外子进程；未声明通用进程树监管能力。

`--audit required`为唯一支持模式，不能关闭原主候选/决策/episode审计。reference_required固定false，不运行额外独立候选模拟，不继承历史N1/N2研究资格。

产物：SUMMARY.json为总状态PASS/FAIL/TIMEOUT，RESULT.json含周期/预测WLS，RUN_OPTIONS/ENVIRONMENT/SOURCE_PINS/INPUT保存运行身份；stdout/stderr保存退出信息；R或S_NEW目录含逐D决策、完整候选结果和感知、PREDICTION_AUDIT、TABLE/SELECTION及其原独立审计、实际流登记、STEP/ACTUAL_FRAMES/ACTUAL_FUSIONS/AFTER；最终PRIVATE_SNAPSHOT/EPISODE_INDEX/EPISODE_AUDIT/FINAL_METRICS及ACTUAL_SENSE_SUMMARY。S_NEW各批含缓存作用域、命中/构建、MEMORY和侧车收据。失败保留FAILURE及已产生文件；启动前参数/输入错误直接报错，不创建伪运行PASS。

当前集成回归仅用合法单目标、零扰动示例，both一次，各6次COMMITTED至tick120，原审计通过；实际收益、动作和轨迹字段与W4一致。R/S单独选项完成参数/分派检查，未为验证命令额外重跑两个episode。不是多任务竞争、Q失效、换员、三机共享、随机可靠性或性能改善结论。合法输入支持仍受原q2共享/感知/审计域限制，不承诺任意新场景无需核对即可通过。Windows侧车保留文件fsync/原子替换/字节核对，不声称Linux目录fsync持久化保证。

后续实验优先复用此入口，在独立授权下声明输入、方法、工作量和审计范围；本次没有实现Lazy、性能统计框架或额外参考模拟。
