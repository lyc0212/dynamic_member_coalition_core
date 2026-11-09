# 只读跨记录端点关联
不在端点添加段ID或来源字段。以外部注册的完整分支身份为根，原quality.frame_id定位feedback/frame/result；检查endpoint相等、frame和stream分支/目标/时间，按team与历史段边界唯一确定服务段，检查side及反馈顺序。
逐成员查(branch,target,robot,tick)原raw缓存，slot seal/digest、position/sigma/health上下文必须与物理profile及原包一致。重新纯prepare_frame比对归一化frame/payload摘要；不调用WLS/Q重算。
同tick旧右/新左用team、segment、stream、side及反馈顺序区分；不明确时拒绝。保留U0 raw可相等，frame packet_id按各自stream生成，不能要求两个流packet_id相同。
OLD仅改endpoint.branch时，其quality.frame_id和原feedback.endpoint仍是OLD身份；完整记录存在但跨记录身份不一致，明确ENDPOINT_PROVENANCE_MISMATCH。负例不靠缺字段、缺文件或KeyError。
关联证明依赖外部冻结证据；不是对能篡改所有可信记录/注册根的攻击者的密码学证明。G0只验证合成完整证据，RUN-G1须从真实记录运行同一关联器并冻结原始输出。
