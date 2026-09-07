# Raids E2E 逐剧本表现

**环境** GizClaw 0.16.2（build b110c39f）· E2E 集群 · 2026-09-08 · `gizclaw test run --parallel 6` · eino 31/31、flowcraft 30/30 通过。

两条路径的差别只在 RuntimeProfile 绑定；记忆驱动都是 `volc_mem0`（poll 500ms），ASR 都是 `volc-bigasr-sauc`，TTS 供应商相同：

- **eino / `h106-zero`** — 设备实际使用的 profile，30 个故事+冒险剧本外加 journey-memory-recall 全绑 eino 实现，collection `raids` / `story-teller`，每剧本单一旁白音色。该 profile 里唯一的 flowcraft 条目 murder-mystery 未在本轮测量。
- **flowcraft / `testing`** — 为对照临时建的 profile，绑同名 flowcraft 实现，collection `raidtest-targets`，每剧本多角色音色。产品当前不走这条路径。

**三种口径**（都以该轮输入推送时刻为计时起点）：

- **冷** — `server.run.workspace.reload` 预热后的第一轮，此时记忆库刚打开、图刚编译、模型与 TTS 连接均为新建。
- **温** — 同一会话后续轮次的中位数。与冷的差别是 workspace 预热状态，**不涉及记忆检索**。
- **recall** — 输入含 eino 图 `prepare-memory-query` 的关键词（重连/恢复/回忆/还记得/代号/更正/改成），因而经 `recall-memory` 节点真正查询 volc mem0。不含关键词的输入会跳过该节点，所以冷/温两列走的都是 no-recall 分支。flowcraft 一轮未测此口径。

## 配置

