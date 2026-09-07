# Raids E2E 逐剧本表现

**环境** GizClaw 0.16.2（build b110c39f）· E2E 集群 · 2026-09-08 · `gizclaw test run --parallel 6` · eino 31/31、flowcraft 30/30 通过。

两条路径的差别只在 RuntimeProfile 绑定；记忆驱动都是 `volc_mem0`，ASR 都是 `volc-bigasr-sauc`，TTS 供应商相同：

- **eino / `h106-zero`** — 设备实际使用的 profile，30 个故事+冒险剧本外加 journey-memory-recall 全绑 eino 实现，每剧本单一旁白音色。该 profile 里唯一的 flowcraft 条目 murder-mystery 未在本轮测量。
- **flowcraft / `testing`** — 绑同名 flowcraft 实现并提供其角色音色槽位的 profile，每剧本多角色音色。产品当前不走这条路径。

**三种口径**（都以该轮输入推送时刻为计时起点，两个引擎均已测量）：

- **冷** — `server.run.workspace.reload` 预热后的第一轮，此时记忆库刚打开、图刚编译、模型与 TTS 连接均为新建。
- **温** — 同一会话后续轮次的中位数。与冷的差别是 workspace 预热状态，不涉及记忆检索。
- **recall** — 输入含关键词（重连/恢复/回忆/还记得/代号/更正/改成），因而真正查询 volc mem0。eino 的判定在图节点 `prepare-memory-query`，flowcraft 在 `route-recall`；不含关键词的输入两者都会跳过检索节点，所以冷/温两列走的都是 no-recall 分支。

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
| adventure-castle-mystery | flowcraft | 1107 | 1790 | 1570 | 1633 | 2902 | 2155 | 37 |
| adventure-debate | eino | 975 | 1433 | 1431 | 1714 | 1918 | 2049 | 74 |
| adventure-debate | flowcraft | 1514 | 1481 | 1365 | 2158 | 2123 | 2066 | 63 |
| adventure-desert-island | eino | 1483 | 1449 | 1548 | 1973 | 2046 | 2276 | 34 |
| adventure-desert-island | flowcraft | 1159 | 1563 | 1385 | 1701 | 2282 | 1970 | 63 |
| adventure-history | eino | 1269 | 1096 | 1155 | 2013 | 1713 | 1755 | 81 |
| adventure-history | flowcraft | 1140 | 1164 | 1418 | 1712 | 1936 | 2131 | 91 |
| adventure-monster-maze | eino | 1367 | 1234 | 1187 | 1913 | 1988 | 1860 | 82 |
| adventure-monster-maze | flowcraft | 1278 | 1468 | 1495 | 1889 | 2185 | 2180 | 63 |
| adventure-nature | eino | 1437 | 1115 | 1359 | 2313 | 1866 | 2261 | 35 |
| adventure-nature | flowcraft | 1097 | 1085 | 1236 | 1686 | 1732 | 1870 | 64 |
| adventure-science | eino | 1178 | 1110 | 1706 | 1696 | 1897 | 2396 | 36 |
| adventure-science | flowcraft | 1328 | 1122 | 974 | 2175 | 1781 | 1592 | 46 |
| adventure-space-encyclopedia | eino | 1408 | 1343 | 1370 | 1902 | 2147 | 1994 | 38 |
| adventure-space-encyclopedia | flowcraft | 1592 | 1137 | 1088 | 2107 | 1763 | 1733 | 36 |
| adventure-space-rescue | eino | 1314 | 1216 | 1275 | 1790 | 1953 | 2102 | 37 |
| adventure-space-rescue | flowcraft | 1359 | 1377 | 1412 | 1890 | 2163 | 2175 | 68 |
| adventure-treasure | eino | 1276 | 929 | 1468 | 1748 | 1639 | 2149 | 41 |
| adventure-treasure | flowcraft | 898 | 1092 | 1605 | 1473 | 1778 | 2221 | 36 |
| adventure-undersea-base | eino | 1181 | 1123 | 1287 | 1838 | 1729 | 1908 | 39 |
| adventure-undersea-base | flowcraft | 1276 | 1267 | 1401 | 2201 | 1910 | 2254 | 890 |
| journey-memory-recall | eino | 1182 | 1311 | 1589 | 2034 | 2058 | 2243 | 44 |
| story-aesop | eino | 1215 | 1107 | 2016 | 2054 | 1819 | 2679 | 46 |
| story-aesop | flowcraft | 1043 | 1162 | 1551 | 1803 | 1807 | 2255 | 92 |
| story-alice | eino | 1190 | 1138 | 1947 | 1951 | 1900 | 2581 | 50 |
| story-alice | flowcraft | 1549 | 1511 | 1309 | 2347 | 2328 | 1994 | 821 |
| story-animal-kingdom | eino | 977 | 1429 | 1543 | 1725 | 2064 | 2249 | 1889 |
| story-animal-kingdom | flowcraft | 1365 | 1454 | 1460 | 2014 | 2062 | 2066 | 95 |
| story-arabian-nights | eino | 1211 | 1395 | 1254 | 2071 | 2182 | 1889 | 726 |
| story-arabian-nights | flowcraft | 1014 | 1206 | 1312 | 1694 | 1971 | 2193 | 94 |
| story-around-world-80-days | eino | 1446 | 1263 | 1278 | 2174 | 2033 | 1998 | 55 |
| story-around-world-80-days | flowcraft | 1805 | 1341 | 1415 | 2447 | 1923 | 2111 | 84 |
| story-chu-han | eino | 1226 | 1379 | 2185 | 1851 | 2019 | 2832 | 572 |
| story-chu-han | flowcraft | 1022 | 1195 | 1474 | 1718 | 1848 | 2128 | 771 |
| story-fairy-tales | eino | 1396 | 1206 | 1303 | 2216 | 1889 | 2053 | 82 |
| story-fairy-tales | flowcraft | 1117 | 1452 | 1649 | 1906 | 2307 | 2392 | 957 |
| story-fengshen | eino | 1005 | 1215 | 1616 | 1965 | 1884 | 2271 | 77 |
| story-fengshen | flowcraft | 1441 | 1477 | 1800 | 2392 | 2173 | 2460 | 40 |
| story-gulliver | eino | 1371 | 1252 | 1002 | 2062 | 1819 | 1735 | 848 |
| story-gulliver | flowcraft | 1431 | 1287 | 1395 | 2338 | 2185 | 2138 | 75 |
| story-journey-center-earth | eino | 1106 | 1230 | 1152 | 2043 | 1915 | 1945 | 1276 |
| story-journey-center-earth | flowcraft | 1149 | 1189 | 1153 | 1885 | 1994 | 1736 | 1711 |
| story-little-prince | eino | 1337 | 1210 | 1349 | 2020 | 1866 | 2061 | 77 |
| story-little-prince | flowcraft | 1189 | 1105 | 2106 | 1964 | 1951 | 2797 | 802 |
| story-nils | eino | 1460 | 1363 | 1421 | 2256 | 1888 | 2008 | 679 |
| story-nils | flowcraft | 1297 | 1350 | 1348 | 1972 | 2286 | 1985 | 765 |
| story-robinson-crusoe | eino | 1532 | 1264 | 1158 | 2225 | 2029 | 1872 | 133 |
| story-robinson-crusoe | flowcraft | 1429 | 1372 | 1207 | 2074 | 2093 | 1884 | 75 |
| story-shanhaijing | eino | 1493 | 1210 | 1360 | 2595 | 1849 | 2061 | 1481 |
| story-shanhaijing | flowcraft | 1518 | 1416 | 1337 | 2215 | 2204 | 2115 | 1773 |
| story-three-kingdoms | eino | 1497 | 1341 | 1608 | 2449 | 2175 | 2268 | 47 |
| story-three-kingdoms | flowcraft | 1124 | 1389 | 1418 | 1856 | 2157 | 2115 | 711 |
| story-tom-sawyer | eino | 1267 | 1275 | 1370 | 2276 | 1950 | 1970 | 130 |
| story-tom-sawyer | flowcraft | 1267 | 1104 | 1406 | 1925 | 1804 | 2052 | 1286 |
| story-twenty-thousand-leagues | eino | 1125 | 873 | 1113 | 1871 | 1688 | 1886 | 841 |
| story-twenty-thousand-leagues | flowcraft | 995 | 1168 | 1448 | 2009 | 2027 | 2052 | 899 |
| story-water-margin | eino | 928 | 1005 | 1141 | 1771 | 1636 | 1939 | 102 |
| story-water-margin | flowcraft | 1414 | 1220 | 1204 | 2101 | 1830 | 1816 | 847 |
| story-wizard-oz | eino | 1248 | 1234 | 1238 | 1861 | 2082 | 1991 | 78 |
| story-wizard-oz | flowcraft | 1034 | 1249 | 2275 | 1671 | 1772 | 2862 | 111 |

