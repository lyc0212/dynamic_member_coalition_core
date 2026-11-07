# TEST-0 同会话 A/B/C 联合验收

SAME_SESSION_A_B_C 和 TEST_0_ISOLATION 均为 PASS。

基准为 234bfbe2d77bf6c7e9f4669c6a72a982109086c7。J0 核对现有 junction 标签、实际目标、文件身份、同相对路径可读性和哈希，均与 handoff 登记一致。TEST-004/006 历史 SHA256 清单及当前运行时指纹复核通过。新建的人工预测文件由本轮受限进程产生。

一个新 AppContainer profile 持续覆盖全部四次受限调用。R1-A、R1-B、R1-C 正负对照回执的 SID 完全一致，所有进程退出码为零。PROFILE_OPEN.json、PROFILE_LAST_GATE.json、PROFILE_CLOSED.json 记录 profile 上下文生命周期。

R1-A 以固定人工公开 D60 执行冻结 M0(K=1)、M1/M2(K=3)，三份结果经原精确比较器核验通过。只排除已登记的计时字段。私有状态、轨迹、未来观测、标签、抽样资料和未授权源码的绝对及相对访问均返回 PermissionError、errno 13，目标哈希保持不变。

R1-B 在相同 SID 和固定 cwd 下成功读取 input/allowed.json，但 input/private_link/world.json 被操作系统拒绝，Python 回执为 PermissionError、errno 13，未提供独立 Win32 错误码。可信端执行前后确认联接指向预期 private，文件 ID 为 1970324839875868，哈希不变。

R1-C 同 SID 对三份新输出的 FILE_WRITE_DATA 正对照成功，句柄关闭且内容未写入。可信端建立 sealed_joint_007 独立副本，登记源与目标文件 ID 和内容 SHA256。相同 SID 对三个封存对象的同等写访问请求均返回 WinError 5，封存哈希不变。这证明副本权限，不声称原输出文件的 ACL 原地撤销。

input 采用非递归 RX，公开文件单独授权；private 和联接未执行递归 ACL 修改。现有 junction、人工目标、运行时保留。本轮只新增人工夹具及报告。正式世界、正式预测、真实标签均为零。PREDICTION_SEAL、ACTUAL_LABELS、TEST_EVALUATION 均为 NOT_RUN。

已具备 TEST-0 的人工隔离准入证据。正式八族执行编排、全局可信封存及真实标签关卡仍需按既定授权与协议单独执行和验收。当前联合通过不等于正式独立评价完成。仓库内 staging 体积问题留待独立处理，本轮未清理或移动。
