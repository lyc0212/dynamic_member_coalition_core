# R1-B 独立验收

R1_B_STANDALONE 为 PASS。完整 TEST_0_ISOLATION 为 BLOCKED_PENDING_SAME_SESSION_A_B_C。

可信端核验现有联接标签为 2684354563，即 IO_REPARSE_TAG_MOUNT_POINT。实际目标是固定 handoff 下的人工 private 目录。原路径和 worker 请求的相对路径指向同一文件，文件 ID 与 HANDOFF.json 登记一致。执行前后 SHA256 均为 4a21834d0dc840fa59661f5978ff2c519d9fe8f9fd65fe38ce1cca085f33a459。证据见 B1.json、B2_AFTER.json。

使用 TEST-004 的启动器、worker、科学依赖布局和最小环境建立新 AppContainer profile，capabilities 为空。实际 cwd 为固定 handoff。同一进程成功读取 input/allowed.json，随后对 input/private_link/world.json 的 rb 请求返回 PermissionError、errno 13，Python 未提供单独 Win32 错误码。进程正常退出，原始路径与结果见 B2_RECEIPT.json，PID、退出码和日志指纹见 B2_PROCESS.json。本轮没有运行科学预测。

input 使用非递归 RX 授权，并只对两个人工公开文件显式授权，避免递归 ACL 设置沿联接影响私有目标。新旧代码、依赖和权限策略差异见 EVIDENCE_COMPARISON.json。当前新增运行时文件保留在 handoff；现有 junction、目标文件和历史证据保留。新 SID 与 TEST-004 历史 SID 分别记录，未宣称同一身份连续验收。A/B/C 同会话复核未执行。正式世界、正式预测、真实标签数均为零。
