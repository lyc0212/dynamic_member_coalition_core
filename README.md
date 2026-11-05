# Windows GQ科研代码

Windows源码态单目标GQ运行与审计；包含R独立评价及S_NEW缓存共享评价。仅固定单目标场景完成Windows回归，不代表多任务、随机可靠性或性能改善已验证。

## 环境与运行

在Windows x64安装Python 3.13.5，在仓库根目录创建并激活虚拟环境，再执行：

```powershell
python -m pip install -r requirements.txt
python -B scripts/run_gq_windows.py --scene configs/gq_windows_single_target.json --output runs/gq_both_001 --evaluator both --max-candidates 12 --timeout 360
```

仅上述Python 3.13.5、NumPy 2.1.3和SciPy 1.15.3组合已用于回归，其他版本未验证；依赖声明不代表pip安装态包经过验收。场景是合法单目标执行输入，来源见同目录provenance；输出目录必须不存在。SUMMARY记录运行状态，逐轮候选、决策、独立episode审计及最终指标位于输出目录；默认没有额外独立候选模拟。

运行非科学CLI测试：`python -B -m unittest discover -s tests -p test_gq_windows_cli.py -v`。360秒both回归中R/S_NEW各6轮、tick120终止，预测/实际WLS各636/28，轨迹与W4-R1对应，净收益0.21873421456963033；参见docs/GQ_WINDOWS_CLI.md。历史研究辅助入口和部分独立诊断依赖未随仓库提供，不属于此版本支持范围。许可证尚未指定。

## Known Limitations

`research/information_service_memory_accounting/auditor.py`、`prepare.py` 和 `supervision.py` 引用未包含的历史 `information_service_future_profile` 或 `information_service_final_summary` 依赖；相关历史扩展入口未验证，不承诺可用。该限制不代表固定单目标回归中这些入口已经执行。
