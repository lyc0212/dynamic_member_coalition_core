# S2 完成状态驱动的动态成员联盟决策理论

**S2_COMPLETION_BASED_COALITION_DECISION — 第一轮独立数学审核存档 V1.0**

| 项目 | 说明 |
|---|---|
| 仓库 | `lyc0212/dynamic_member_coalition_core` |
| 日期 | 2026-11-16 |
| 文档性质 | 主研员理论成果的独立审查、证明整理与条件性定理存档 |
| 数学审核 | APPROVED_WITH_DIRECT_CLARIFICATIONS |
| S2范围 | 有限数学研究；不涉及新算法实施或科学仿真 |
| 经济口径 | ECON-NOC：固定改派费用为0，真实进度损失和时间成本保留 |
| 生产准入 | BLOCKED |

## 摘要

本文件记录S2第一轮已经通过数学审核的两条研究主线：一是从原经济账本中分离完成状态、完成时间与控制成本，建立无需精确预测完整价值的动作经济支配充分条件；二是将双成员角色几何写成目标位置支持集与共同服务区域之间的关系，建立单时刻几何认证条件。通过历史N1案例I/II的公开状态和ACTUAL经济结果说明其机制意义。S1同信息双世界反例给出这项研究的信息边界：即使条件价值评价器准确，当前公开信息也可能不足以判定服务完成或选择最优动作。本文不声称已解决跨反馈区间的连续服务认证，不提出新的可部署算法或普遍性能结论。

**核心成果：** 在经济区间严格分离时，完成状态足以决定动作排序；成员重构可以改变角色几何共同区域及其对位置失配的容忍度。但将瞬时G认证转化为全窗口G/Q连续服务认证仍是待解问题。

## 1. 科研背景与证据边界

### 1.1 已有研究的收缩路径

- CCVD与N1提供了成员变化、服务时钟与任务经济价值的历史案例。CCVD、N1价值预测器研究和单格归因不重新开启；BLVF保持冻结。
- N1案例I的SWITCH原参考世界评价为 −0.712539994057，实际对应世界的同世界MODEL与历史ACTUAL均约为 −0.142544315007，残差约 −2.78×10⁻¹⁷。这说明该格误差来自外生世界失配，不是普遍评价器正确性证明。
- S1用同一D60公开信息、不同T1隐藏物理定义的A/B世界，检验固定K/S/M首动作及Hold机制下的服务与决策不可辨识性。

### 1.2 S1提供的有限反例

世界A为原案例I，世界B为仅将T1真实出生位置从(9,10)改为(9.45,10)，真实速度从(0.6,0)改为(0.4,0)的合法ACTUAL世界。公开公告、原控制先验、T0物理运动、共同前缀与D60公开状态均不变。S1报告已在仓库main可读；下表由报告及历史证据提供，S1正式独立证据验收与本理论存档为不同事项。

| 指标 | A | B |
|---|---:|---:|
| SWITCH最大连续服务 | 1.05 s | 0.75 s |
| SWITCH完成T1 | D114 | 否 |
| $J(S,w)$ | −0.14254431500738049 | −0.71253999405727086 |
| $J(K,w)$ | −0.32251923105899283 | −0.32251923105899283（结构性推论） |
| $J(M,w)$ | −0.32501858815285356 | 未执行 |
| S−K | +0.17997491605161234 | −0.39002076299827804 |

共同公开状态摘要：`4ca524be946aafaeece4058597433de613cdb29452d18efa63f45d1c2b8441fe`。

在冻结Hold条件下，K只服务T0，T1隐藏运动不参与T0控制、观测及分配；A/B均无提前逃逸且未服务T1经济参数相同，因此K的价值结构性不变。A中S唯一最优，B中K严格优于S，所以无需知道B中M的价值即可得到

$$I(w_A)=I(w_B),\qquad c_1(S,w_A)\ne c_1(S,w_B),\qquad A^*(w_A)\cap A^*(w_B)=\varnothing.$$

定义 $R(a,w)=\max_{b\in\{K,S,M\}}J(b,w)-J(a,w)$。任何仅使用该共同信息的确定性首动作选择器，在两世界中的最坏遗憾满足

