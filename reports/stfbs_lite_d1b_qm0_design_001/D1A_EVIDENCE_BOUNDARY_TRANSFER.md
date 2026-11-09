# D1A三项证据限制传递

既有D1A限定验收保持，不重开修复。本轮仅设计未来必要测试。

## F1 / test_same_tick_member_change_real_fusion_reuses_retained_raw

已有：ModelRawCache同键复用；历史stream循环仅标签，事务fixture使用fake_fuse。

未验证：旧团队右80→新团队左80真实融合的端到端复用

PASS：同B1旧U0/U1右80、新U0/U2左80各合法融合；U0 producer仍1次、U2仅1次新采样，原slot不变，流/段独立。

FAIL：重采样、通过角色/流改raw key、非法复制WLS结果、部分提交。

首轮必需：是；未来结果NOT_RUN。源码/测试精确位置见EVIDENCE_BOUNDARY_TRANSFER.json。

## F2 / test_valid_historical_slot_readonly_MODEL_inheritance

已有：MISSING继承fixture禁止producer；构造器检查历史slot身份。

未验证：VALID完整包/身份/来源与冲突的端到端组合

PASS：独立合法历史引用测试中VALID packet、digest、target/robot/tick、sigma/position不变，producer不调用；各上下文冲突拒绝，过去ACTUAL不改标新MODEL原始样本。

FAIL：改packet、重采样、忽略冲突、伪造ACTUAL checkpoint/endpoint。

首轮必需：是；未来结果NOT_RUN。源码/测试精确位置见EVIDENCE_BOUNDARY_TRANSFER.json。

## F3 / test_cache_pending_fusion_state_cross_branch_isolation

已有：缓存层branch/摘要拒绝，不代表全部pending/融合风险已验证。

未验证：cache/packet/pending/estimate/stream逐项污染与错误流拒绝

PASS：B0/B1独立可信上下文，无可变别名；修改一侧不影响另一侧；错误branch/target/stream/packet在消费/WLS前拒绝。

FAIL：跨分支污染、缺少上下文却通过、错误流或包被接受。

首轮必需：是；未来结果NOT_RUN。源码/测试精确位置见EVIDENCE_BOUNDARY_TRANSFER.json。

## 最小七项拟议用例（不是已存在或已通过函数）

1. F1真实新旧流同tick融合及保留成员raw复用；2. 同key改变sigma拒绝且正式状态不变；3. F2 VALID继承；4. VALID上下文冲突；5. F3 cache/pending/融合逐项隔离；6. 错误branch/target/stream/packet身份；7. 动态声明79/80、旧区间、冻结、换员及81新服务区间的联合时钟/费用。
每项先有合法正例再单因素篡改，核对具体拒绝原因；无文件、未启动、无上下文等无关失败不能冒充通过。历史VALID引用作为单独合法测试上下文，不移植到新主场景伪造ACTUAL前缀。优先复用ModelRawCache，不新建复杂缓存架构。
