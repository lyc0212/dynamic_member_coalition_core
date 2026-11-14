# RESOURCE_INTERFACE_RESTORATION_DIFF_SUMMARY

| 组件 | 002契约 | 003失败实现 | 本次处理 |
|---|---|---|---|
| ResourceLedger | ACTUAL固定三类别 | 传MODEL及R/Assignment五键 | 只读保留，外置直接继承适配 |
| ModelJournal | 映射category及预算字典 | 被移除 | 恢复双向映射及显式原始预算副本 |
| NestedJournal | 无统一跨R调用栈 | 有栈但不映射 | 单例语义栈、唯一ordinal、LIFO和白名单 |
| LocalJournal | 原冻结持久化 | 原冻结类 | 新任务本地实现完整写入与独立诊断，不改原类 |
| R | 独立计数，不完整闭合 | 混入WLS ledger | 独立权威STARTED重建、provenance绑定和完整生命周期 |
| Assignment | 独立计数 | 混入WLS ledger | 独立额度及权威/内存核对 |
| 执行后检查 | 原core负责 | 原包装存在终结时点问题 | core返回之后才记录RETURNED |
| stderr | 合并到文件 | 没有运行中结构化接收 | 显式Win32共享读句柄和持续接收包装 |
| 初始化 | Budget在try外 | 账本拒绝导致缺失诊断 | 从LocalJournal起统一保护 |

全部是新增外置源码；没有改任何共享核心、历史执行组件或科学算法。没有将003失败分支转换为可重试状态。

最终工作树状态（本次仍未提交）：

?? docs/ARCHIVE_MIGRATION_DUPLICATES.csv
?? docs/ARCHIVE_MIGRATION_INVENTORY.csv
?? docs/ARCHIVE_MIGRATION_PREFLIGHT.json
?? docs/ARCHIVE_MIGRATION_PREFLIGHT_MANIFEST.csv
?? docs/ARCHIVE_MIGRATION_PREFLIGHT_REPORT.md
?? docs/ARCHIVE_MIGRATION_REPORT.md
?? docs/resource_interface_restoration/
?? research/non_oracle/local_dev/