$$\min_{a\in\{K,S,M\}}\max_{w\in\{w_A,w_B\}}R(a,w)\ge 0.17997491605161234.$$

证明：选K在A损失约0.179975，选M在A损失约0.182474，选S在B至少损失约0.390021，取三者最小值。该下界不是精确minimax值，不推广到完整动作目录、随机策略或可根据未来信息自适应改派的策略，也不意味着必须引入主动信息获取。

## 2. 统一符号与假设

| 符号 | 含义 |
|---|---|
| $t_0,T,H=T-t_0$ | 当前决策时刻、真实episode终点、剩余时长 |
| $a,w,I,\mathcal W(I)$ | 候选首动作、物理世界、合法信息、与信息相容的非空世界集合 |
| $K,S,M$ | KEEP、SWITCH、MEMBER_CHANGE |
| $w_j,d_j,\tau_j,q_j$ | 任务权重、截止时间、连续服务要求、已有合法服务进度 |
| $c_j(a,w),t_j^c$ | 任务是否完成的指示量、完成时刻（仅完成时定义） |
| $W_{\rm ref},H_{\rm ref}$ | 权重归一化量、时间归一化量 |
| $\lambda_f,\lambda_l,\lambda_u,\lambda_c$ | flow、late、unfinished、control权重 |
| $C_u(a,w)\ge0$ | 窗口内非负控制成本，净值中扣除 |
| $r_i,d_i^{\rm role},\rho$ | 机器人位置、固定世界坐标系角色偏移、几何容差 |
| $G,Q$ | 几何合格与信息质量状态，连续服务需两者共同成立 |

假设 E1：比较动作拥有共同合法起点；所比较的相关任务均已出生且尚未完成；窗口内没有提前逃逸；无其他未纳入的动作相关经济项。窗口价值扣除共同前缀沉没收益。

假设 E2：采用原经济定义，所有成本权重非负、任务权重为正，固定改派费用为0。$T$ 是实际执行episode终点，终端未完成惩罚按原规则只结算一次。历史已完成任务或共同无关项可作为常量处理，不能漏计动作相关项。

假设 E3：所述K/S/M结论采用固定首动作与Hold语义，允许自然释放，不允许主动新增服务。具体单任务支配命题要求每个动作至多完成其指定任务，其他任务的非控制贡献共享同一基准。

假设 G1：几何部分使用原 `angular_standoff_v1` 固定世界坐标角色偏移，成员和角色完整且合法；所有几何半径与位置均为模型坐标单位，不宣称实物米制测量。

源码实现中 `geometry.radius(cfg)` 在名义容差上加 `1e-10`。本文理论使用名义 $\rho=0.15$，若用于严格复现实现语义应使用相应有效半径；不能把浮点边界误判为实质差异。

## 3. 定理E1：统一经济分解

### 3.1 非完成基准

令 $[x]_+=\max(x,0)$，在E1–E2条件下所有相关任务均未完成、且不计控制成本的窗口净值为

$$B=-\sum_j\left(\frac{\lambda_f w_j(T-t_0)}{W_{\rm ref}H_{\rm ref}}+\frac{\lambda_l w_j[T-\max(t_0,d_j)]_+}{W_{\rm ref}H_{\rm ref}}+\frac{\lambda_u w_j}{W_{\rm ref}}\right).$$

定义任务完成最低经济改善

$$W_j=\frac{(1+\lambda_u)w_j}{W_{\rm ref}},$$

以及完成后不再发生的时间成本

$$F_j(t)=\frac{w_j}{W_{\rm ref}H_{\rm ref}}\left(\lambda_f(T-t)+\lambda_l[T-\max(t,d_j)]_+\right),\quad t\in[t_0,T].$$

### 3.2 结论与证明

$$\boxed{J(a,w)=B+\sum_{j:c_j(a,w)=1}[W_j+F_j(t_j^c)]-C_u(a,w).}$$

