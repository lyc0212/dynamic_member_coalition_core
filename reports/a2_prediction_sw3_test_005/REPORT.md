# R1-B 专项验收

结论为 BLOCKED。当前基准 382de0acd22a8f683d01d755d553b61975bda597，实施前工作树干净。

B0 确认人工目录位于 NTFS，目标存在，link 不存在。目录权限和当前令牌记录在 ACL.txt、TOKEN.txt。whoami /all 另报告无法取得用户声明信息，因此本轮令牌资料有此限制。普通目录创建和文件写入成功，不能据此确认重解析点创建权。此前同一执行环境的 mklink /J 已被操作系统拒绝，本轮没有取得新的重解析点创建权限依据，依照授权条件没有再次尝试。

B1、B2 未执行，没有创建 AppContainer profile，没有新 SID、worker 或沿联接读取回执。人工原文件保存在 artificial/private/world.json。要继续，需要可信端在具备创建 NTFS mount-point 重解析点能力的受控环境中准备登记夹具，然后在相同受限启动和 ACL 策略下验证读取拒绝。当前没有证据说明一定需要管理员权限。

TEST-004 的历史 A/C PASS 保留；本轮启动器、worker 和编排源码与其归档指纹一致性见 EVIDENCE_COMPARISON.json。没有部署新运行时，无法宣称完成新旧权限环境等价验收。SAME_SESSION_A_B_C 为 NOT_VERIFIED。正式世界、预测、标签数均为零。
