# L3-B 停止后恢复审查（READ-ONLY）

任务：STFBS_LITE_L3_B_FEEDBACK_CONSISTENCY_001  
审查日期：2026-11-14（Asia/Shanghai）  
总裁定：**L3_B_BLOCKED；当前诊断程序不具备直接恢复启动条件。**

本报告仅为只读取证和源码静态审查。唯一新增文件为本报告；未运行、导入、实例化诊断程序或科学模块，未执行 P1—P4、WLS、Assignment、R、MODEL、ACTUAL、测试或科学 attempt。未修改任何既有文件，未执行 Git 写操作。本文的 CONFIRMED 表示文本、静态代码或现有证据确认，不等于动态验证通过。

## 一、停止原因与真实资源证据

### 1. 精确触发条件（CONFIRMED）

`diagnose.py:10–14`：

```python
PRIOR_CPU=15.
DEADLINE=datetime.fromisoformat('2026-11-14T15:55:59+08:00').timestamp()
if time.process_time()-C+PRIOR_CPU>=115: raise RuntimeError('CPU_STOP_RESERVE')
if time.time()>=DEADLINE: raise RuntimeError('WALL_STOP_RESERVE')
```

实际 deadline_epoch 为 **1794642959.0**。触发是系统民用时钟到达固定绝对截止时间，不是 `monotonic()-start >= 300`。代码没有从实际任务开始时间推导该截止点的记录。

原 traceback 指向第151行 `try:check();status,error=main()` 中的首次 `check()`，再指向第13行。Python 顺序执行语义说明 `main()` 未调用。因此 STAGE_0 只是初始阶段标签，不表示程序内阶段0已经完成或开始读取科学输入。完成诊断单元和参考计算均为0。

### 2. 启动前后的计时依据

| 范围 | 依据 | 判断 |
|---|---|---|
| 前期准备、只读检查、代码编写及中断 | 无统一CPU/单调墙钟起点；只有部分命令时间、工具返回和文件时间 | NOT_VERIFIED，不能复原精确累计量 |
| 准备CPU | 手工设置15秒保守预留 | CONFIRMED为预留值；不是实测消费，也没有证明覆盖全部准备开销 |
| 正式入口墙钟保护 | 固定民用时钟截止15:55:59+08:00 | CONFIRMED；不是可靠累计墙钟账本 |
| 正式进程局部计量 | 第4行之后的process_time与monotonic差值 | CONFIRMED存在；范围仅为局部片段 |
| 报告与封存 | 第153行先取快照，第154–158行再写报告、清单及打印 | 未包含在最终消耗快照内 |

### 3. 能确定的时间及不能确定的部分

原回执报告 `current_wall_seconds=0.01171510000131093`、`cpu_seconds_current=0.015625`。这只是该进程从第4行到第153行取样之间的局部测量，不是总运行时长，也未覆盖进程最早启动、最终报告写入、清单写入和退出尾部。

已观察到的两个准备时间点为15:52:19.8900470和15:55:38.8190554（+08:00），相差 **198.9290084秒**。这能说明这段任务活动的日历时间跨度；不能作为完整CPU或精确正式累计墙钟。文件元数据显示启动回执在15:56:07附近写入，晚于截止时间，但文件mtime不是精确的进程开始或退出回执。

完整任务墙钟、准备CPU、全部辅助进程CPU、最终退出尾部及历史峰值存储均 **UNKNOWN**，不能记为零。无法从当前证据判断原300秒累计墙钟是否实际超限。

### 4. 是否有真实CPU/Storage超限证据

- **没有CPU超限证据。** CPU检查在墙钟检查之前且未抛出CPU异常；在该局部取样时，局部CPU加15秒预留尚未达到115秒。不能由此宣称整个任务累计CPU合规。
- **没有Storage超限证据。** 原回执13114 bytes仅为取样时目录内容（当时主要是程序本身），不是最终大小或历史峰值。审查开始时七个归档文件合计 **32034 bytes**，远低于67108864 bytes，但也不证明全部历史临时写入受完整监控。
- **实际停止由固定保守截止策略触发（CONFIRMED）。** 不是已测得300秒真实累计墙钟超限；也不是科学错误、P1不一致或预算CPU/Storage超限导致。本次停止保护本身暴露出计量起点和截止时间推导缺陷。