证明：逐任务比较未完成基准与完成结算。每次完成新增 $w_j/W_{\rm ref}$ 奖励，并避免 $\lambda_u w_j/W_{\rm ref}$ 终端惩罚，同时节省完成后至T的flow和late成本，恰得 $W_j+F_j$。各任务贡献可加；从窗口总价值扣除实际控制成本。ECON-NOC没有额外固定改派扣费。未完成任务不存在上述改善。证毕。

$F_j(t)\ge0$ 且随 $t$ 非增；$F_j(T)=0$。若评价窗口仅到中间预测时刻而不含真实终端结算，则不得把避免终端惩罚计入 $W_j$，需按该窗口实际经济定义重写分解。本命题不直接覆盖提前逃逸、后续任务出生、额外动作相关惩罚或不同终止时间。

### 3.3 控制成本上界

原配置 `effort_reference = N H_ref u_ref^2`。若在剩余时间H内同时最多 $m_a$ 个机器人运动，每个速度不超过 $u_{\max}$，则

$$0\le C_u(a,w)\le C_a^{\max}=\frac{\lambda_c m_a u_{\max}^2H}{NH_{\rm ref}u_{\rm ref}^2}.$$

这是保守上界，不要求预知控制轨迹，且不把真实资源占用或时间成本设为零。

## 4. 定理E2：经济区间分离与完成状态判据

若动作S仅可能完成任务j，未完成时 $J_S\le B$；完成时 $J_S\ge B+W_j-C_S^{\max}$。若K的价值已知或有可靠区间 $J_K\in[L_K,U_K]$，且

$$\boxed{B<L_K,\qquad U_K<B+W_j-C_S^{\max},}$$

则对于同一世界中的比较，

$$J_S>J_K\iff c_j(S,w)=1.$$

证明：失败分支严格低于K下界，成功分支严格高于K上界。两区间不相交。若只获得重叠区间，不能据此断言动作排序或真实不可辨识性。证毕。

若K精确价值为 $J_K$，可令 $L_K=U_K=J_K$。若K只可能完成任务i且已知完成，则有无需历史准确净值的保守界

$$B+W_i-C_K^{\max}\le J_K\le B+W_i+F_i^{\max}.$$

因此，只要 $W_i>C_K^{\max}$ 且 $W_j-W_i>F_i^{\max}+C_S^{\max}$，同样得到S/K的完成状态判据。这里K完成本身仍是前提，不是由经济定理认证出来的服务事件。

## 5. 定理E3：不同任务之间的完成支配及进度影响

设动作a只可能完成任务i，动作b只可能完成任务j，且两者在所比较世界中均完成指定任务。给定合法最早完成时刻下界 $t_i^{\min}$，令 $F_i^{\max}=F_i(t_i^{\min})$。由E1，

$$J(a,w)\le B+W_i+F_i^{\max},\qquad J(b,w)\ge B+W_j-C_b^{\max}.$$

两式相减得到

$$J(b,w)-J(a,w)\ge W_j-W_i-F_i^{\max}-C_b^{\max}.$$

从而充分条件为

$$\boxed{W_j-W_i>F_i^{\max}+C_b^{\max}\ \Longrightarrow\ J(b,w)>J(a,w).}$$

该条件是充分而非必要，不排除条件不成立时b仍然占优。

### 5.1 离散服务时钟与已有进度

若KEEP能够合法继承当前时钟 $q_i$，连续模型的理想最早完成时刻为 $t_0+\tau_i-q_i$。原实现采用完整全局区间 $\Delta t=0.05$，且完成比较含服务容差 $\mathrm{TOL}$。与实现一致的下界为

$$n_i^{\min}=\max\left(0,\left\lceil\frac{\tau_i-q_i-\mathrm{TOL}}{\Delta t}\right\rceil\right),\quad t_i^{\min}=t_0+n_i^{\min}\Delta t.$$

这里只是理论最早下界；要求相同成员与角色身份、合法保留进度，后续区间两端点G/Q持续合格。成员/角色改变或无效服务导致重置时应按实际时钟语义处理。若 $t_i^{\min}>T$，指定完成事件在该时间预算下不可能发生，不能再套用双方成功定理。

