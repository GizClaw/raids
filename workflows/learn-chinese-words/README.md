# Chinese Word Treasury (`learn-chinese-words`) — 语文积累

Explore verified primary Chinese textbook treasures through proverb and two-part-allegorical-saying riddles, quotation attributions, couplets, and character stories.

- Category: `learn`; rating: `6+`; tags: `learn`, `chinese`, `proverbs`, `characters`, `curriculum`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-chinese-words` | eino | learner | `eino-learn-chinese-words.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-chinese-words` | flowcraft | learner | `flowcraft-learn-chinese-words.model` | `flowcraft-learn-chinese-words.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-chinese-words --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This single all-grades raid covers 统编版小学语文一至六年级. Its prompt embeds
checked proverbs, 歇后语, quotations, 对子/对联, and character stories from
语文园地·日积月累 and 识字课, about 5149 characters in total. Spoken
cards omit URLs, page numbers, and research notes. Exact duplicate spoken lines
are removed without changing the normalized research record.

[`knowledge.json`](knowledge.json) is the normalized source of truth and retains
all placement, source, dispute, work, note, 字源, and unverified fields from the
research input. 统编版小学语文；修订版（根据2022年版课程标准修订）用于一至三年级上下册和四至六年级上册，四至六年级下册为平台现行版本。内容来自语文园地·日积月累和识字课。

## 谚语

