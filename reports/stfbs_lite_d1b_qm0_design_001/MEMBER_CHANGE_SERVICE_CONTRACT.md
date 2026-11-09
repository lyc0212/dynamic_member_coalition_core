# 合法预设换员与服务/经济

U0保留T0/dual_neg45，U1由T0/dual_pos45退出空闲，U2由空闲加入T0/dual_pos45；目标不变、团队2、角色完整、资源唯一。是实验动作，不是自主搜索。
public.plan_action_metadata区分MEMBER_CHANGE/ROLE_CHANGE；prepare_assignment映射TEAM_CHANGED，旧段关闭、新段建立、clock归零、端点和事件引用完整。D1A开段标签可能为REASSIGNMENT，不能改旧schema迎合名字；独立D1B账本另记action_kind即可。
原Branch.assign验证→隔离准备→统一提交；动态schedule/notice在准备前按tick确定，不能因事务回调随机变化，失败不得留下局部费用、缓存、pending或历史。

先按旧团队结算(79,80]，右80用已生效的新sigma。freeze80后才换员；旧进度若已因Q失效清零，不另加进度损失罚。新段初始clock=(0,0)，新左80不产生服务进度；(80,81]以后必须同段相邻G/Q均PASS才累积，UNKNOWN也invalid。
U2始终从原位置按公开belief控制移动，不能瞬移或按MODEL条件真值Oracle跟踪；合法Assignment不保证立即G合法或时域内可恢复。旧/新80两次融合可以不同，但保留U0的同tick原始slot应复用，U2只生成一次；真实流/段切换专项必须在未来验证。

## 四时间

t_change为换员事务成功commit；t_GQ为新段首个G真/Q PASS实际端点；t_resume为新段首个完整有效区间的右端点；t_complete来自真实完成事件when和processed_tick。保存tick、秒、分支/任务/段/端点/区间引用。
t_GQ可为80但t_resume最早81；孤立GQ PASS不保证连续恢复。未发生用null和NOT_OBSERVED_BY_H/ACTIVE_AT_H/REJECTED等原因，不把未完成叫永久失败；不能用ceil(when/DT)替代原处理切口。

## 经济

完整Assignment逐机器人变化：U0不变、U1退出和U2加入各1，共2*kappa；kappa=0.01时为0.02。若实际还换角色则按真实条目计，不硬填2。自然完成/逃逸释放额外费用0，后续主动变化分别结算，不能重复收费。
J=completion+flow+late+effort+terminal−change_cost；按原公式并使用新场景task_count=1正确归一化，不偷用D1A两任务分母。不重复D60前沉没费用，未服务任务若存在仍演化并计成本；deadline软约束，终止罚只在真实H120，不在probe80观察截止收取。
独立验证从帧/控制/服务/事件重算费用和各收益分量，做Fraction精确二进制及浮点残差配对，不用主程序PASS代替核算。净收益正/零/负均可接受机制结论。
首轮B0/B1在80/100只更新公开belief并采取预设KEEP/换员；不调用R求最优，不比较自主动作。D1-C另行授权。