| 剧本 | 引擎 | Profile | Workflow | LLM | temp | max_tokens | Memory | 音色 |
|---|---|---|---|---|---|---|---|---|
| adventure-castle-mystery | eino | h106-zero | eino-adventure-castle-mystery | doubao-seed-2-0-lite-260215 | 0.5 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-castle-mystery | flowcraft | testing | flowcraft-adventure-castle-mystery | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-debate | eino | h106-zero | eino-adventure-debate | doubao-seed-2-0-lite-260215 | 0.3 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-debate | flowcraft | testing | flowcraft-adventure-debate | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-desert-island | eino | h106-zero | eino-adventure-desert-island | doubao-seed-2-0-lite-260215 | 0.3 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-desert-island | flowcraft | testing | flowcraft-adventure-desert-island | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-history | eino | h106-zero | eino-adventure-history | doubao-seed-2-0-lite-260215 | 0.3 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-history | flowcraft | testing | flowcraft-adventure-history | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-monster-maze | eino | h106-zero | eino-adventure-monster-maze | doubao-seed-2-0-lite-260215 | 0.5 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-monster-maze | flowcraft | testing | flowcraft-adventure-monster-maze | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-nature | eino | h106-zero | eino-adventure-nature | doubao-seed-2-0-lite-260215 | 0.3 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-nature | flowcraft | testing | flowcraft-adventure-nature | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-science | eino | h106-zero | eino-adventure-science | doubao-seed-2-0-lite-260215 | 0.3 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-science | flowcraft | testing | flowcraft-adventure-science | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-space-encyclopedia | eino | h106-zero | eino-adventure-space-encyclopedia | doubao-seed-2-0-lite-260215 | 0.3 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-space-encyclopedia | flowcraft | testing | flowcraft-adventure-space-encyclopedia | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-space-rescue | eino | h106-zero | eino-adventure-space-rescue | doubao-seed-2-0-lite-260215 | 0.5 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-space-rescue | flowcraft | testing | flowcraft-adventure-space-rescue | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-treasure | eino | h106-zero | eino-adventure-treasure | doubao-seed-2-0-lite-260215 | 0.3 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-treasure | flowcraft | testing | flowcraft-adventure-treasure | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-undersea-base | eino | h106-zero | eino-adventure-undersea-base | doubao-seed-2-0-lite-260215 | 0.3 | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| adventure-undersea-base | flowcraft | testing | flowcraft-adventure-undersea-base | doubao-seed-2-0-lite-260215 | — | 2048 | adventure (volc_mem0) | zh_male_changtianyi_mars_bigtts |
| journey-memory-recall | eino | h106-zero | eino-journey-memory-recall | doubao-seed-2-0-lite-260215 | — | 2048 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-aesop | eino | h106-zero | eino-story-aesop | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-aesop | flowcraft | testing | flowcraft-story-aesop | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts |
| story-alice | eino | h106-zero | eino-story-alice | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-alice | flowcraft | testing | flowcraft-story-alice | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts |
| story-animal-kingdom | eino | h106-zero | eino-story-animal-kingdom | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-animal-kingdom | flowcraft | testing | flowcraft-story-animal-kingdom | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts, zh_female_wenroushunv_uranus_bigtts |
| story-arabian-nights | eino | h106-zero | eino-story-arabian-nights | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-arabian-nights | flowcraft | testing | flowcraft-story-arabian-nights | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts |
| story-around-world-80-days | eino | h106-zero | eino-story-around-world-80-days | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-around-world-80-days | flowcraft | testing | flowcraft-story-around-world-80-days | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts |
| story-chu-han | eino | h106-zero | eino-story-chu-han | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-chu-han | flowcraft | testing | flowcraft-story-chu-han | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts |
| story-fairy-tales | eino | h106-zero | eino-story-fairy-tales | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-fairy-tales | flowcraft | testing | flowcraft-story-fairy-tales | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts, zh_female_wenroushunv_uranus_bigtts |
| story-fengshen | eino | h106-zero | eino-story-fengshen | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-fengshen | flowcraft | testing | flowcraft-story-fengshen | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts, zh_male_naiqimengwa_mars_bigtts |
| story-gulliver | eino | h106-zero | eino-story-gulliver | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-gulliver | flowcraft | testing | flowcraft-story-gulliver | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts, zh_female_wenroushunv_uranus_bigtts |
| story-journey-center-earth | eino | h106-zero | eino-story-journey-center-earth | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-journey-center-earth | flowcraft | testing | flowcraft-story-journey-center-earth | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_naiqimengwa_mars_bigtts, zh_male_changtianyi_mars_bigtts |
| story-little-prince | eino | h106-zero | eino-story-little-prince | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-little-prince | flowcraft | testing | flowcraft-story-little-prince | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_naiqimengwa_mars_bigtts, zh_female_wenroushunv_uranus_bigtts |
| story-nils | eino | h106-zero | eino-story-nils | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-nils | flowcraft | testing | flowcraft-story-nils | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_naiqimengwa_mars_bigtts |
| story-robinson-crusoe | eino | h106-zero | eino-story-robinson-crusoe | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-robinson-crusoe | flowcraft | testing | flowcraft-story-robinson-crusoe | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_changtianyi_mars_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts |
| story-shanhaijing | eino | h106-zero | eino-story-shanhaijing | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-shanhaijing | flowcraft | testing | flowcraft-story-shanhaijing | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_naiqimengwa_mars_bigtts |
| story-three-kingdoms | eino | h106-zero | eino-story-three-kingdoms | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-three-kingdoms | flowcraft | testing | flowcraft-story-three-kingdoms | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts, zh_male_changtianyi_mars_bigtts |
| story-tom-sawyer | eino | h106-zero | eino-story-tom-sawyer | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-tom-sawyer | flowcraft | testing | flowcraft-story-tom-sawyer | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_naiqimengwa_mars_bigtts |
| story-twenty-thousand-leagues | eino | h106-zero | eino-story-twenty-thousand-leagues | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-twenty-thousand-leagues | flowcraft | testing | flowcraft-story-twenty-thousand-leagues | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_changtianyi_mars_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts |
| story-water-margin | eino | h106-zero | eino-story-water-margin | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-water-margin | flowcraft | testing | flowcraft-story-water-margin | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts, zh_male_changtianyi_mars_bigtts |
| story-wizard-oz | eino | h106-zero | eino-story-wizard-oz | doubao-seed-2-0-lite-260215 | 0.2 | 1024 | story-teller (volc_mem0) | ICL_uranus_zh_male_rexueshaonian_tob |
| story-wizard-oz | flowcraft | testing | flowcraft-story-wizard-oz | doubao-seed-2-0-lite-260215 | — | 1024 | story-teller (volc_mem0) | zh_female_shaoergushi_mars_bigtts, zh_female_wenroushunv_uranus_bigtts, zh_male_jieshuoxiaoming_uranus_bigtts |

## 表现（ms）

