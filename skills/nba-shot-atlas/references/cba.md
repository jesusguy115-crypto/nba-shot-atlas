# CBA：身份、取数、坐标和制作

此流程已用贺希宁2025-26常规赛完成26秒、1080p/60fps成片验证。数据依赖用户在CBAstats的有效登录及可访问权限；不能承诺所有球员所有历史赛季都有坐标。普通CBA数据调查不需要渲染；用户要求制作视频时完成下面流程。

## 输入与赛季

姓名先查 `assets/cba/player-aliases.json` 和本地缓存身份表，再从网站搜索核验中文全名、英文名、球队、playerId。CBA与NBA的ID不互通；不得把NBA别名解析结果用于CBA。新球员身份及常见中英文别名立即存缓存，易混中文名须核对球队。

仅给姓名时询问赛季，列出该球员源站实际可选赛季和“全部可用赛季”；已给赛季则不重复问。可选赛季不等于一定有完整坐标，逐季核查。NBA的1996-97起始界限不适用于CBA。用户指定常规赛就仅常规赛；未指定沿用常规赛＋季后赛，并分别抓取、标注缺口。

已验证CBA leagueId=10003。2025-26源站seasonYears=[2025]（起始年）、seasonId=200732，常规赛stageType=1、stageTypes=[1]；规范CSV为season=2026、season_type_id="2"，季后赛规范值为"4"。其他源站stageType、seasonId从页面筛选及实际响应确认，不把NBA的2/4直接发给CBA。

## 从已登录网站获取业务数据

优先使用现有浏览器工具及登录状态；可用Kimi WebBridge时按其技能会话规则执行。没有对应工具时使用环境提供的浏览器能力，不要求用户手工复制所有比赛。操作权限不足时说明实际缺项；不绕过登录或付费限制。

打开球员页 `https://cbastats.com/#/player/<playerId>/shot-charts`，确认赛季/阶段后读取正常应用返回的数据。已验证普通应用客户端可调用以下接口，执行示例在 `scripts/cba_browser_api.js`。它接收当前网页观察到的正常应用client，不保存账号或鉴权头。

- 比赛：POST `/api/base/shoot-plot/games`，body必须为**筛选对象数组**。player筛选项为 `{leagueIds:[10003],seasonYears:[2025],stageTypes:[1],playerId:"21674"}`。只有日期/阶段、不带球员或球队，不能假定返回全联盟。
- 坐标：POST `/api/player-shot/shot-plot`，body `{playerId:"21674",scheduleIds:[...]}`；去掉playerId得到选中比赛双方全部球员。按40场分批，成功一批落盘一批，断点复用。不得按坐标去重；两次相同坐标可以是真实两次出手。
- 精确赛季技术统计：POST `/api/players/match-base-data-info/player`，body含playerId、leagueIds、seasonId、seasonYears、stageType、stageTypes、dataType:"sum"。响应可能为多行，必须选择相同赛季/阶段。核对fga、fgM、thfga、thfgM、gamesPlayed，不能用场均四舍五入值推算。
- 逐回合：正常应用GET/POST调用路径 `/api/match-events/filterPage?startNum=0`，参数 `{scheduleId}`。先观察当前页面实际method与body。应用封装函数可正常返回已解码data.records；必要时分页到total/空页。缓存**完整比赛所有球员**事件，便于同场其他球员复用；保留id、playerId、quarter、eventTime、eventType。不把某一球员过滤后的41场事件冒充全联盟PbP。
- player league/season目录：`/api/base/players/<id>/league-list` 和正常页面的season-year筛选请求；身份与素材URL从页面/比赛信息响应获取，不猜头像/队标文件名后缀。

2026-10-16观察到主客户端模块 `index-f0db0e4d.js` 导出a6，比赛模块 `index-948846c6.js` 导出y（PbP）、m（game-info）、d（league）。这些是**当时公开前端模块**，hash/导出名会变；仅作为诊断线索。缓存发现记录，遇到404/导出失效只从当前页面script、公共模块import及正常请求重新发现一次，不重复沿用旧哈希，不提取或公布登录令牌。可直接从正常已渲染页面/业务响应获取等效数据。

### 全联盟基准

已有相同联盟＋赛季＋阶段＋几何版本的联盟坐标缓存时直接复用。否则取得该赛季球队列表（源站联盟目录，或已覆盖球队的比赛对手网络），按每队获取比赛，按scheduleId去重，分批获取双方全部球员坐标。贺希宁41场对手覆盖了当季20队；20队赛程返回840行，去重420场、56,584条坐标。**其他球员或进行中赛季不保证单一球员对手覆盖全部球队**，须核查球队目录和已赛赛程；未覆盖全联盟不能标成完整联盟基准。所有分页都检查终点。

统计图比较CBA同赛季、同阶段、同几何区域的总进/总投；不能借用NBA、只拿深圳比赛、平均球员命中率，或直接采用不一致的官网15区均值。源站hotShootArea汇总曾漏掉底角命中，最终总计始终从shootList逐条计算，并与独立精确技术统计核对。