## 二、工作区保全与变化

### 1. 当前Git状态

- HEAD：`f0227c73673cddcba54375835de0f3ec3db66ccf`，当前分支main。
- 上一提交：`76316a4e0f2fe757b677814c147c83414055df4e`。
- 本次审查开始时 `git status --short --untracked-files=all` 仅列出 `?? clean_export.py`。
- `git diff --stat`、`git diff`、`git diff --cached --stat` 均无输出。
- HEAD较上一提交新增七个L3-B归档文件，提交说明为L3_B_BLOCKED。此提交已存在，不是本次审查创建。

上次启动前记录为干净工作树、HEAD为76316a4e；上次启动后记录为新增任务目录及clean_export.py。现在任务归档已经纳入HEAD，clean_export.py仍为未跟踪。不能将这次HEAD变化归因于诊断程序；程序中没有Git提交路径。

### 2. 上次新增归档文件（本次审查前）

| 文件 | bytes | SHA256 |
|---|---:|---|
| diagnose.py | 13114 | 03bc70dcf2414092cf37d6c22194713586caa1adb6d4c5a0d80582cfd521c860 |
| evidence_manifest.json | 462 | d81ac6ed3c5b1f8a67cc0844f11caa46c91e349e4d4ab285e9e75674d42cffa2 |
| FINAL_REPORT.json | 1030 | c2063f6946f23eb200d58e6083851d7f7ae94b4ab46af5282bcca7dfd50fa931 |
| FINAL_FILE_INVENTORY.json | 1071 | 28a8d76e1bcf5703101e0527fe6771d8bbadebef61c06593e88849119a5f470b |
| ORIGINAL_EXECUTION_DRAFT.txt | 13937 | 3412486361bf989abdd8c8c1ac69e6cec9ce7d88c7fc55c229aaeac397e28869 |
| REPORT.md | 1201 | 4c1baea8aa628a138b2f24f84789137c1cb9a06329c885ad3ed3c7ae736d2e1d |
| STOP_EXPLANATION.md | 1219 | 895f7334cfc20ef284e13f1e3294a6502390e3aa1651600ef9f6bc870e94fcec |

原evidence_manifest覆盖程序、回执和REPORT；补充FINAL_FILE_INVENTORY覆盖六个文件，不含自身。该分层范围应如实保留，不将其说成启动时已覆盖全部最终证据。

### 3. clean_export.py专项

- 大小：**1500 bytes**。
- SHA256：`640361bc91dd3967324c12dc9f843372e58512c0d5a68ec9f58451b9c69f5bd0`。
- 创建时间UTC：2026-11-14 07:56:33（本地15:56:33）。
- 修改时间UTC：2026-11-14 07:56:52（本地15:56:52）。
- 内容：导入os/shutil，从当前目录遍历，排除reports、runs、虚拟环境、.git等目录；按.py/.json/.yaml/.yml/.ini/.toml/.md/.txt后缀复制到`./clean_project`。若目标目录已存在，代码会先调用`shutil.rmtree(dest_dir)`。
- 与L3-B关系：**SUPPORTED：看起来是一般代码导出工具，不是L3-B诊断程序。** 未引用任务、P1—P4、科研预算或反馈流；作者、创建目的和是否曾执行未知。
- 当前`clean_project`路径不存在；不能据此证明该工具从未执行。
- 静态注意：clean_project未列入遍历排除集合，输出目录位于输入目录内，存在遍历自身输出的风险；这不是本次修复范围。不执行、不修改、不清理该文件。

## 三、诊断程序逐项静态审查

