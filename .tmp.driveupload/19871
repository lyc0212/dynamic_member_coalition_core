# 运动权威静态核查
Config默认motion_model=continuous_turn、turn_max_angle=0.5（pursuit_v2/config.py）。保留原配置，不更改科学条件。
本MODEL路径权威是fixture.world.motion_rule=constant_velocity_from_public_D60_v1；prepare_branch显式核验。stfbs_d1a_model.point按position+velocity*((tick-60)*0.05)取条件目标真值，Branch.advance读取world.motion[j].velocity处理逃逸，不调用Environment连续转向生成器。
机器人由policy.command(self.frozen[j],...)控制，公开belief经trajectory计算；QMBranch.raw用point(world)产生条件bearing，原fuse用point计算G。motion_model/turn_max_angle未进入这些运动计算，故不产生连续转向作用。静态AST测试核验该事实，不进行轨迹积分或物理运行。
