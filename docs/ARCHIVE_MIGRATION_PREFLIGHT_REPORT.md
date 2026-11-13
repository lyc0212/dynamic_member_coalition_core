# 科研档案迁移准入审查（未完成）

核查时间：2026-11-13T11:41:57.9727897+08:00

本报告为部分核查记录，不能作为最终准入裁定。读取既有 ARCHIVE_MIGRATION_REPORT.md、ARCHIVE_MIGRATION_INVENTORY.csv 和 ARCHIVE_MIGRATION_DUPLICATES.csv。

CIM 查询失败：无法从客户端访问 CIM 资源；历史尝试 psutil 的解释器路径不可用。所有进程状态 UNKNOWN。002 为用户提供的失败结案信息，尚未独立完成结案核验；003 按用户指令未结案。001 历史消费状态 UNKNOWN。

清单 657 条，10 个目录；上次盘点无重复路径记录，75 组重复哈希，其中 23 组跨目录，跨任务数未知。当前目录数见下表，尚未完成新增路径和访问错误逐项对比。

| 源目录 | 任务身份（待进一步核实） | 当前文件数 | 根目录候选 manifest 匹配 / 不匹配 | 准入 |
|---|---|---:|---:|---|
| D:\1st\stfbs_journal_run002_b7cb23ce24bd4faebcf79a423bf7d8fe | UNKNOWN | 71 | 0 / 0 | FALSE |
| D:\1st\stfbs_lite_h2_h3_extension_002_451cdb6e266e426692865771edc6a02f | STFBS_LITE_LOCAL_DEV_H2_H3_EXTENSION_002 | 142 | 141 / 0 | FALSE |
| D:\1st\stfbs_lite_h2_h3_extension_003_a801a60d3e2142ca94567c0f75929a49 | STFBS_LITE_LOCAL_DEV_H2_H3_EXTENSION_003 | 251 | 85 / 15 | FALSE |
| D:\1st\stfbs_local_dev_actual_d60_001_6037a6a8c57845c5b7aa7f84374ad696 | STFBS_LITE_LOCAL_DEV_ACTUAL_D60_RUN_001 | 21 | 20 / 0 | FALSE |
| D:\1st\stfbs_local_dev_actual_d60_002_a8f43e8d95464686b58a55ac7f70eeda | RUN_002 | 22 | 21 / 0 | FALSE |
| D:\1st\stfbs_local_dev_engineering_smoke_c25b643faece43ccb2d41128647afcd5 | LOCAL_DEV_ENGINEERING_NATIVE_TWO_PROCESS_SMOKE_V1.1 | 15 | 14 / 0 | FALSE |
| D:\1st\stfbs_local_dev_validation_d2dec7ad24a746f19a1c6ddd266aeecb | UNKNOWN | 55 | 0 / 0 | FALSE |
| D:\1st\stfbs_m3_d2a_envretry_0142a28812c5406c916afe98d6b44631 | UNKNOWN | 5 | 0 / 0 | FALSE |
| D:\1st\stfbs_member_change_001_c18fb23902c84dd4bb3f29931a411158 | STFBS_LITE_LOCAL_DEV_REAL_D60_MEMBER_CHANGE_EXTENSION_001 | 61 | 60 / 0 | FALSE |
| D:\1st\stfbs_post_consume_validation_73d3f7595a32474cb3369f5deb1f1496 | UNKNOWN | 14 | 0 / 0 | FALSE |

候选 manifest 路径及不匹配条目见配套 CSV。003 的 15 项不匹配尚未核定原因；不能断言损坏。其他匹配数量不代表最终 manifest 完整通过：报告引用、自身摘要协议、重复路径、补充 manifest、未列出的必要文件尚未完成核验。任务身份、结案、分支及证据完整性尚未逐一完成审查；零个目录已确认准入，所有目录应保留原位置。

没有复制、移动、删除或修改源文件，没有启动科研任务，没有创建 marker，没有 Git 写操作，未修改 003 执行目录。

本次报告自身摘要无法写入自身而保持不变；可由外部文件记录。
