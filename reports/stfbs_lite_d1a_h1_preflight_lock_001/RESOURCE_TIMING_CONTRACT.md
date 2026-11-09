# 资源计量与保护契约

正式唯一入口为 scripts/stfbs_d1a_watchdog.py；其CLI只允许固定900秒墙钟与600秒CPU配置，不提供阈值覆盖参数。主脚本缺少合法watchdog票据会在authorize/输出/Branch前拒绝。票据绑定真实父子PID、父进程命令、批准文件SHA、900秒及挂入Job后才恢复执行；子解释器使用-I/-B。这里是最小可信编排检查，不声称能防御恶意可信Python代码。

watchdog先执行原authorize（审批、HEAD、源码、工作树、新目录），再创建与正式输出并列的新 <output>_watchdog 证据目录。子进程以CREATE_SUSPENDED启动，在执行任何用户代码前加入Windows Job，写入LAUNCH后恢复。Job启用KILL_ON_JOB_CLOSE，不允许子进程breakaway；正常、异常和超时均保留退出码、stdout/stderr原字节及真实墙钟。900秒或整树600秒触发即终止整个Job，等待退出，无自动重试。子进程内部原Budget仍保持600/900及1000/4000/5000原值。

主进程CPU来自保留的进程句柄GetProcessTimes；整树CPU来自Job Basic Accounting的累计用户/内核时间；后代CPU为两者之差。CPU与墙钟均覆盖H1子进程完整生命周期，而非只覆盖Branch.run。确认Job ActiveProcesses=0后才标cpu_complete。查询失败或仍有活动进程时保留null/原始已得值、缺失原因和范围，不能填零。OS实际返回零CPU是测量分辨率下的真实值，不能用预设零替代。watchdog自身开销不包含在子进程CPU字段内，scope明确登记。

短时测试只验证机制：正常、退出码7异常、0.3秒单进程超时、1秒带后代超时；未进行真实900秒或H1负载试验。初次因Python未导出常量失败的原始回执仍保留。全部实际测量值见EXTERNAL_WATCHDOG_TESTS与各WATCHDOG_RECEIPT。

未来G5必须由外层收齐正式LAUNCH/最终回执、原始日志、批准/执行源码指纹、PID与输出身份、整组WLS/CPU账本后独立验收。verify_watchdog_receipt默认拒绝短时测试回执、非正式生产标记、缺失或无效CPU、超时、非零退出及未清零的进程树；资源函数PASS只表示资源证据必要条件成立，不自动判定G5或D1-A通过。内部Budget通过、watchdog启动成功、或历史人工回执均不能替代这次正式证据。