在其他参数相同、该下界合法时，$q_i$ 增大使最早完成时刻不增，$F_i^{\max}$ 不减。因此，旧任务进度越大，新任务获得严格经济支配所需的保守收益优势可能越大（离散网格和截止时间可导致平坦区间）。这不是必须KEEP的规则；若旧任务无法完成或新任务权重足够大，切换仍可能占优。

## 6. 案例I经济数值验证（历史证据与解析计算）

冻结参数：$t_0=3,T=6,H=3,H_{\rm ref}=3,W_{\rm ref}=8$，$N=3,m=2,u_{\max}=3,u_{\rm ref}=10$，$\lambda_f=0.1,\lambda_l=0.3,\lambda_u=2,\lambda_c=0.02$。

| 参数 | T0 | T1 |
|---|---:|---:|
| 权重 | 1 | 1.5 |
| 截止时刻 | 2 | 5 |
| 服务要求 | 2.25 | 1.05 |
| D60已有服务进度 | 0.15 | 0 |
| 完成最低经济改善 | 0.375 | 0.5625 |

计算得：

- $B=-0.03125-0.05625-0.625=-0.7125$。
- $C_K^{\max}=C_S^{\max}=C_M^{\max}=0.0012$。
- K最早完成为5.1秒（42个区间），$F_0^{\max}=1/(8\times3)\,(0.1+0.3)\times0.9=0.015$。
- $W_1-W_0=0.1875$，所以双方完成时 $J_S-J_K\ge0.1875-0.015-0.0012=0.1713$。

使用E2中不依赖准确历史值的区间，K完成时 $J_K\in[-0.3387,-0.3225]$，S失败上界 −0.7125，S成功下界 −0.1512。由区间严格分离可直接得到：**只要K完成且其余假设成立，S优于K当且仅当S完成T1。**

若另使用冻结历史K的精确ACTUAL净值 $J_K=-0.32251923105899283$（对A/B具有结构性不变性），则失败时

$$J_S-J_K\le -0.38998076894100717,$$

成功时

$$J_S-J_K\ge 0.17131923105899283.$$

实际A中S−K为 +0.17997491605161234，与上述下界一致；实际B中S−K为 −0.39002076299827804，与失败上界一致。该一致性为历史结果说明，不是新增验证或调参。

### 6.1 权重充分条件

固定其余配置、任务数、旧任务权重 $w_0=1$ 与合法最早完成下界，原归一化 $W_{\rm ref}=4\times\text{task_count}=8$ 不随权重变化。双方成功条件下：

$$\frac{3}{8}(w_1-1)>0.015+0.0012\quad\Longleftrightarrow\quad\boxed{w_1>1.0432.}$$

这是严格经济支配的充分条件（不含等号），不是新任务一定应切换的阈值；不保证完成、不证明一般权重配置下的最优策略，不授权改变任何历史参数。

## 7. 定理E4：同任务成员重构的完成支配

K与M仅可能完成同一任务i。在E1–E3下，若M完成而K未完成，则

$$J_M-J_K\ge W_i-C_M^{\max}.$$

所以 $W_i>C_M^{\max}$ 时，M严格占优。对称地，若K完成而M未完成且 $W_i>C_K^{\max}$，K严格占优。完整四种组合：

| K完成 | M完成 | 结论 |
|---|---|---|
| 是 | 否 | 若 $W_i>C_K^{\max}$，K严格占优 |
| 否 | 是 | 若 $W_i>C_M^{\max}$，M严格占优 |
| 是 | 是 | 比较 $F_i(t_M^c)-F_i(t_K^c)-(C_M-C_K)$；进度通过完成时间与服务可行性间接影响 |
| 否 | 否 | 在共同B条件下 $J_M-J_K=C_K-C_M$，不能仅凭完成状态排序 |

案例I/II中 $W_0=0.375>0.0012$，故若仅一方成功，成功方至少领先0.3738。实际历史结果：

| 案例 | K完成 | M完成 | $J_M-J_K$ |
|---|---|---|---:|
| I | D102 | D105 | −0.002499357094 |
| II | 否 | D105 | +0.387513202372 |

