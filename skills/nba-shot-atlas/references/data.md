# 数据、名字和赛季

## 数据源

主要缓存为 sportsdataverse/sportsdataverse-data 的 `nba_stats_shots` 与 `nba_stats_schedules` GitHub release。脚本每次读发布清单，不用猜文件名。2026-10-15核验到shots_1997.parquet至shots_2026.parquet，即1996–97至2025–26；这是当时清单，不是永久上限。

- https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_shots
- https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_schedules

```sh
python scripts/fetch_data.py --cache <缓存目录> --list-seasons --refresh
python scripts/fetch_data.py --person-id 893 --years 1998 --cache <缓存目录> --output <项目>/shots.csv
python scripts/fetch_data.py --person-id 893 --years all --cache <缓存目录> --output <项目>/shots.csv
```

`all`逐年过滤同一NBA person_id，保留实际有出手年份；输出coverage.json。可复用本机已有parquet，文件命名按发布清单。无记录不自动等于该球员未上场，应对照生涯/比赛日志区分无参赛、无出手与缺失。未覆盖赛季必须明确列出。参考独立赛季统计核对总出手、命中和比赛数，不能只把同一数据源的两个字段相加当完整性证据。

**NBA此源season_type_id：2=常规赛，4=季后赛；3是全明星，不能误当季后赛。** 季前赛不混入默认成片。`season`是结束年份；球员可交易，同季可能多个team_id。game_id保留前导零。

## 名字与选择

`assets/players.json` 是常见中文/英文/繁体别名与NBA ID对应表，非全联盟名册。脚本对英文做大小写、空格、标点、重音规范化；不做危险的模糊自动匹配。比如库里/Stephen Curry/Steph Curry→201939，乔丹/Michael Jordan→893。其他名字从官方NBA球员页、历史赛季名册核验再加别名，不能根据投篮源只含姓氏的player_name串人。

只有名字时用用户输入工具提供赛季选择，示例：

> 你想做迈克尔·乔丹的哪个赛季？数据库可覆盖1996–97、1997–98、2001–02、2002–03，或全部可用赛季（1996年前不包含）。

不要在给出选项前把“1997–98是最经典”当成用户的选择。若用户选全部，按覆盖清单获取；若给单季，检查有无该球员数据后继续。

全部赛季须保留season、game_date、game_id、phase、team_id，按日期→比赛→节次→剩余时间倒序排列。总计为所有选中年份的逐球总和。跨队生涯未指定球场时，可用出手最多球队的主场作为统一展示场景并告知；不能声称这代表每个年份的实际主场。

## 规范输入

CSV至少含game_id、game_date、season、season_type_id、period、clock、person_id、shot_result、shot_value、x_legacy、y_legacy、game_number；推荐保留team_id、team_tricode、description。Made/Missed区分结果，shot_value只允许2/3，罚球不算出手。

本NBA源x_legacy/y_legacy为十分之一英尺，模板世界坐标为(-x_legacy/10,y_legacy/10,0.045)，篮圈(0,0,10)，远端篮圈y=83.5。其他数据源必须重新校准原点、轴向、单位，不能直接套NBA比例。

五区几何规则见模板zones.py：篮下4ft半径；短两分为剩余|x|≤8且y≤13.75；其他两分为长两分；三分中|x|≥22且y≤9.2为合并底角；其他为弧顶及侧翼。此为几何重建，非NBA官方SHOT_ZONE_BASIC；有可靠官方分区时可用官方值并记录口径。

重复坐标不打散、不随机抖动、不删记录。乔丹样本2419次中有513个(0,0)，可能为历史近筐精度限制，必须保留并说明；示意飞行弧高和速度不是实测。缺坐标的出手单独报告，不能编点凑数。

CBA暂不自动进入本skill。已验证网站样本有shotX/shotY，但是另一套归一化坐标；跨接口时间匹配与历史完整性尚不能承诺，需单独验证后开发适配器。
