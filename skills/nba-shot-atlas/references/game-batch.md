# 按场齐发：已审定的杰罗姆前三场版本

先完成姓名、赛季、阶段和实际出场范围核验，按真实比赛与事件顺序整理全部出手；每条轨迹必须有对应圈/叉，区域统计只含运动战，不把用户另要求的罚球混进区域基准。无坐标不能编造。

## 执行顺序

1. 复用已缓存坐标、字体、头像队标与球场，新建项目并正常运行 configure_video、apply_half_court、apply_scene_framing、apply_stable_camera。
2. 运行 `python scripts/apply_approved_layout.py PROJECT`。已具备 approved_layout_version 的项目跳过这一步。
3. 运行 `python scripts/apply_game_batch.py PROJECT --duration 5 --pause 0.5 --hold 2`。
4. 运行 render_video 的 check 与 video，然后 append_zone_summary（NBA）或 append_cba_summary（CBA），追加默认6秒向右展开总结。

脚本会复制 batch_motion.py 与最新侧栏到项目，将 animation_mode 设为 game_batch、shot_animation_duration=5、source/delivery_duration=7；真实出手原始CSV不改变。三场起始0.1、1.7、3.3秒，完整弧线0.9秒、含淡出1.1秒，批间无轨迹0.5秒。游戏场数或时长变化时重新计算节奏，不能缩到弧线不可见；脚本遇到不足时要求延长时长，不漏球。

## 验收

开场0点0出手；每场所有出手共享一个开始时间，三场以此例共64次运动战出手，36中28未中。整段每条弧线都完整可见。左栏总次数值逐个增长不跳号；命中与未中由同一整数前缀计算，柱条按同一分数前缀插值，固定共同数量刻度。每批飞行结束与累计统计对齐。

英文名在中文右边、淡色，不能跟身高体重重叠。所有投篮结束再停留2秒发光，最终相机冻结；圈叉与发光共用原坐标和屏幕映射。左栏内容保持，随后用左侧背景向右展开进入十区图。最终总长示例13秒（5+2+6），完整解码并抽查编码后的动效、停留及转场帧。

这些模式适用于NBA和CBA；球场几何、左右分区、联盟基准仍按各联盟适配。公开技能不携带本次球员逐球私有缓存、付费数据、登录信息或工作区绝对路径。