| Text | Meaning | Placement | Sources |
| --- | --- | --- | --- |
| 一年之计在于春，一日之计在于晨。 | 春天和早晨是打基础的好时光 | 一年级上册；语文园地五·日积月累；第69页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/74.jpg) |
| 一寸光阴一寸金，寸金难买寸光阴。 | 时间宝贵，用钱也买不回 | 一年级上册；语文园地五·日积月累；第69页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/74.jpg) |
| 站如松，坐如钟。行如风，卧如弓。 | 站坐走睡都要有好姿势 | 一年级上册；识字3《口耳目手足》；第12页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/17.jpg) |
| 种瓜得瓜，种豆得豆。 | 做什么事，就得什么结果 | 一年级上册；语文园地七·日积月累；第91页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/96.jpg) |
| 前人栽树，后人乘凉。 | 前人辛苦付出，后人得到好处 | 一年级上册；语文园地七·日积月累；第91页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/96.jpg) |
| 千里之行，始于足下。 | 再远的路也要从第一步走起 | 一年级上册；语文园地七·日积月累；第91页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/96.jpg) |
| 百尺竿头，更进一步。 | 已经很好了，还要再努力 | 一年级上册；语文园地七·日积月累；第91页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/96.jpg) |
| 朝霞不出门，晚霞行千里。 | 早上有霞可能下雨，傍晚有霞多晴 | 一年级下册；语文园地六·日积月累；第75页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/80.jpg) |
| 有雨山戴帽，无雨半山腰。 | 云盖山顶要下雨，云在山腰不下 | 一年级下册；语文园地六·日积月累；第75页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/80.jpg) |
| 早晨下雨当日晴，晚上下雨到天明。 | 早雨白天会晴，夜雨下到天亮 | 一年级下册；语文园地六·日积月累；第75页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/80.jpg) |
| 蚂蚁搬家蛇过道，大雨不久要来到。 | 蚂蚁搬家、蛇出洞，大雨快来了 | 一年级下册；语文园地六·日积月累；第75页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/80.jpg) |
| 十年树木，百年树人。 | 培养一个人要花很长时间 | 二年级上册；识字2《树之歌》课后·读一读，记一记；第19页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/24.jpg) |
| 树无根不长，人无志不立。 | 人没有志向就立不住 | 二年级上册；识字2《树之歌》课后·读一读，记一记；第19页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/24.jpg) |
| 一九二九不出手，三九四九冰上走，五九六九，沿河看柳，七九河开，八九雁来，九九加一九，耕牛遍地走。 | 数九：冬天到春天的天气变化 | 二年级上册；语文园地二·日积月累《数九歌》；第26页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/31.jpg) |
| 一日读书一日功，一日不读十日空。 | 天天读书才有收获 | 二年级上册；语文园地五·日积月累；第65页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/70.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/141.jpg) |
| 予人玫瑰，手有余香。 | 帮助别人，自己也快乐 | 二年级下册；语文园地二·日积月累；第25页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/30.jpg) |
| 平时肯帮人，急时有人帮。 | 常帮别人，有难时别人也帮你 | 二年级下册；语文园地二·日积月累；第25页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/30.jpg) |
| 与其锦上添花，不如雪中送炭。 | 在别人最难时帮忙最可贵 | 二年级下册；语文园地二·日积月累；第25页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/30.jpg) |
| 春雨惊春清谷天，夏满芒夏暑相连。秋处露秋寒霜降，冬雪雪冬小大寒。 | 每字代表一个节气，共二十四个 | 二年级下册；语文园地六·日积月累《二十四节气歌》；第80页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/85.jpg) |
| 人心齐，泰山移。 | 大家一条心，力量大无比 | 三年级上册；语文园地四·日积月累；第56页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/61.jpg) |
| 二人同心，其利断金。 | 两人齐心，力量能切断金属 | 三年级上册；语文园地四·日积月累；第56页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/61.jpg) |
| 三个臭皮匠，顶个诸葛亮。 | 大家一起想办法，胜过聪明人 | 三年级上册；语文园地四·日积月累；第56页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/61.jpg) |
| 兵来将挡，水来土掩。 | 遇到什么问题就想办法应对 | 三年级下册；语文园地八·日积月累；第110页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/115.jpg) |
| 不入虎穴，焉得虎子。 | 不冒险就难以成功 | 三年级下册；语文园地八·日积月累；第110页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/115.jpg) |
| 眼见为实，耳听为虚。 | 亲眼看到的比听说的可靠 | 三年级下册；语文园地八·日积月累；第110页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/115.jpg) |
| 近朱者赤，近墨者黑。 | 常和什么人在一起就会受影响 | 三年级下册；语文园地八·日积月累；第110页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/115.jpg) |
| 立了秋，把扇丢。 | 立秋后天凉，不用扇子了 | 四年级上册；语文园地三·日积月累；第46页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/51.jpg) |
| 二八月，乱穿衣。 | 农历二月八月冷热多变 | 四年级上册；语文园地三·日积月累；第46页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/51.jpg) |
| 一场秋雨一场寒，十场秋雨要穿棉。 | 秋雨一场场，天一天天变冷 | 四年级上册；语文园地三·日积月累；第46页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/51.jpg) |
| 八月里来雁门开，雁儿脚上带霜来。 | 大雁南飞时，霜也快来了 | 四年级上册；语文园地三·日积月累；第46页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/51.jpg) |
| 尺有所短，寸有所长。 | 人和物各有长处和短处 | 四年级上册；语文园地七·日积月累；第106页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/111.jpg) |
| 一言既出，驷马难追。 | 话说出口就要算数 | 四年级上册；语文园地七·日积月累；第106页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/111.jpg) |
| 差之毫厘，谬以千里。 | 开始差一点，结果差很远 | 四年级上册；语文园地七·日积月累；第106页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/111.jpg) |
| 少年不知勤学苦，老来方知读书迟。 | 小时不勤学，老了才后悔 | 四年级下册；语文园地八·日积月累；第136页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/141.jpg) |
| 莫道君行早，更有早行人。 | 别以为自己最早，还有更早的 | 六年级下册；语文园地二·日积月累；第40页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/45.jpg) |
| 路遥知马力，日久见人心。 | 时间长了才看出人好坏 | 六年级下册；语文园地二·日积月累；第40页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/45.jpg) |
| 听君一席话，胜读十年书。 | 听了你的话，收获特别大 | 六年级下册；语文园地二·日积月累；第40页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/45.jpg) |
| 有意栽花花不发，无心插柳柳成荫。 | 用心做的未必成，随手做的却成了 | 六年级下册；语文园地四·日积月累；第78页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/83.jpg) |
| 书到用时方恨少，事非经过不知难。 | 要用时才觉得书读少了 | 六年级下册；语文园地四·日积月累；第78页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/83.jpg) |
| 良药苦口利于病，忠言逆耳利于行。 | 批评的话难听，却对人有益 | 六年级下册；语文园地四·日积月累；第78页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/83.jpg) |
## 歇后语