## 汇总（中位数 / 最小 / 最大 ms）

偶数个样本的中位数取排序后中间两个值的平均，再截断为整毫秒。

| 指标 | eino (h106-zero) | flowcraft (testing) |
|---|---|---|
| 首 text 冷 | 1267 / 928 / 1532 (n=31) | 1271 / 898 / 1805 (n=30) |
| 首 text 温 | 1234 / 873 / 1449 (n=31) | 1277 / 1085 / 1790 (n=30) |
| 首 text recall | 1359 / 1002 / 2185 (n=31) | 1409 / 974 / 2275 (n=30) |
| 首音节 冷 | 1973 / 1696 / 2595 (n=31) | 1944 / 1473 / 2447 (n=30) |
| 首音节 温 | 1915 / 1636 / 2182 (n=31) | 2010 / 1732 / 2902 (n=30) |
| 首音节 recall | 2049 / 1735 / 2832 (n=31) | 2115 / 1592 / 2862 (n=30) |

走 volc mem0 检索相对不检索的净代价（中位数）：eino 首 text +125ms、首音节 +134ms；flowcraft 首 text +132ms、首音节 +105ms。

**下行音频**：包间隔 p95 ≈17ms（20ms 一包），`receive_span == target_span`，无实际丢包。但部分回合出现一次 0.5–1.6s 的到达空档，超过客户端约 1.6–1.9s 的领先缓冲即欠载：eino 约 5% 的回合，flowcraft 约 11%。并发 6/12/20 下比例不变，故非负载所致；出问题的都是 500 包以上的长回合。

