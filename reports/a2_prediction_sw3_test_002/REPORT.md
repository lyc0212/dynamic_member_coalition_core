# SW3-C-TEST-0 人工隔离复核

**结论为 BLOCKED。** 本轮基准为 `e92cee43721039375366b38a0f226a33cbff6449`。在新目录记录人工试验，原 TEST-001 归档未修改。

- R1-A 不依赖 junction。可信端从 worker 将要访问的绝对及相对路径读取夹具，并登记内容哈希。完成运行时 staging 和 AppContainer ACL 设置后，实际 Python worker 在 Windows `CreateProcessW` 启动时失败，错误码 203。操作系统返回无法找到所需的环境选项。该错误来自启动阶段，具体缺失项未确认。没有实际 Python 进程访问证据。
- R1-B 的人工 staging 位于 NTFS。可信端尝试用 `mklink /J` 创建仅指向人工私有目录的联接，退出码 1，标准错误为 `Access is denied.`。没有创建出可验证联接，也没有执行受限读取。无法仅凭此错误确定限制来自哪一层。
- R1-C 未执行。R1-A 没有产出可供可信编排端封存的受限预测文件。代码保留了单一 profile 作用域，并为可信端复制封存后由原 SID 重启写入探针预留流程，这些流程没有实际权限验收证据。

科学等价比较器只排除 `/end_to_end`、`/selection/validation_timing`、`/selection/screening_timing`、`/prediction/cost` 与 `/prediction/results/<index>/cost` 下面的 `cpu` 和 `wall` 值。比较保留其他字段的类型和精确数值。1 项针对性单元测试通过，验证未登记的同名字段变动可被定位，整数和浮点类型差异可被识别。该测试不能代替受限预测科学等价性验收。

正式测试世界、预测和标签均为 0。未修改冻结科学代码、协议或既有证据。下一次验收需先确认受限 Python 启动环境，并在受控条件下获得真实重解析路径拒绝证据。