| Front | Back | Meaning | Placement | Sources |
| --- | --- | --- | --- | --- |
| 芝麻开花 | 节节高 | 一步比一步好 | 一年级下册；语文园地五·日积月累；第57页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/62.jpg) |
| 竹篮打水 | 一场空 | 白费力气，什么也没得到 | 一年级下册；语文园地五·日积月累；第57页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/62.jpg) |
| 十五个吊桶打水 | 七上八下 | 心里慌乱不安 | 一年级下册；语文园地五·日积月累；第57页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/62.jpg) |
## 名言

| Text | Textbook attribution | Work | Meaning | Dispute | Placement | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 不知则问，不能则学。 | 《荀子》 | 《荀子·非十二子》 | 不懂就问，不会就学 | - | 一年级下册；语文园地七·日积月累；第94页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/99.jpg) [2](https://zh.wikisource.org/wiki/%E8%8D%80%E5%AD%90/%E9%9D%9E%E5%8D%81%E4%BA%8C%E5%AD%90%E7%AF%87) |
| 读万卷书，行万里路。 | 董其昌 | - | 多读书，也要多出去见识 | - | 一年级下册；语文园地七·日积月累；第94页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/99.jpg) |
| 读书破万卷，下笔如有神。 | 杜甫 | 《奉赠韦左丞丈二十二韵》 | 书读得多，写作就流畅 | - | 一年级下册；语文园地七·日积月累；第94页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/99.jpg) [2](https://zh.wikisource.org/wiki/%E5%A5%89%E8%B4%88%E9%9F%8B%E5%B7%A6%E4%B8%9E%E4%B8%88%E4%BA%8C%E5%8D%81%E4%BA%8C%E9%9F%BB) |
| 黑发不知勤学早，白首方悔读书迟。 | 教材未署作者 | - | 年轻不勤学，老了才后悔 | 网上常说是颜真卿《劝学》，本卡未找到可靠早期出处；讲作者时只说“教材没写作者”。 | 二年级上册；语文园地五·日积月累；第65页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/70.jpg) [2](https://www.gushiwen.cn/mingju_1115.aspx) |
| 书山有路勤为径，学海无涯苦作舟。 | 教材未署作者 | - | 勤奋和吃苦是学习的路和船 | 常被说成韩愈所作，但韩愈作品里没有这两句，属后人托名；作者不详。 | 二年级上册；语文园地五·日积月累；第65页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/70.jpg) [2](https://zhuanlan.zhihu.com/p/1963559756250743049) [3](https://www.zhihu.com/question/55946205) |
| 有志者事竟成。 | 《后汉书》 | 《后汉书·耿弇传》（卷十九） | 有志向的人终能成功 | - | 二年级上册；语文园地六·日积月累；第79页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/84.jpg) [2](https://zh.wikisource.org/wiki/%E5%BE%8C%E6%BC%A2%E6%9B%B8/%E5%8D%B719) |
| 志当存高远。 | 诸葛亮 | 《诫外甥书》 | 志向要远大 | - | 二年级上册；语文园地六·日积月累；第79页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/84.jpg) [2](https://zh.wikisource.org/wiki/%E8%AA%A1%E5%A4%96%E7%94%A5%E6%9B%B8) |
| 穷且益坚，不坠青云之志。 | 王勃 | - | 处境越难越坚定，不丢大志向 | - | 二年级上册；语文园地六·日积月累；第79页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/84.jpg) |
| 己所不欲，勿施于人。 | 《论语》 | 《论语·颜渊》 | 自己不想要的，别强加给别人 | - | 二年级上册；语文园地八·日积月累；第105页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/110.jpg) [2](https://zh.wikisource.org/wiki/%E8%AB%96%E8%AA%9E/%E9%A1%8F%E6%B7%B5%E7%AC%AC%E5%8D%81%E4%BA%8C) |
| 与朋友交，言而有信。 | 《论语》 | 《论语·学而》 | 和朋友交往要说话算数 | 这句是孔子的学生子夏说的，不是孔子本人说的。 | 二年级上册；语文园地八·日积月累；第105页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/110.jpg) [2](https://zh.wikisource.org/wiki/%E8%AB%96%E8%AA%9E/%E5%AD%B8%E8%80%8C%E7%AC%AC%E4%B8%80) |
| 不以规矩，不能成方圆。 | 《孟子》 | 《孟子·离娄上》 | 做事要守规则 | - | 二年级上册；语文园地八·日积月累；第105页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/110.jpg) [2](https://zh.wikisource.org/wiki/%E5%AD%9F%E5%AD%90/%E9%9B%A2%E5%A9%81%E4%B8%8A) |
| 失信不立。 | 《左传》 | 《左传·襄公》 | 不讲信用就立不住脚 | - | 二年级下册；语文园地四·日积月累；第52页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/57.jpg) [2](https://zh.wikisource.org/wiki/%E6%98%A5%E7%A7%8B%E5%B7%A6%E6%B0%8F%E5%82%B3/%E8%A5%84%E5%85%AC) |
| 诚信者，天下之结也。 | 《管子》 | - | 诚信是连结天下人的纽带 | - | 二年级下册；语文园地四·日积月累；第52页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/57.jpg) |
| 小信成则大信立。 | 《韩非子》 | 《韩非子·外储说左上》 | 小事守信，才能赢得大信任 | - | 二年级下册；语文园地四·日积月累；第52页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/57.jpg) [2](https://zh.wikisource.org/wiki/%E9%9F%93%E9%9D%9E%E5%AD%90/%E5%A4%96%E5%84%B2%E8%AA%AA%E5%B7%A6%E4%B8%8A) |
| 仁者爱人，有礼者敬人。 | 《孟子》 | 《孟子·离娄下》 | 仁爱的人爱别人，有礼的人尊重人 | - | 三年级上册；语文园地三·日积月累；第44页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/49.jpg) [2](https://zh.wikisource.org/wiki/%E5%AD%9F%E5%AD%90/%E9%9B%A2%E5%A9%81%E4%B8%8B) |
| 与人善言，暖于布帛；伤人以言，深于矛戟。 | 《荀子》 | - | 好话暖人心，恶语比刀伤人深 | - | 三年级上册；语文园地三·日积月累；第44页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/49.jpg) |
| 士不可以不弘毅，任重而道远。 | 《论语》 | 《论语·泰伯》 | 读书人要胸怀宽、意志坚 | 这句是曾子说的，不是孔子本人说的。 | 三年级上册；语文园地八·日积月累；第108页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/113.jpg) [2](https://zh.wikisource.org/wiki/%E8%AB%96%E8%AA%9E/%E6%B3%B0%E4%BC%AF%E7%AC%AC%E5%85%AB) |
| 锲而舍之，朽木不折；锲而不舍，金石可镂。 | 《荀子》 | 《荀子·劝学》 | 坚持不放弃，金石也能刻穿 | - | 三年级上册；语文园地八·日积月累；第108页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/113.jpg) [2](https://zh.wikisource.org/wiki/%E8%8D%80%E5%AD%90/%E5%8B%B8%E5%AD%B8%E7%AF%87) |
| 人谁无过？过而能改，善莫大焉。 | 《左传》 | 《左传·宣公二年》 | 谁都会犯错，改了就是好事 | - | 三年级下册；语文园地六·日积月累；第82页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/87.jpg) [2](https://zh.wikisource.org/wiki/%E6%98%A5%E7%A7%8B%E5%B7%A6%E6%B0%8F%E5%82%B3/%E5%AE%A3%E5%85%AC) |
| 人非生而知之者，孰能无惑？ | 韩愈 | 《师说》 | 没人天生就懂，谁都有疑问 | - | 四年级上册；语文园地二·日积月累；第32页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/37.jpg) [2](https://zh.wikisource.org/wiki/%E5%B8%AB%E8%AA%AA) |
| 善疑者，不疑人之所疑，而疑人之所不疑。 | 方以智 | 《东西均》 | 会提问的人能在没人怀疑处发现问题 | - | 四年级上册；语文园地二·日积月累；第32页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/37.jpg) [2](https://zh.wikisource.org/wiki/%E6%9D%B1%E8%A5%BF%E5%9D%87) |
| 天行健，君子以自强不息。 | 《周易》 | 《周易·乾》 | 像天运行不停一样，永远努力 | - | 四年级下册；语文园地七·日积月累；第120页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/125.jpg) [2](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93/%E4%B9%BE) |
| 生于忧患而死于安乐。 | 《孟子》 | 《孟子·告子下》 | 忧患使人奋发，安乐使人衰败 | - | 四年级下册；语文园地七·日积月累；第120页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/125.jpg) [2](https://zh.wikisource.org/wiki/%E5%AD%9F%E5%AD%90/%E5%91%8A%E5%AD%90%E4%B8%8B) |
| 盛年不重来，一日难再晨。及时当勉励，岁月不待人。 | 陶渊明 | 《杂诗》 | 青春不再来，要抓紧时间努力 | - | 五年级上册；语文园地二·日积月累；第32页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/37.jpg) [2](https://zh.wikisource.org/wiki/%E9%9B%9C%E8%A9%A9%20%28%E9%99%B6%E6%B7%B5%E6%98%8E%29) |
| 莫等闲，白了少年头，空悲切。 | 岳飞 | 《满江红》 | 别虚度青春，老了空后悔 | 教材署岳飞；但《满江红》是否岳飞所作，学界自余嘉锡、夏承焘以来一直有争议，尚无定论。 | 五年级上册；语文园地二·日积月累；第32页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/37.jpg) [2](https://www.chinawriter.com.cn/n1/2023/0129/c442005-32613628.html) [3](https://www.thepaper.cn/newsDetail_forward_1396387) |
| 君子坦荡荡，小人长戚戚。 | 《论语》 | 《论语·述而》 | 君子心胸宽，小人常忧愁 | - | 五年级下册；语文园地八·日积月累；第118页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/123.jpg) [2](https://zh.wikisource.org/wiki/%E8%AB%96%E8%AA%9E/%E8%BF%B0%E8%80%8C%E7%AC%AC%E4%B8%83) |
| 多行不义，必自毙。 | 《左传》 | 《左传·隐公元年》 | 坏事做多了，必然自取灭亡 | - | 五年级下册；语文园地八·日积月累；第118页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/123.jpg) [2](https://zh.wikisource.org/wiki/%E6%98%A5%E7%A7%8B%E5%B7%A6%E6%B0%8F%E5%82%B3/%E9%9A%B1%E5%85%AC) |
| 位卑未敢忘忧国。 | 陆游 | 《病起书怀》 | 地位再低也不忘关心国家 | - | 六年级上册；语文园地二·日积月累；第30页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/%E7%97%85%E8%B5%B7%E6%9B%B8%E6%87%B7) |
| 其实地上本没有路，走的人多了，也便成了路。 | 鲁迅 | 《故乡》 | 路是人走出来的，要敢开拓 | - | 六年级上册；语文园地八·日积月累；第125页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/130.jpg) |
| 青，取之于蓝，而青于蓝。 | 《荀子》 | 《荀子·劝学》 | 学生可以超过老师 | - | 六年级下册；语文园地五·日积月累；第96页；现行版(旧版) | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/101.jpg) [2](https://zh.wikisource.org/wiki/%E8%8D%80%E5%AD%90/%E5%8B%B8%E5%AD%B8%E7%AF%87) |
## 对子与对联

| Text | Type | Placement | Sources |
| --- | --- | --- | --- |
| 云对雨，雪对风。花对树，鸟对虫。山清对水秀，柳绿对桃红。 | 对韵歌 | 一年级上册；识字5《对韵歌》；第73页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/78.jpg) |
| 古对今，圆对方。严寒对酷暑，春暖对秋凉。晨对暮，雪对霜。和风对细雨，朝霞对夕阳。桃对李，柳对杨。莺歌对燕舞，鸟语对花香。 | 对韵歌 | 一年级下册；识字6《古对今》；第50页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/55.jpg) |
| 有山皆图画，无水不文章。 | 对联 | 二年级上册；语文园地四·日积月累；第51页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/56.jpg) |
| 白马西风塞上，杏花烟雨江南。 | 对联 | 二年级上册；语文园地四·日积月累；第51页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/56.jpg) |
| 清风明月本无价，近水远山皆有情。 | 对联 | 二年级上册；语文园地四·日积月累；第51页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/56.jpg) |
| 雾锁山头山锁雾，天连水尾水连天。 | 对联（回文） | 二年级上册；语文园地四·日积月累；第51页；修订版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/56.jpg) |
## 汉字小故事