这说明重构的价值既可能来自跨越完成阈值，也可能在双方完成时被进度损失和时间成本抵消。两个历史案例不构成成员重构普遍有效的统计证据，也不单独证明进度损失是案例I差异的唯一原因。

## 8. 定理G1：双成员共同服务区域的精确表达

对完整合法双成员联盟，记固定世界坐标角色偏移为 $d_i^{\rm role}$，约束中心为

$$z_i=r_i-d_i^{\rm role},\qquad \mathcal G_a=B(z_0,\rho)\cap B(z_1,\rho).$$

注意 $B(z,\rho)$ 在本几何章节表示闭圆盘，与经济基准标量B无关。令

$$c=\frac{z_0+z_1}{2},\quad d=z_0-z_1,\quad x=p-c,\quad D_C=\|d\|.$$

则

$$G(p,a)=1\iff \|x-d/2\|\le\rho\ \land\ \|x+d/2\|\le\rho.$$

两平方范数的最大值为 $\|x\|^2+\|d\|^2/4+|x^\top d|$，故

$$\boxed{G(p,a)=1\iff\|x\|^2+\frac{D_C^2}{4}+|x^\top d|\le\rho^2.}$$

证明仅使用平方展开与最大值恒等式。该式区分联盟中心相对于目标的失配 $x$ 与成员之间角色构型失配 $d$；两者不能相互替代。角色合法性是前提，几何表达不代替角色检查、信息质量Q或时钟。

## 9. 定理G2：共同区域的中心内外圆界

若 $D_C>2\rho$，两圆无交集（由三角不等式）。若 $D_C\le2\rho$，定义

$$r_{\rm in}=\rho-D_C/2,\qquad r_{\rm out}=\sqrt{\rho^2-D_C^2/4}.$$

则

$$\boxed{B(c,r_{\rm in})\subseteq\mathcal G_a\subseteq B(c,r_{\rm out}).}$$

证明：若 $\|p-c\|\le\rho-D_C/2$，则 $\|p-z_i\|\le\|p-c\|+D_C/2\le\rho$，故在共同区域内。反之，G1中非负的 $|x^\top d|$ 可舍去，得到 $\|x\|^2\le\rho^2-D_C^2/4$。证毕。

在二维中，内界沿两中心连线方向达到，外界沿垂直方向达到，故这两个以c为中心的半径是紧的。$D_C=0$ 时两圆重合；$D_C=2\rho$ 时共同区域仅为c。$D_C$ 减小使这两个半径增大，但不同联盟的中心和方向可能同时改变，不能据此断言新旧区域存在实际坐标下的包含关系、目标一定落入区域、任务成功概率或服务时长按半径比例增加。

## 10. 历史案例I/II几何复核

原角色偏移为 $d_-=(h,-h),d_+=(h,h)$，其中 $h=0.6/\sqrt2$。K使用U0负角色与U1正角色；M使用U2负角色与U1正角色。原D60公开坐标如下：

| 机器人 | I | II |
|---|---|---|
| U0 | (9.498793987038624, 9.575735940118388) | (9.241769673908419, 9.575735940118388) |
| U1 | (9.498793987038624, 10.424264059881612) | 同I |
| U2 | (9.6,9.6) | 同I |
| T0合法位置估计 | (9.2,10) | (9.2,10) |

将公开坐标代入G1/G2，使用名义 $\rho=0.15$，所得（数值仅为公式求值、非新仿真）：

| 案例 | 动作 | $D_C$ | $r_{\rm in}$ | $r_{\rm out}$ |
|---|---|---:|---:|---:|
| I | K | 1.7660632e−8 | 0.149999991 | 0.150000000 |
| I | M | 0.104074024 | 0.097962988 | 0.140684574 |
| II | K | 0.257024313 | 0.021487843 | 0.077360362 |
| II | M | 0.104074024 | 0.097962988 | 0.140684574 |