| 剧本 | 引擎 | 首text 冷 | 首text 温 | 首text recall | 首音节 冷 | 首音节 温 | 首音节 recall | 最大下行空档 |
|---|---|---|---|---|---|---|---|---|
| adventure-castle-mystery | eino | 1215 | 1390 | 1315 | 1731 | 2083 | 1937 | 74 |
| adventure-castle-mystery | flowcraft | 2792 | 1420 | — | 3277 | 2237 | — | 133 |
| adventure-debate | eino | 975 | 1433 | 1431 | 1714 | 1918 | 2049 | 74 |
| adventure-debate | flowcraft | 1055 | 1084 | — | 1649 | 2053 | — | 133 |
| adventure-desert-island | eino | 1483 | 1449 | 1548 | 1973 | 2046 | 2276 | 34 |
| adventure-desert-island | flowcraft | 1010 | 1214 | — | 1488 | 2233 | — | 113 |
| adventure-history | eino | 1269 | 1096 | 1155 | 2013 | 1713 | 1755 | 81 |
| adventure-history | flowcraft | 3212 | 1300 | — | 3800 | 2082 | — | 78 |
| adventure-monster-maze | eino | 1367 | 1234 | 1187 | 1913 | 1988 | 1860 | 82 |
| adventure-monster-maze | flowcraft | 1205 | 1562 | — | 2029 | 2279 | — | 95 |
| adventure-nature | eino | 1437 | 1115 | 1359 | 2313 | 1866 | 2261 | 35 |
| adventure-nature | flowcraft | 1157 | 1215 | — | 1863 | 1894 | — | 95 |
| adventure-science | eino | 1178 | 1110 | 1706 | 1696 | 1897 | 2396 | 36 |
| adventure-science | flowcraft | 1457 | 1387 | — | 1954 | 2160 | — | 89 |
| adventure-space-encyclopedia | eino | 1408 | 1343 | 1370 | 1902 | 2147 | 1994 | 38 |
| adventure-space-encyclopedia | flowcraft | 2309 | 1129 | — | 2840 | 2158 | — | 87 |
| adventure-space-rescue | eino | 1314 | 1216 | 1275 | 1790 | 1953 | 2102 | 37 |
| adventure-space-rescue | flowcraft | 1691 | 1388 | — | 2286 | 2168 | — | 52 |
| adventure-treasure | eino | 1276 | 929 | 1468 | 1748 | 1639 | 2149 | 41 |
| adventure-treasure | flowcraft | 1020 | 1390 | — | 1573 | 2085 | — | 74 |
| adventure-undersea-base | eino | 1181 | 1123 | 1287 | 1838 | 1729 | 1908 | 39 |
| adventure-undersea-base | flowcraft | 1474 | 1317 | — | 2294 | 1878 | — | 632 |
| journey-memory-recall | eino | 1182 | 1311 | 1589 | 2034 | 2058 | 2243 | 44 |
| story-aesop | eino | 1215 | 1107 | 2016 | 2054 | 1819 | 2679 | 46 |
| story-aesop | flowcraft | 1489 | 1117 | — | 2141 | 1760 | — | 74 |
| story-alice | eino | 1190 | 1138 | 1947 | 1951 | 1900 | 2581 | 50 |
| story-alice | flowcraft | 1322 | 1298 | — | 2026 | 2022 | — | 128 |
| story-animal-kingdom | eino | 977 | 1429 | 1543 | 1725 | 2064 | 2249 | 1889 |
| story-animal-kingdom | flowcraft | 1050 | 1177 | — | 1746 | 1941 | — | 1499 |
| story-arabian-nights | eino | 1211 | 1395 | 1254 | 2071 | 2182 | 1889 | 726 |
| story-arabian-nights | flowcraft | 1070 | 1133 | — | 1863 | 1884 | — | 1413 |
| story-around-world-80-days | eino | 1446 | 1263 | 1278 | 2174 | 2033 | 1998 | 55 |
| story-around-world-80-days | flowcraft | 999 | 1567 | — | 1836 | 2533 | — | 893 |
| story-chu-han | eino | 1226 | 1379 | 2185 | 1851 | 2019 | 2832 | 572 |
| story-chu-han | flowcraft | 837 | 1514 | — | 1804 | 2236 | — | 61 |
| story-fairy-tales | eino | 1396 | 1206 | 1303 | 2216 | 1889 | 2053 | 82 |
| story-fairy-tales | flowcraft | 1484 | 1339 | — | 2355 | 2170 | — | 608 |
| story-fengshen | eino | 1005 | 1215 | 1616 | 1965 | 1884 | 2271 | 77 |
| story-fengshen | flowcraft | 2241 | 1199 | — | 3137 | 1918 | — | 82 |
| story-gulliver | eino | 1371 | 1252 | 1002 | 2062 | 1819 | 1735 | 848 |
| story-gulliver | flowcraft | 1280 | 1096 | — | 2183 | 1961 | — | 71 |
| story-journey-center-earth | eino | 1106 | 1230 | 1152 | 2043 | 1915 | 1945 | 1276 |
| story-journey-center-earth | flowcraft | 1578 | 1438 | — | 2556 | 2093 | — | 734 |
| story-little-prince | eino | 1337 | 1210 | 1349 | 2020 | 1866 | 2061 | 77 |
| story-little-prince | flowcraft | 1396 | 1325 | — | 2129 | 1965 | — | 855 |
| story-nils | eino | 1460 | 1363 | 1421 | 2256 | 1888 | 2008 | 679 |
| story-nils | flowcraft | 1800 | 1343 | — | 2520 | 2228 | — | 32 |
| story-robinson-crusoe | eino | 1532 | 1264 | 1158 | 2225 | 2029 | 1872 | 133 |
| story-robinson-crusoe | flowcraft | 1293 | 1056 | — | 1972 | 1750 | — | 660 |
| story-shanhaijing | eino | 1493 | 1210 | 1360 | 2595 | 1849 | 2061 | 1481 |
| story-shanhaijing | flowcraft | 1716 | 1334 | — | 2348 | 2057 | — | 1252 |
| story-three-kingdoms | eino | 1497 | 1341 | 1608 | 2449 | 2175 | 2268 | 47 |
| story-three-kingdoms | flowcraft | 1167 | 1652 | — | 1890 | 2540 | — | 39 |
| story-tom-sawyer | eino | 1267 | 1275 | 1370 | 2276 | 1950 | 1970 | 130 |
| story-tom-sawyer | flowcraft | 1935 | 1229 | — | 2765 | 2032 | — | 50 |
| story-twenty-thousand-leagues | eino | 1125 | 873 | 1113 | 1871 | 1688 | 1886 | 841 |
| story-twenty-thousand-leagues | flowcraft | 1799 | 1279 | — | 3117 | 2388 | — | 112 |
| story-water-margin | eino | 928 | 1005 | 1141 | 1771 | 1636 | 1939 | 102 |
| story-water-margin | flowcraft | 1755 | 1476 | — | 2464 | 2336 | — | 654 |
| story-wizard-oz | eino | 1248 | 1234 | 1238 | 1861 | 2082 | 1991 | 78 |
| story-wizard-oz | flowcraft | 1274 | 1344 | — | 2049 | 2087 | — | 89 |

