# SW3-C-TEST-0 第四轮人工隔离验收

**结论为 BLOCKED。** 诊断通道和人工 R1-A、R1-C 通过。R1-B 仍缺实际重解析路径负例。基准为 `a06301d9851ecb048c42eb9284c06e3c04bb8808`，实施前工作树干净。

## D0 捕获验收

首次原生 cmd.exe 人工探针成功创建 PID 31548，以预登记的 47 退出。stdout 和 stderr 各 26 字节，与各自的固定标记逐字节相同。长度、SHA256 和原始字节见 `D0_NATIVE_PROCESS.json` 和两个日志。捕获文件以独占创建模式生成。启动器使用 STARTF_USESTDHANDLES 与 PROC_THREAD_ATTRIBUTE_HANDLE_LIST。子进程只继承空输入只读句柄和两个独立人工日志的只写句柄。使用普通文件捕获，无匿名管道缓冲等待。父端在 CreateProcessW 返回后关闭自己的子端句柄。三轮人工尝试均先通过 D0，再启动 Python。

## D1 首个失败及限定修复

原打包布局复现退出 1。受限 Python 最小代码和标准库探针都已正常退出，原始 stderr 随后定位到 worker 导入 `ctypes` 时 `_ctypes` 的 DLL 加载失败。核对安装中的 `_ctypes.pyd` 发现其引用 `ffi.dll`。将原运行时的该 DLL 加入 staging DLLs 后，重试越过该错误。第一次重试进一步定位到冻结策略引用的 `scripts.gq_windows.a0_plans` 未打包，NumPy 同时报告缺少 MKL 初始化模块。随后只补入已定位的策略依赖文件和原运行时 MKL 包。第二次重试的 NumPy 2.1.3、SciPy 1.15.3 导入以及人工 worker 回执均通过。三次原始证据分别保存在本目录、`ffi_retry/` 和 `policy_dependency_retry/`。首次复现的失败可定位到 worker 导入阶段，历史 TEST-003 的同一退出码当时没有 stderr。

## 人工预测及权限

最终重试使用同一 AppContainer profile 和 SID 完成 R1-A 与 R1-C。三种冻结预测均执行。与可信端比较时，仅排除登记的计时值，其他科学字段严格一致。预先核验的绝对、相对私有文件以及未授权仓库文件均由受限 worker 返回 PermissionError，目标哈希保持不变。人工探针及依赖清单见最终重试的 R1-A 文件。

可信端验证三份人工预测产物后，同一 SID 对输出文件的 FILE_WRITE_DATA 正对照全部取得并关闭句柄。可信端复制到独立封存对象并记录源与目标身份及 SHA256，之后同一 SID 对三份封存副本的同等请求均返回 WinError 5，文件 SHA256 不变。此证据适用于封存副本的权限。实际封存与权限回执见最终重试的 R1-C 文件。

R1-B 本轮没有重复运行无新增权限依据的 junction 创建命令。前轮在 NTFS 的人工联接创建返回 Access is denied。当前没有经核验的联接，也没有 AppContainer 沿联接读取的拒绝证据。要通过完整关卡，仍需在受控 NTFS 环境中由可信端建立只指向人工夹具的重解析点，再用同一受限配置实测读取拒绝。

精确比较器针对性测试 1/1 通过。冻结科学文件、协议、历史证据未修改。正式测试世界、正式预测和真实标签均为 0，TEST-1 至 TEST-5 未执行。
