# A2-FACTORIAL-P 准备报告

**FACTORIAL_E_READY，场景、分析口径和最小入口适配方案均已冻结。** 准备阶段未启动完整 episode。正式启动前须在 FACTORIAL-E 授权下实现、测试并冻结 LOCKED 与审计编排层。

## 历史与新输入

只读复算 VALUE-1/2 保存的 binary64 净收益差，分别为 −0.4175267270800314 和 +0.17157410652733024，符号与原验收一致。两个历史 OPEN 在 tick60 的 policy_input、候选与选择证据逐模式严格相同。两个对角世界的全部差异只有 T1 私有出生位置和速度。当前 HEAD 为 `d1e1ce6cec51bae091f615bded45a331205db80a`，338 项历史证据和科学源码在准备前后指纹一致。

| 新场景 | T1 私有位置 | T1 私有速度 | 相对 VALUE-1 的唯一差异 | 相对 VALUE-2 的唯一差异 |
|---|---|---|---|---|
| X1 | (9.20, 10.10) | (0.02, 0) | `/targets/1/velocity` | `/targets/1/position_at_birth` |
| X2 | (9.03, 10.29) | (0.40, 0) | `/targets/1/position_at_birth` | `/targets/1/velocity` |

两场景通过正式 Config、Target 类型及原公告校验。T1 仍在 tick60 才公告；提前公告用例被拒绝。历史前三轮仅有 T0 策略可见和实际观测。相同可见性及观测规则继续适用，正式新场景仍须以实际 STEP 核验。公告逐字节复用，机器人、T0、观测、G/Q、原收益和时间参数均未改。

## 入口、测试与停止

OPEN 原入口可直接读取两份新世界。VALUE-2 LOCKED 入口只绑定旧世界 SHA256，且接收显式 OPEN 路径；分叉逻辑并未固定 tick、选择或最终收益。审计驱动器则绑定旧目录。协议已规定两处最小编排适配与复用函数；本轮按授权只完成兼容性核查与方案，未改动任何已有入口或科学代码。

未来顺序为 X1 OPEN、OPEN 独立核验、X1 LOCKED、X1 复核，然后 X2。每个 R/S_NEW 调用独立采用 1800 秒外部护栏，异常保留输出并停止。四个原始输出和两个独立审计目录已登记且尚不存在。主指标、服务区间判定、精确 ΔJ 及交互公式已冻结。X1、X2 结果留空。

4 项针对性测试与 20 项既有相关回归通过。命令为 `D:\anaconda3\python.exe -B -m unittest discover -s tests -p test_a2_factorial_design.py -v` 与同命令使用 `test_a2_value*.py`。见 `targeted.log`、`regression.log`。

| 文件 | SHA256 |
|---|---|
| X1 | `581ec60ca6168461f5d00e6a23f4ee39f5111e14753e7ce9977d484541760178` |
| X2 | `17b2a888942f7ac8164c8d7832c3f8240e3676fe411dcc7cb8f59547b4f3cf21` |
| 复用公告 | `80853bbd59c1f06b1864819a98c9fae7090cbca99bbedfc9ab9198d07b5daed0` |
| 预登记协议 | `b01a67a41e987f7eef556e58075a9389316a1cc70abe62228b9f1f8f06a148d3` |
| 新测试 | `f5aa4a1042c510f1997154e3ef8d9b7d22aacb44378f8251249246ef6a632cd5` |

本轮完成后停止。后续交叉消融是否在 B 之前执行由用户决定，既定路线及受限非零 bearing 噪声检查的顺序保持不变。