## 规范化和事件对齐

每批干净JSON至少含shootList，行含pbpType/playerId/scheduleId/teamId/shotX/shotY。2PM、3PM为进，2Pm、3Pm为未中，**大小写有意义**；只包括2/3分运动战出手。原始顺序保留。

现代CBA已验证的686×640半场坐标：

```text
x_m = (shotX - 0.5) × 15
 y_m = shotY × 14 - 1.575
x_legacy = -x_m / 0.3048 × 10
 y_legacy = y_m / 0.3048 × 10
```

篮圈世界点(0,0,10ft)。远距离压哨球shotY可>1，不能截断或删除。其他年代/数据图比例发生变化时先重新校准，不把现代映射无条件套到所有历史赛季。

坐标无事件时间；逐回合有时间但shotX/Y可能null。已验证坐标顺序对应原始事件ID顺序，有补录事件时网页展示顺序不等于比赛时间。每场筛选对应球员2PM/2Pm/3PM/3Pm，按ID排序，核对**完整球值＋命中类型序列**，只在唯一匹配时绑定；随后按比赛日期、节次、倒计时、eventId排序播放。禁止同类型贪心凑对、线性分配时间、混用两套相机或随机补缺点。

可执行适配器（Python环境使用技能requirements）：

```bash
python scripts/prepare_cba_data.py league --batches <批次JSON列表> --season 2026 --phase 2 --output <cba-league.parquet>
python scripts/prepare_cba_data.py player --batches <批次JSON列表> --season 2026 --phase 2 --player-id 21674 --games <games.json> --pbp-dir <逐场目录> --official <official.json> --output <shots.csv>
```

games.json是`[{"scheduleId":100030020041,"game_date":"2025-12-20"},...]`；official.json是已核验所选口径`{"fga":613,"fgM":294,"gamesPlayed":41}`。逐场JSON为`{scheduleId,scope:"whole-game",records:[...]}`。仅球员缓存须声明`scope:"player",player_id:21674`，不能用于别人。适配器拒绝非唯一对齐、重叠比赛批次、未解释的技术统计差额，输出CSV和.audit.json。发生歧义时查看该场原始事件与正常投篮图，不能伪造匹配。

已验证样本：官方613投294中，坐标612投294中，全部41场覆盖；缺的是2025-12-20对北京北汽第一节08:02两分未中，eventId51198862。左栏显示“坐标出手”612，所有柱状图与总结同612口径，在交付说明中报告缺1次。不要把这条个案写成其他球员固定缺口。

## 球场与执行

球场采用对应年份实际主场，先确认场馆、地板配色、中圈标、底线字、赞助及篮架参考。已经保存的深圳2025-26龙华文体中心参考重绘在 `assets/cba/shenzhen-longhua-2025/`；附provenance。它是当季使用过的主场，不能冒充全年唯一场馆或官方精确扫描；不能给其他球队套深圳地板。头像从已核验URL缓存原始透明素材。

现代FIBA全场28×15m，篮圈距底线1.575m，双篮间距24.85m，篮下半径1.25m，禁区宽4.9m，罚球线距篮心4.225m，三分半径6.75m、侧线直段距中轴6.6m。历史线规需查对应年份。依据 [FIBA官方规则](https://refereeing.fiba.basketball/en/rules)。

1. 从模板新建项目，传自己的shots/job/court/portrait/logo。job指定`league:"CBA",court_dimensions_m:[28,15]`、实际player_id、中文/英文名、赛季/阶段、expected_attempts/made/games及bar_scale；后者覆盖最大区域总出手。存在缺口时加入official_attempts、official_made、missing_coordinate_attempts。深圳预设court_texture_box=[240,3600,180,1980]，其他地板重新测边界。头像crop按实际图片，不能套乔丹裁切。
2. 可用 `scripts/create_cba_project.py <新项目目录> --job <job.json> --shots <shots.csv> --court <球场.png> --portrait <头像.png> --logo <队标.png>` 一次完成已验证管线。手动执行时，按共享制作流程依次create_project、configure_video、apply_half_court、apply_scene_framing、apply_stable_camera，**随后**运行 `python scripts/apply_cba_court.py <project>`。此步骤适配地板比例、双篮间距和五区；不可在已适配项目上重新跑NBA文本替换管线，需从新项目开始。
3. `render_video.py --mode check` 后查看画面；再导出轨迹视频。所有投篮起笔/圈叉同记录、同坐标、同帧相机不变。
4. 使用 `append_cba_summary.py <project> --video <轨迹MP4> --league-shots <CBA联盟parquet> --output <最终MP4>`，不是NBA总结脚本。默认20秒＋6秒，其他视觉及总结展开规则沿用SKILL.md。
5. 成片完整解码，核对逐球、五区、10区和左右底角、同季CBA均值、双篮与真实场地比例；交付视频并说明已覆盖/缺失的真实坐标。更新本地缓存清单，不自动公开付费原始数据。