I中更换成员降低中心内接圆半径；II中内接圆半径增至原来的约4.56倍。这是局部构型容忍度的几何解释，而不是全窗口成功率或因果效应。I中的K与M对合法估计点的最大角色误差恰好相同（均约0.125470082），也直接说明内接圆大小不能代替区域中心与估计位置的联合判断。

## 11. 定理G3：合法位置支持下的单时刻几何认证

设合法信息可保证真实目标 $p\in\mathcal P\subseteq B(\hat p,\varepsilon)$。这里 $\varepsilon\ge0$ 是有独立依据的确定性误差上界，不得从WLS收敛、残差、局部条件数或Q PASS直接推断。若只有概率置信域，则结论必须保留对应概率语义，不能称为确定性认证。

### 11.1 内外界充分条件

当 $D_C\le2\rho$ 时，

$$\|\hat p-c\|+\varepsilon\le r_{\rm in}\Longrightarrow \forall p\in B(\hat p,\varepsilon),\ G(p,a)=1;$$

$$\|\hat p-c\|-\varepsilon>r_{\rm out}\Longrightarrow \forall p\in B(\hat p,\varepsilon),\ G(p,a)=0.$$

证明由三角不等式及G2包含关系。若 $D_C>2\rho$，G对任何目标位置均不成立。

### 11.2 对完整支持球的精确全包含条件

对任意完整合法角色集合，记 $E(a,\hat p)=\max_{i\in C_a}\|\hat p-z_i\|$。因每个圆盘的最远点距离为 $\|\hat p-z_i\|+\varepsilon$，故

$$\boxed{B(\hat p,\varepsilon)\subseteq\mathcal G_a\iff E(a,\hat p)+\varepsilon\le\rho.}$$

这是针对完整支持球的充要条件；若真实相容位置集合只是球的子集，则对该集合仅提供充分条件，不能因全包含失败就断言真实服务失败。

还可直接用单成员排除：

$$\boxed{E(a,\hat p)-\varepsilon>\rho\Longrightarrow \forall p\in B(\hat p,\varepsilon),\ G(p,a)=0.}$$

证明：取达到最大角色误差的成员，由反三角不等式，其到任何可能真实位置的角色误差均超过容差。它是充分而非必要条件；即使每个圆盘分别与支持球相交，三者共同交集也可能为空。

### 11.3 案例II的条件性认证阈值

根据原公开状态直接求值得

$$E_K=0.38249439480350855,\quad E_M=0.12547008167330306.$$

因此（使用名义容差）

- M在完整支持球内几何合格的精确条件：$\varepsilon\le\rho-E_M\approx0.02452991832669693$。
- K在完整支持球内单成员几何排除的充分条件：$\varepsilon<E_K-\rho\approx0.23249439480350855$。

展示值不得作为向上舍入后的严格认证阈值。例如 $\varepsilon\le0.024529$ 是较保守的可写小数条件。若使用实现有效半径，按同一表达式重新代入即可。现有WLS公开估计并不提供这些误差保证，故不能宣称已在D60事前成功认证M的实际几何合格；更不能宣称已认证整段服务完成。

## 12. 尚未解决的理论桥梁：跨时间连续服务

### 12.1 真实可辨识性与可计算认证

对合法候选a与世界w，令 $\Gamma_j(a,w)=\max_k q_j(k)$（包含终止前最大时钟及完成事件，不使用释放后归零时钟替代）。在当前离散服务时钟、按完成事件保留最大值的定义下，完成等价于达到实现的服务阈值；以下用符号 $\tau_j$ 表示该阈值。若按名义连续模型表达，则应明确完成比较的数值容差。

真实相容世界集合上的极值定义为

$$\underline\Gamma=\inf_{w\in\mathcal W(I)}\Gamma_j(a,w),\qquad\overline\Gamma=\sup_{w\in\mathcal W(I)}\Gamma_j(a,w).$$

所有世界完成/所有世界未完成/存在成功与失败世界是三类真实状态。真实极值满足 $\underline\Gamma\ge\tau$ 即所有世界完成，$\overline\Gamma<\tau$ 即所有世界未完成。若上确界恰等于阈值，必须处理能否取得该值；有限离散时钟与固定初始进度下的可达值为有限集合时极值可取得。一般连续模型不可默认成立。

