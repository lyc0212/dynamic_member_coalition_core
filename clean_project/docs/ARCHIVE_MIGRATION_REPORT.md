# 科研档案迁移报告

状态：未完成；没有复制或删除源文件，不能报告迁移成功。

只读盘点发现以下目录（文件数；字节数）：

- `D:\1st\stfbs_journal_run002_b7cb23ce24bd4faebcf79a423bf7d8fe`：71；150960
- `D:\1st\stfbs_lite_h2_h3_extension_002_451cdb6e266e426692865771edc6a02f`：142；28074839
- `D:\1st\stfbs_lite_h2_h3_extension_003_a801a60d3e2142ca94567c0f75929a49`：251；7436693
- `D:\1st\stfbs_local_dev_actual_d60_001_6037a6a8c57845c5b7aa7f84374ad696`：21；10322981
- `D:\1st\stfbs_local_dev_actual_d60_002_a8f43e8d95464686b58a55ac7f70eeda`：22；18998006
- `D:\1st\stfbs_local_dev_engineering_smoke_c25b643faece43ccb2d41128647afcd5`：15；63772
- `D:\1st\stfbs_local_dev_validation_d2dec7ad24a746f19a1c6ddd266aeecb`：55；130862
- `D:\1st\stfbs_m3_d2a_envretry_0142a28812c5406c916afe98d6b44631`：5；7037
- `D:\1st\stfbs_member_change_001_c18fb23902c84dd4bb3f29931a411158`：61；21161314
- `D:\1st\stfbs_post_consume_validation_73d3f7595a32474cb3369f5deb1f1496`：14；18766

目标为仓库 `runs/` 下按任务 ID 建立的目录；本次尚未建立目标或迁移文件，迁移数量和字节数均为 0。源文件相对路径、字节数及 SHA256 见 `ARCHIVE_MIGRATION_INVENTORY.csv`；同一哈希出现多次的 75 组见 `ARCHIVE_MIGRATION_DUPLICATES.csv`，可用哈希关联清单中的具体路径。尚未进行目标文件哈希、数量或字节数对比。

所有上述文件均未迁移：进程命令行查询被系统拒绝，无法确认任务是否正在使用；目录的结案状态、任务身份及归档范围尚未逐项确认。003 明确尚未完成，须等待结案。目录中可见脚本、输入、日志、结果、冻结和失败证据，但尚未完成逐项分类。manifest 引用尚未逐条核查，其绝对路径可能仍指向源目录；不得将副本当作执行文件。

盘点前 `git status --short` 为空；本次新增本报告及两个清单，未执行任何 Git 写操作。此状态不包含之后可能发生的外部变化。