## 汇总（中位数 / 最小 / 最大 ms）

| 指标 | eino (h106-zero) | flowcraft (testing) |
|---|---|---|
| 首 text 冷 | 1267 / 928 / 1532 (n=31) | 1426 / 837 / 3212 (n=30) |
| 首 text 温 | 1234 / 873 / 1449 (n=31) | 1321 / 1056 / 1652 (n=30) |
| 首 text recall | 1359 / 1002 / 2185 (n=31) | — |
| 首音节 冷 | 1973 / 1696 / 2595 (n=31) | 2135 / 1488 / 3800 (n=30) |
| 首音节 温 | 1915 / 1636 / 2182 (n=31) | 2086 / 1750 / 2540 (n=30) |
| 首音节 recall | 2049 / 1735 / 2832 (n=31) | — |

走 volc mem0 检索相对不检索的净代价：首 text 中位 +82ms，首音节 中位 +109ms。

**下行音频**：包间隔 p95 ≈17ms（20ms 一包），`receive_span == target_span`，无实际丢包。但部分回合出现一次 0.5–1.6s 的到达空档，超过客户端约 1.6–1.9s 的领先缓冲即欠载：eino 约 5% 的回合，flowcraft 约 11%。并发 6/12/20 下比例不变，故非负载所致；出问题的都是 500 包以上的长回合。