若只有保守可计算界 $L_\Gamma\le\underline\Gamma\le\overline\Gamma\le U_\Gamma$，则 $L_\Gamma\ge\tau$ 可认证完成，$U_\Gamma<\tau$ 可认证未完成；其余情况只是当前界无法认证，不能等同真实不可辨识。S1已经给出一对具体异质完成世界，而不是仅从保守界跨阈值推出不可辨识。

### 12.2 第一反馈区间是优先研究对象（已有思路，非已验证跨时间定理）

首动作之后至第一次反馈冻结前，在尚未完成/逃逸/自然释放的活跃分支上，固定先验控制轨迹可由共同信息与候选决定，与未消费的新目标观测无关。对CV世界可写 $p_k=p_0+v(k-k_0)\Delta t$。因此可能用共享的初始位置—速度支持和逐端点几何约束构造必要条件，避免对每个世界分别做完整价值模拟。

跨时间分析不能把不同端点各自可行的目标位置任意拼接为一个相容物理世界；同一个世界的 $p_0,v$ 必须在全部端点一致。原服务时钟要求完整角色、两端点G/Q合格、合法进度继承或重置，并正确处理终止事件。若某段几何连续合格机会在乐观Q条件下仍不足所需时间，可能形成失败充分条件；但仅有瞬时G合格或某些端点可能合格不等于任务完成。

第一次反馈后，控制轨迹依赖世界自身的观测、定位接受、速度差分、传播和后续冻结，不能继续把同一先验轨迹当作所有世界的真实轨迹。本轮未建立覆盖这些机制的有效全窗口认证。

### 12.3 后续有限数学研究与止损

下一轮只优先研究：利用联盟几何失配、合法目标位置支持及剩余连续服务时间，能否建立非平凡、低成本的跨时间完成或失败充分条件。若只能返回过宽的未知范围、必须构建复杂闭环可达集或重新大量遍历完整物理世界，则重新评估科研收益，必要时保留E/G理论并停止复杂化路线。不因本存档启动S2工程、S3信息获取、额外ACTUAL/MODEL或恢复旧预测器研究。

## 13. 独立审核记录及状态

| 编号 | 命题/成果 | 审核状态 |
|---|---|---|
| E1 | 统一经济分解及控制成本上界 | APPROVED，限定真实终端结算 |
| E2 | 经济区间分离与完成状态等价 | APPROVED，严格分离充分条件 |
| E3 | 不同任务完成支配及进度关系 | APPROVED，双方成功及合法离散时钟前提 |
| E4 | 同任务成员重构支配 | APPROVED，限定共同经济基准 |
| G1 | 双成员共同几何精确表达 | APPROVED，完整合法固定角色 |
| G2 | 中心内外圆界 | APPROVED，不等于实际包含或概率改善 |
| G3 | 单时刻位置支持几何认证 | APPROVED，需有合法确定性误差界 |
| N1历史数值 | I/II经济与几何复核 | VERIFIED_FROM_FROZEN_INPUTS |
| 跨时间服务认证 | 完整G/Q及反馈下完成认证 | NOT_ESTABLISHED |
| 一般算法优势及文献创新性 | 统计性能、计算优势、创新性 | NOT_ESTABLISHED |

直接澄清记录：R1真实终端结算；R2离散服务时钟与时间可行性；R3共同区域尺度不等于实际目标覆盖；R4严格几何边界与误差保证。以上均已合入正文，不需另行整改或追加实验。本文将原主研员推导、独立审查员此前的区间判据和本次直接数学澄清统一组织，未更改原冻结证据。第6节不依赖历史K准确净值的区间判据、第10节关于相同最大误差的观察及第11节单成员排除证明是独立审查整理中的直接推论，不是新增科学计算任务。

