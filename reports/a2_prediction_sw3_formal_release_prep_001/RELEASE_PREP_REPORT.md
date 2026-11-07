# SW3-C Formal Release 准备验收

结论为 SW3_FORMAL_RELEASE_PREPARED_NOT_AUTHORIZED。当前实际 HEAD 为 708b7860f98e12ad9dd6b27fdebdc7fe130083b4，main，实施前工作树干净。GitHub 连接器 compare_commits 确认该提交与 main identical、ahead/behind 均为0。本轮未提交源码，未来正式授权版本尚未固定。

## 最小工程修改与预检

修改 sw3_formal_physics.py，将主族公开检查提取为 public_precheck(n)，备用族也调用同一方法。它核对冻结任务、出生、先验、声明、误差界、速度界和族中心身份，再依据已冻结的位置域检查给出族特定失败。共同模板先独立验证，输入畸形、冻结身份错配及未知异常直接阻断，不能触发备用。全部实际八族及备用7通过公开检查，没有私有抽样。备用7公告中心为 (9.1,10.3)。

sw3_formal_adapter.py 的 reserve_precheck 不再直接返回PASS，先核验共同模板，再调用public_precheck(7)。生产前缀补入已有61次/世界WLS预算守卫。没有修改科学预测、原执行器、WLS或协议。

Release定向测试5/5，受影响FI回归17/17。首次定向测试错误地把备用7的中心写成族11的中心，保留release_tests.log，修复人工预期后release_tests_retry.log通过。另一次diff检查发现写文件时引入CRLF，已恢复LF，通过diff检查。未新增科学阈值。

## 三重硬锁及未来受控开放

当前CLI无条件拒绝，Coordinator仅接受IMPLEMENTATION_TEST+ARTIFICIAL，ProductionPhysics的实际prepare/finish无条件拒绝。布尔参数和环境变量无法解除。检查的是未授权协调链路不可达，不限制独立导入研究模块。

未来正式授权需以一次受控源码版本变更同步开放FORMAL_RUN+PRODUCTION，并保持其他组合拒绝。正式生产仍由ProductionAdapter绑定物理sample与原暂停对象，受限AppContainer处理公开输入，三个可信封存屏障继续生效。不能把本轮准备工作树或FI历史baseline直接当作未来正式执行版本。实际开放后的文件摘要和运行命令应在抽样前重新固定。本轮没有实施该开放。

## 预算核对

MODEL每族41+123+123=287，八族2296。T0前缀每世界61，32世界1952。T1后窗每世界41，32世界1312。总ACTUAL规划上限3264。新增前缀守卫与原后窗守卫分别落实61和41，本轮用静态调用关系和非执行测试核对，不声称已在正式32世界实测。正式路径保持硬关闭。

本轮MODEL、T0前缀ACTUAL、T1后窗ACTUAL、总ACTUAL WLS均为0。未把历史2175次人工MODEL调用当成正式资源实测。

## 非正式容量预演

使用已归档DEV族11世界0，构造32个独立StaggeredEnvironment初始对象，每个附带独立复制的已归档前缀证据。没有运行STEP、观测或WLS。对象均处于tick0，并非live D60队列状态。

可信进程RSS基线78139392字节，驻留采样132923392字节，最终132976640字节；进程峰值working set 133058560字节。CPU 0.859375秒、墙钟3.9244264秒，三次一秒间隔采样稳定。另一个普通Python子进程正常退出。该子进程不是受限科学预测，不能代替worker负载稳定性验收。既有人工链路归档100453819字节，可用磁盘118367580160字节。完整数值见RESOURCE_REHEARSAL.json。

预演设定了30秒构造阶段、2GiB RSS和子进程10秒超时保护。未验证真实32个D60环境的观测缓存、长期驻留、峰值资源和全程预测等待稳定性；这些风险须在正式授权时明确接受，不能据本次小规模驻留保证正式完成。

## 版本和证据

177项冻结源码及协议指纹一致，V2为90291aaf8b0f637e0a2d86168d1f91666c151748cc84e99637f8dc54cd314d7f。RELEASE_SOURCE_PINS.json记录冻结科学、Release源码、原场景与公告、Python、NumPy、SciPy、实际受限运行时文件及工作树状态。

复用FI人工OS、可信封存与独立核验历史证据。此次仅修改生产预检和预算守卫，未改变worker、输入输出传输、ACL或封存边界，因此未重复AppContainer验收。原handoff和历史证据保持原样。只读Git远端查询首先因受限环境中凭据助手失败，随后通过GitHub连接器完成关系核查，没有fetch或更改本地版本。

正式TEST族为(3,10,5,1,8,2,0,9)，DEV为(11,6,4)，唯一备用7；每族四世界、一份公开D60、三方法预测，标签逐世界，主评价八族等权。揭盲后该测试集不得再作为据其设计的STFBS新算法的全新确认集。

本轮结束后正式世界、正式预测、ACTUAL标签仍为0。下一步仅需用户单独授权正式Release的受控版本变更、接受所列资源风险，并冻结实际执行版本与四Gate一次运行计划。当前授权不包含正式运行。