| 项目 | 标记 | 静态结论 |
|---|---|---|
| P1历史实现等价性 | NOT_VERIFIED | 第127–130行有原实现与诊断输出比较；实际未执行。使用当前导入模块，之后核对历史source_sha256，若全部相同可支持源码等价；未核对历史Git blob及全部环境身份。仅对归档value/ledger比较，未逐一核对所有已归档核心任务/终端字段。 |
| P2传播截断开关 | SUPPORTED | 第108–114行对已有观测belief取消位置截断及速度归零；PUBLIC_PRIOR不变，公式与原command结构一致。尚无动态等价证据。 |
| P3反馈接收 | BLOCKED | 有独立命名空间Beliefs.freeze回放和状态/历史/receipt比较，但未独立建立完整队列和冻结边界，见问题F1。 |
| P4联合处理 | SUPPORTED / NOT_VERIFIED | 同一streams用于P3/P4且NoCap开关相同；处理定义静态可见，但依赖P3证据链，尚未运行。 |
| D80/D100切面连续性 | BLOCKED | 单一for循环，边界只改belief，结构支持连续；第122行主动跳过全部dict，主要服务状态未被检查，见F2。 |
| change_cost重复计费 | SUPPORTED | 修改后的循环仍在末尾仅调用一次原ledger；changed为逐机器人动作差异数量，边界没有Assignment或费用调用。实际未验证。 |
| MODEL/ACTUAL隔离 | SUPPORTED / NOT_VERIFIED | 不修改生产enqueue；独立命名空间直接pending+freeze，不进入生产enqueue。但独立回放保留ACTUAL_WLS等历史内部字段，未给注入belief/逐拍日志补全外部MODEL来源映射。 |
| available_tick约束 | BLOCKED（完整时间审计） | 第77行只验证available<=消费tick，未核验available>=measurement、frame与event时刻一致及冻结前已入队。不能称完整时间链核验。 |
| 经济账本 | NOT_VERIFIED | HF有signed components求和减change_cost对net的检查；Proxy依赖原ledger/P1比较。未实现完整时域、归一化、延续策略和完成后行为审查。 |
| 24个诊断单元 | SUPPORTED / NOT_VERIFIED | 版本4×世界2×candidate数量；未断言candidate恰为三个唯一动作。实际完成0。参考计数在返回后加1，异常启动不计数。 |
| CPU计量 | BLOCKED | 单进程process_time存在；无完整准备/子进程账本，15秒无实测依据，结束尾部不覆盖，检查存在长区间空档。 |
| Wall-clock计量 | BLOCKED | 固定民用时间截止与局部monotonic并存，无可核验统一累计起点，非300秒累计监督。 |
| Storage计量 | BLOCKED（完整峰值保证） | 保存前检查当前目录大小，符合部分新增占用检查；没有全任务峰值、全部临时目录覆盖或最终封存计量。 |

### F1：反馈回放未完整证明原队列语义

位置：diagnose.py:62–85。

程序强制seed.pending为空（不支持一般遗留pending），随后仅按归档事件的consumed_tick筛选，跳过PENDING事件，并把consumer.pending每次替换为单条记录。没有独立重建冻结前队列、核对pending跨边界延续、检查queue_ordinal及feedback_digest，也未把frame.target_id/frame.tick/available与事件字段逐项绑定。原observed_branch.py:46明确存在target/tick/estimate绑定检查，本程序没有等价完整实现。

状态和历史终值相等可支持结果一致，却不能替代完整队列时序及来源链。SOURCE_INVENTORY中准备写入的feedback_replay='PASS'超出这些静态检查覆盖范围。实际文件未生成，不存在本次已产生的虚假PASS结果。

### F2：切面检查遗漏主要状态

位置：diagnose.py:117–123。

`state`包含positions、states、lefts、geometry_before、statuses、tasks、effort。第122行的`if not isinstance(x,dict)`跳过states、lefts、geometry_before、statuses、tasks，因此只比较positions数组及effort数值。之后无条件记录state_unchanged=True，不足以证明所有要求状态无变化。

代码本身没有显式重置这些对象，故连续性结构可获SUPPORTED；但不能把当前断言认定为完整连续性验收。