```
S2_ROUND_1_MATHEMATICAL_REVIEW = APPROVED_WITH_DIRECT_CLARIFICATIONS
THEORY_ARCHIVE = V1.0
ADDITIONAL_MATHEMATICAL_REMEDIATION_REQUIRED = NO
S2_FINITE_THEORETICAL_STUDY = AUTHORIZED
S2_CROSS_TIME_SERVICE_CERTIFICATION = NOT_ESTABLISHED
S2_ENGINEERING_IMPLEMENTATION = NOT_AUTHORIZED
NEW_SCIENTIFIC_EXECUTION_AUTHORIZATION = NOT_GRANTED
S3_ACTIVE_INFORMATION_ACQUISITION = DEFERRED
CCVD_REOPENING = NO
N1_REOPENING = NO
BLVF_CORE = FROZEN
PRODUCTION_ADMISSION = BLOCKED
```

## 14. 来源索引与存档说明

**主研员材料**：`CCVD研究(2).md`（本轮原推导，经济分解至几何认证）；`CCVD研究(1).md`（S1结果及案例I经济等价命题）；本轮及上一轮独立数学审核意见。

**冻结原始证据**（提交 `69fee291885f354978ba3ed7b873579b1ba87c34`）：

- [原案例配置](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/reports/n1_independent_decision_validation_001/ATTEMPT_001/EXPERIMENT_CONFIG.json)
- [I/PUBLIC_D60.json](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/reports/n1_independent_decision_validation_001/ATTEMPT_001/I/PUBLIC_D60.json)；[II/PUBLIC_D60.json](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/reports/n1_independent_decision_validation_001/ATTEMPT_001/II/PUBLIC_D60.json)
- [I/DECISION_FREEZE.json](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/reports/n1_independent_decision_validation_001/ATTEMPT_001/I/DECISION_FREEZE.json)；[II/DECISION_FREEZE.json](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/reports/n1_independent_decision_validation_001/ATTEMPT_001/II/DECISION_FREEZE.json)
- [I/ACTUAL_VALUES.json](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/reports/n1_independent_decision_validation_001/ATTEMPT_001/I/ACTUAL_VALUES.json)；[II/ACTUAL_VALUES.json](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/reports/n1_independent_decision_validation_001/ATTEMPT_001/II/ACTUAL_VALUES.json)

**冻结源码**（同提交）：[经济执行与服务结算](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/research/information_service_online/execution.py)、[配置与归一化](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/pursuit_v2/config.py)、[角色几何](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/pursuit_v2/observation_geometry.py)、[服务时钟](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/pursuit_v2/service.py)、[非Oracle控制](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/research/non_oracle/environment.py)、[belief消费](https://github.com/lyc0212/dynamic_member_coalition_core/blob/69fee291885f354978ba3ed7b873579b1ba87c34/research/non_oracle/belief.py)。

**单格归因**：[报告（固定提交 d8d3f32e00c65aafd1817073b1c3254c22717ed6）](https://github.com/lyc0212/dynamic_member_coalition_core/blob/d8d3f32e00c65aafd1817073b1c3254c22717ed6/reports/n1_switch_failure_attribution_001/ATTEMPT_001/N1_SWITCH_FAILURE_ATTRIBUTION_REPORT.md)。

**S1新增报告**：[S1_WITNESS_RESEARCH_REPORT.md（本次读取main，尚未在本文固定同步提交SHA）](https://github.com/lyc0212/dynamic_member_coalition_core/blob/main/reports/s1_service_identifiability_witness_001/ATTEMPT_001/S1_WITNESS_RESEARCH_REPORT.md)。报告、配置、执行状态、资源回执和可辨识性分析已读取；未在本次理论审核中完整核验所有S1证据文件及提交身份，因此不将S1正式证据验收标为通过。部分文件读取未成功，这不影响独立的S2数学定理审核。

**归档建议**：本文件使用UTF-8 Markdown保留LaTeX公式及可追溯链接，建议作为独立理论记录保存至 `reports/s2_completion_based_coalition_decision/THEORY_V1.0.md`（建议路径，未写入仓库）。本次仅制作本地可下载存档、读取历史证据和进行代数/几何公式的直接求值；无新的物理仿真、WLS、Solver、R、Assignment、代码修改、提交或推送。S2本轮数学成果审核通过，但没有新工程执行授权。