| Character | Form | Ancient form | Story | Label | Placement | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 日 | 象形 | 甲骨文是个圆圈像太阳，中间一点或一横表示太阳的光。 | - | 史实 | 一年级上册；识字4《日月山川》；第13页；修订版 | [1](https://www.zdic.net/hans/%E6%97%A5) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/18.jpg) |
| 月 | 象形 | 古字像一弯半个月亮，《说文》说像月亮不圆满的样子。 | - | 史实 | 一年级上册；识字4《日月山川》；第13页；修订版 | [1](https://www.zdic.net/hans/%E6%9C%88) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/18.jpg) |
| 山 | 象形 | 古字像几座山峰并排立在一起。 | - | 史实 | 一年级上册；识字4《日月山川》；第13页；修订版 | [1](https://www.zdic.net/hans/%E5%B1%B1) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/18.jpg) |
| 水 | 象形 | 甲骨文中间一道弯弯像水流，两边小点像流动的水花。 | - | 史实 | 一年级上册；识字4《日月山川》；第13页；修订版 | [1](https://www.zdic.net/hans/%E6%B0%B4) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/18.jpg) |
| 火 | 象形 | 甲骨文像一团向上蹿的火苗，下面大，上面尖。 | - | 史实 | 一年级上册；识字4《日月山川》；第13页；修订版 | [1](https://www.zdic.net/hans/%E7%81%AB) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/18.jpg) |
| 田 | 象形 | 字形像田埂横竖交错，把地分成一块块农田。 | - | 史实 | 一年级上册；识字4《日月山川》；第13页；修订版 | [1](https://www.zdic.net/hans/%E7%94%B0) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/18.jpg) |
| 禾 | 象形 | 金文像一棵庄稼，顶上的谷穗沉甸甸地垂下来。 | - | 史实 | 一年级上册；识字4《日月山川》；第13页；修订版 | [1](https://www.zdic.net/hans/%E7%A6%BE) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/18.jpg) |
| 口 | 象形 | 甲骨文像人张开的嘴巴。 | - | 史实 | 一年级上册；识字3《口耳目手足》；第11页；修订版 | [1](https://www.zdic.net/hans/%E5%8F%A3) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/16.jpg) |
| 目 | 象形 | 古字像一只眼睛，外框是眼眶，里面是眼珠。 | - | 史实 | 一年级上册；识字3《口耳目手足》；第11页；修订版 | [1](https://www.zdic.net/hans/%E7%9B%AE) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/16.jpg) |
| 人 | 象形 | 甲骨文像一个侧着身子站立的人。 | - | 史实 | 一年级上册；识字1《天地人》；第8页；修订版 | [1](https://www.zdic.net/hans/%E4%BA%BA) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/13.jpg) |
| 木 | 象形 | 甲骨文像一棵树，上面是树枝，下面是树根。 | - | 史实 | 一年级上册；识字2《金木水火土》；第9页；修订版 | [1](https://www.zdic.net/hans/%E6%9C%A8) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/14.jpg) |
| 林 | 会意 | 两个“木”并排站，表示树木成片生长。 | 课文：双木林。 | 史实 | 一年级上册；识字6《日月明》；第74页；修订版 | [1](https://www.zdic.net/hans/%E6%9E%97) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/79.jpg) |
| 森 | 会意 | 三个“木”叠在一起，表示树木又多又密。 | 课文：三木森。 | 史实 | 一年级上册；识字6《日月明》；第74页；修订版 | [1](https://www.zdic.net/hans/%E6%A3%AE) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/79.jpg) |
| 明 | 会意 | 甲骨文把“日”和“月”放在一起，表示明亮。 | 课文：日月明。 | 史实 | 一年级上册；识字6《日月明》；第74页；修订版 | [1](https://www.zdic.net/hans/%E6%98%8E) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/79.jpg) |
| 贝 | 象形 | 甲骨文像一枚海贝，背部拱起，下面有一道开口。 | 古人觉得贝壳漂亮珍贵，还把它当钱用，所以贝字旁的字多和钱财有关，如赚、赔、购、贫、货。 | 史实 | 二年级下册；识字3《“贝”的故事》；第33页；修订版 | [1](https://www.zdic.net/hans/%E8%B4%9D) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/38.jpg) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/39.jpg) |

## Disputed quotations

| Text | Child-friendly spoken note | Full research note | Sources |
| --- | --- | --- | --- |
| 黑发不知勤学早，白首方悔读书迟。 | 课本没写作者，常说是颜真卿，但没找到可靠早期出处 | 网上常说是颜真卿《劝学》，本卡未找到可靠早期出处；讲作者时只说“教材没写作者”。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/70.jpg) [2](https://www.gushiwen.cn/mingju_1115.aspx) |
| 书山有路勤为径，学海无涯苦作舟。 | 课本没写作者，常说是韩愈，但他的作品里找不到这句 | 常被说成韩愈所作，但韩愈作品里没有这两句，属后人托名；作者不详。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/70.jpg) [2](https://zhuanlan.zhihu.com/p/1963559756250743049) [3](https://www.zhihu.com/question/55946205) |
| 与朋友交，言而有信。 | 这句是子夏说的，不是孔子说的 | 这句是孔子的学生子夏说的，不是孔子本人说的。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/110.jpg) [2](https://zh.wikisource.org/wiki/%E8%AB%96%E8%AA%9E/%E5%AD%B8%E8%80%8C%E7%AC%AC%E4%B8%80) |
| 士不可以不弘毅，任重而道远。 | 这句是曾子说的，不是孔子说的 | 这句是曾子说的，不是孔子本人说的。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/113.jpg) [2](https://zh.wikisource.org/wiki/%E8%AB%96%E8%AA%9E/%E6%B3%B0%E4%BC%AF%E7%AC%AC%E5%85%AB) |
| 莫等闲，白了少年头，空悲切。 | 课本写岳飞，但《满江红》是不是他写的仍有争议 | 教材署岳飞；但《满江红》是否岳飞所作，学界自余嘉锡、夏承焘以来一直有争议，尚无定论。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/37.jpg) [2](https://www.chinawriter.com.cn/n1/2023/0129/c442005-32613628.html) [3](https://www.thepaper.cn/newsDetail_forward_1396387) |

## Unverified / research limits

| Item | Issue |
| --- | --- |
| 黑发不知勤学早，白首方悔读书迟 | 作者：流传署名颜真卿《劝学》，未找到可靠早期出处；教材未署名。 |
| 穷且益坚，不坠青云之志（王勃） | 篇名通常说是《滕王阁序》，本次维基文库检索未命中该句，篇名未写入卡片。 |
| 读万卷书，行万里路（董其昌） | 只核对了教材署名，未核对董其昌原文的篇名。 |
| 诚信者，天下之结也（《管子》）/ 与人善言……（《荀子》） | 只核对了教材署名，未核对篇名。 |
| 千里之行，始于足下 | 教材未署出处；常说出自《老子》，本次未核实，卡片里没写出处。 |
| 2上园地四的对联（有山皆图画等） | 教材未署作者，本次没考证作者，卡片里没写作者。 |
| 数九歌 | 各地版本不同，卡片以教材文本为准；“从冬至开始数九”是常识，没有另附来源。 |
| 男、从、众、川、耳、手、足等识字课字 | 汉典已查到字源，为控制篇幅没有收入；男字的“力”一说是耒（农具），有两种说法。 |


## Testing

Tester: `test.yaml` (`learn-chinese-words-test`, eino), shared by every implementation:

- `tests/giztest/learn-chinese-words/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-words/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-words/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-chinese-words/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses and verifies the exact opening,
hint-before-answer barrier, gentle wrong-guess handling, explicit reveal,
disputed attribution, character description, and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `riddle-no-spoiler` | 我一年级。我们来猜歇后语：竹篮打水，下半句是什么？你先别告诉我，给我一个提示。 | 只给提示，不得说出后半句；20-360字 |
| 3 | `wrong-guess` | 是“一场雨”吗？ | 温和说不对并再给一个提示，不得公布答案；10-360字 |
| 4 | `reveal` | 我猜不出来，告诉我答案和意思吧。 | 说出“竹篮打水——一场空”并讲清意思；20-360字 |
| 5 | `disputed-quote` | “书山有路勤为径”是谁说的？ | 必须说明课本没写作者、常说是韩愈但他的作品里找不到这句，不得肯定地说就是韩愈说的；20-360字 |
| 6 | `character-story` | 给我讲讲“森”字是怎么来的。 | 按知识卡描述古字样子（三个木），不说看图；20-360字 |
| 7 | `memory-store` | 请记住：我今天学会了歇后语竹篮打水，下次想学对韵歌。只确认你已经记住。 | 必须确认已记住下次想学对韵歌（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学什么。 | 重载后必须从长期记忆准确回忆对韵歌；只回答主题；2-200字 |

Run:

```sh
make test-e2e RAID=learn-chinese-words PARALLEL=2
```
