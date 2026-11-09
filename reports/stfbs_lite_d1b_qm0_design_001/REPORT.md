# D1-B-QM-0 V1.2 中文设计审查

## 裁定

D1_B_QM_0_DESIGN_READY_WITH_DEPENDENCIES。QM-G0～QM-G5契约已明确，没有发现必须改变Q/WLS/服务/经济公式才能成立的直接科学冲突；合法新MODEL fixture、动态声明薄适配、真实缓存/融合组合验证是后续直接依赖，不是本轮已经完成的实现或物理PASS。
当前cf730a41e2681efdf8880bc6b142b6deb347ac0d，科学参考c75f364bf32e6fc63be6a7080d4f21bc6d75ec55，原H1实际执行fa42557fd4ee453a27b38ab3644000830246ac42。初始工作树干净，科学目录/测试/配置相对参考无变化，原H1/追加清单及45源码核对不变。D1-A限定验收及其H1相关阻断解除保持；不重开G3或H1。

## 18项审查答案

1. D1-A已由用户认可，FINAL_RESEARCH_DECISION接受D1_A_MODEL_PAIR_VALIDATED；三种版本身份和旧档保持，不把报告HEAD变化当源码失配。
2. 首轮sigma仅改变声明精度、WLS权重与质量半径；bearing保持确定性零扰动，避免同时引入测量随机性，不宣称统计鲁棒性。
3. PASS/FAIL仅在原估计/数值前置条件成立后按r≤0.06严格判定；UNKNOWN涵盖不足测量/不可接受或不可评价等；数值异常可直接阻断。missing不等于FAIL，Q FAIL不等于belief必须拒绝估计。
4. 相同tick/目标/机器人位置/角色/方向/扰动/阈值，只改U1 sigma，OLD和DEGRADED均执行原WLS/assess_quality；不直接指定结果。新动态右80还需复核同几何条件，不拿probe替代主场景。
5. OLD及各DEGRADED_i独立branch/cache/payload，不同key空间，旧packet不修改。同一key改变sigma仍应被原缓存冲突拒绝。
6. effective、public、decision分别定义并保存；首版80/80/80，一般effective≤public≤下一合法cut。参数表是私有外生机制，当前到期声明才公开。
7. 旧团队移动到80，用effective80参数生成右80并结算(79,80]；再公布/消费/冻结，提交换员并建立新左80；(80,81]才判新服务。新左80反馈不影响刚冻结的belief80。
8. 独立physical_profile_at与public_profile_at，不将未来schedule放入view/config/seed/闭包。仅隐藏profiles不足以防packet.sigma/Q/缓存泄漏，延迟公告不支持。ACTUAL基类Oracle控制和含真状态checkpoint不能直接作为MODEL公开接口。
9. ModelRawCache键/上下文、first outcome、冲突拒绝有历史单位证据；当前H1复用/冲突0。stream标签循环并非真实换流，必须用新旧端点真实融合验证。
10. F1同tick真实成员更换后复用保留U0 raw；F2 VALID历史只读继承及上下文冲突；F3 cache/pending/融合状态和错误身份分别隔离。均是首轮未来必要专项，结果NOT_RUN，不改D1A验收。
11. 固定U0负角色保留，U1退出，空闲U2加入T0正角色，完整q2/资源互斥/生命周期检查；TEAM_CHANGED关闭旧段、建新段，原子提交。是预设动作，不是自主选择算法。
12. U1退出和U2加入各变化一次，通常2*kappa=0.02；若真实还改角色须按条目重计。自然释放零额外费，不重复加进度损失罚；新场景task_count=1分母明确。
13. 旧(79,80]绝不被新动作追溯改变；新段clock0，左80本身不产生服务；新(80,81]需同段两端G/Q都PASS。U2必须按公开belief真实移动，G可暂失效，UNKNOWN也invalid。
14. t_change/t_GQ/t_resume/t_complete分别取事务、首个GQ端点、首个完整有效区间右端和真实完成事件；可不同且可null，不填虚构值/不以ceil替代processed_tick。
15. B0/B1同一初态/任务/外生变化/成本/信息规则，独立MODEL内部状态；B1仅预设干预。B2为两机器人q2公共准入负例，零physics/WLS，不虚构三机器人中的单机器人被别的完整q2占用，也不拿missing/远G当Assignment非法。B3 missing专用UNKNOWN负例，与主sigma因子分开。保存每个profile、packet、key、WLS/Q、流/段、端点/区间、公开view/消费、位移/effort、四时间、全账及资源。
16. 最小新增合法fixture、动态实际/公开profile接口、预设controller与动态审计。原fuse/WLS/事务/advance/时钟/经济尽量复用，不修改冻结实现。D1A run中自动R选择在独立D1B驱动里改为实验动作，不改R算法，不伪造R输出。B2不扩展3固定数组内核为2机器人模拟器。
17. 六QM Gate设计为DESIGN_PASS_WITH_DEPENDENCIES，无直接科学矛盾；没有任何PHYSICAL_PASS。未来必须补合法fixture、profile信息隔离、专项端到端及真实Q准入证据。
18. 真实Q-only FAIL、动态sigma结果、MEMBER_CHANGE恢复/完成/成本及自主换员均未验证。找不到明确FAIL、无恢复、未完成或净差非正都允许据实收尾；不调阈值/时刻/初态求成功。

## 关键场景选择

不机械沿用原H1作为修复成功场景：原T0时长2.25秒，D80清零后到D120只有2秒，原U2又在(2,2)，不能先验宣称能完成。
规划独立单T0、q2、三机器人MODEL fixture：birth60，prior(9,10)、CV(0.4,0)，weight1、服务1.05、软deadline5秒、终点120；原角色偏移上初始化U0/U1，U2在正角色位置外0.70待命。它只提供潜在恢复机会，不保证G/Q。新fixture须有合法PUBLIC_PRIOR/MODEL出生与历史，D60真实首次融合后clock0；不是改写旧ACTUAL坐标或来源。未来若不接受该新fixture，必须在任何WLS前另外冻结合法初态，不能运行后选有利场景。
候选退化因子[2,4,8,16]升序，仅选第一个OLD PASS/DEGRADED FAIL且G均PASS的值，最多四项。基线不合法或候选耗尽有明确构造失败状态；异常停止。没有执行任何数值搜索。

## 科研与实现边界

首轮80/100更新合法belief但不做R最优选择，B0保持旧队，B1只在80预设换员后保持新队；未来自主净价值决策属于D1-C。只用CV与零角度扰动，不引入连续转向、随机噪声、新WLS、新Q阈值或复杂缓存。
设计成本估算一次有限批次约≤238次MODEL WLS，包含初始左端点、探针及七项各至多四融合的测试估计；不是实耗或生产守卫。MODEL策略候选WLS=0、ACTUAL=0；CPU/墙钟未测。下一执行授权前固定版本、实际预算与外部保护，不能拿旧1255或预算上限当实际值。
本轮仅静态文本/JSON/AST/Git只读/SHA及文档写入；没有科学模块导入、测试、WLS、MODEL推进、ACTUAL STEP或新物理场景，也没有修改旧档/源码/配置或提交推送。
设计完成后停止，等待独立设计审查；不自动进入任何实现/实验阶段。