### F3：动态源码变换及历史基准缺少保护

位置：diagnose.py:32、45–48、92–99。

生产模块先导入，再核对source_sha256；诊断源码用多次字符串replace生成，未断言每个替换恰好命中一次，也未记录真实生产策略command的独立数值对比。未修改生产全局变量，故不属于生产全局monkey patch。但当前源码SHA相同是历史等价的必要证据，尚不是已通过P1的证据。

新增proxy_diagnostic.py在运行中才写入；本次未进入main，因此该文件和各阶段输出不存在，不能将其当成已核验实现。

### F4：状态来源、科学指标及验收输出不完整

位置：diagnose.py:85、115、123、134–148。

controls只保存部分字段，缺少逐拍observation_age、完整MODEL来源、receipt身份、重置事件和明确的首次控制偏离计算。未生成完整状态误差、平均signed bias、Delta_AE、KEEP/SWITCH差值、epsilon最优集合、分层机制归因及中文科学分析。当前report仅为通用回执，不是V0.5要求的科研报告。

PHASE在单元成功保存后才更新，进入新版本的首个单元失败时可能显示上一阶段。任一反馈证据异常均直接进入全局except，未实现反馈不足时有条件保留P2独立继续的约定。

### F5：硬预算及最终接收没有完整闭合

位置：diagnose.py:4、10–21、51–58、118、128、147–158。

- CPU阈值115（包含15秒预留）与120秒授权上限之间有5秒名义余量，但未证明预留覆盖准备或余量覆盖封存。
- SHA批量读取、反馈批量回放、原实现参考计算及最终保护核验内没有充分检查；仅靠边界和单元开始的check不能保证所有阶段遵守硬上限。
- 未禁止/核验导入库可能启动的子进程；程序主体没有主动subprocess调用，但这不能补齐准备命令和未知子进程的累计CPU。
- trace代码写入和REPORT.md直写不经统一save存储预检；其他任务目录或临时写入没有统计。
- 最终资源取样发生在报告/清单之前；失败后仍写文件，但没有单独封存余量核验或封存失败的二级记录。
- 原稿要求的源保护、最终预算、全部必要输出及完整证据接收条件未汇总为PASS前置条件。main返回PASS_CANDIDATE只表示其自身有限路径成功，不能覆盖V0.5全部验收要求。

以上均为静态发现，不是本次实际触发的故障。当前仅WALL_STOP_RESERVE为已发生的入口异常。

## 四、恢复启动前必须满足的条件（建议，不构成修改授权）

1. 保留本次失败、七个既有归档文件及clean_export.py；不复用已占用的open('x')输出路径覆盖历史。
2. 用户明确授权任务本地必要修正及一次后续启动；本报告不授予代码修复或运行权限。
3. 建立真实起点、单调累计墙钟及实际CPU范围；说明前次不可恢复的资源如何在剩余额度中保守处理，不能自行把未知数记0或凭空声称已精确核算。
4. 存储口径固定为新增文件逻辑大小峰值，覆盖代码、日志、临时文件、最终报告及封存，不扩大成累计物理写入监控系统。
5. 修正反馈绑定/队列核验、切面断言、P1归档字段及正式成功条件；保持模型、预算和24+至多6规模不变。
6. 补全实际科学指标与报告，但不增加工程专项组或新科学试跑。参考计算和所有核验均计入预算。
7. 若在现有预算内无法可靠完成或历史反馈不足，保留部分结果并按已批准状态规则停止；不通过重置预算或自动重试推进。

## 五、本次操作结论

本次只读审查确认：原停止属于缺乏精确起点支持的保守墙钟截止，不是已测得CPU/Storage/累计墙钟超限。科学执行没有开始。程序存在多项恢复前必须处理的静态缺陷，不能原样重启并期望得到可验收科学结果。

本报告不改变原FINAL_REPORT.json、STOP_EXPLANATION.md、attempt状态、历史科研结论或生产BLOCKED状态。完成后停止，等待用户决定。
