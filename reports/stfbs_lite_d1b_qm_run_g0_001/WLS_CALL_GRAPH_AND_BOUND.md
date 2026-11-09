# WLS调用图与整数预算提案（不是批准）

MODEL_*_WLS沿用外层estimate()入口口径。BridgeFrameProcessor.process每个新合法frame至多调用一次estimator_fn；重复frame不重复估计，少于两测量跳过。estimate内部对(4,10,16)^2九初始点逐个调用least_squares；nfev/njev不是外层WLS。

Branch.assign → prepare_assignment → 新段fuse；同团队KEEP仅更新first_fusion_tick，不融合。Branch.advance每个服务tick至多一个fuse，本场景只有T0。

五个探针各左60一次+61..80二十次=21，共105。OLD已是正常参考，禁止第六前缀。B0左60+61..120最多61；B1再加新左80一次=62；B3保守至多61（实际80起旧团队测量不足可能跳过，所以实际通常少于上限）。主链上限105+61+62+61=289外层。

原28次专项只有估算，无逐项调用图，不能据此宣称317已核定。本次提出最小专项方案：F1仅独立读取B1已产生的旧右80/新左80=0；F2 VALID继承组合一条新流一帧合法正例=1，冲突在WLS前拒绝=0；F3两个隔离流各一合法正例=2，其后篡改负例在WLS前拒绝=0；独立来源/历史/Q代数/收益审计均不重算WLS=0。

因此提案为289+3=292外层、最多292×9=2628底层优化启动。317/2853作为原条件性算例保留，未作为本提案批准预算。新专项调用数量是未来协议建议，不是已实施真实专项，RUN-G1必须核实实际实现与此调用图一致后单独批准；不允许带着未核定实现直接使用292。若专项必须额外前缀或新融合，首次WLS前修订提案，不通过运行后追加预算。

外层调用开始后失败照记，事务失败不回滚；底层启动后异常照记。预算拒绝发生在估计器前，单独记rejected，外层/底层均不增。外层与底层分账、不相加。策略评估WLS=0，ACTUAL=0。真实计量回调为候选结构，G0入口始终关闭；本轮九次内层验证全是标记替身，不证明真实埋点完整。

源码依据：stfbs_d1a_model.py Branch.fuse/assign/advance；stfbs_d1a_history.py prepare_assignment；information_service_bridge/public_stream.py process；cooperative_sensing/estimator.py estimate。逐文件指纹见RUN_POLICY。未调用这些科学执行入口。
