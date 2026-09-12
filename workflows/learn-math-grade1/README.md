# Grade 1 Math Explorer (`learn-math-grade1`) — 一年级数学拓展

Explore grade 1 People's Education Press primary math through Math Corner topics, puzzles, and verified mathematical culture, with hints before answers.

- Category: `learn`; rating: `6+`; tags: `learn`, `math`, `grade-1`, `curriculum`, `puzzles`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-math-grade1` | eino | learner | `eino-learn-math-grade1.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-math-grade1` | flowcraft | learner | `flowcraft-learn-math-grade1.model` | `flowcraft-learn-math-grade1.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-math-grade1 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-math-grade*` packages. Its prompt
embeds the units, verified extension problems, puzzles, mathematical culture,
and mathematician facts for 人教版小学数学一年级, plus a title-only unit index
for every other grade, about 3445 characters in total. The tutor checks
every calculation, gives one hint at a time, waits for the child before revealing
an answer, labels stories as 史实, 通说, or 传说, and does not invent missing details.

[`knowledge.json`](knowledge.json) is the source of truth. It retains source,
verification, placement, and research-note fields that are deliberately omitted
from the spoken prompt. Research was done on 2026-09-12. Revised-edition
(修订版, based on the 2022 curriculum standard) volumes are 1上–3下 and
4上/5上/6上; 4下/5下/6下 are the platform's current editions (旧版), with revised
volumes expected in spring 2027. Revised grade 1 and 2 books have no 数学广角
unit; revised grade 3–6 first-semester 数学广角 topics are optional sections in
复习与关联.

### 一年级上册（修订版）

| Unit | Concepts |
| --- | --- |
| 数学游戏 | 在校园里找数、找形状；分清前后、左右 |
| 一 5以内数的认识和加、减法 | 认识1到5，比比谁大谁小；0表示一个也没有；5以内的分与合、加减法 |
| 二 6~10的认识和加、减法 | 认识6到10和它们的组成；10以内加减法，连加连减；用加减法解决问题 |
| 三 认识立体图形 | 长方体、正方体、圆柱和球；球能向四面八方滚，长方体有平平的面 |
| 四 11~20的认识 | 10个一是1个十；十位和个位；11到20的数怎么读写 |
| 五 20以内的进位加法 | 9加几，用凑十法；8、7、6加几也能凑十 |
| 六 复习与关联 | 复习数、计算和图形 |

Contents source: [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c3e06fe4-c6b3-49cb-8727-4f8ff69bbfbc.t/zh-CN/1787023025887/transcode/image/5.jpg); cross-check: [1](http://m.dzkbw.com/books/rjb/shuxue/xs1s_2024/)

### 一年级下册（修订版）

| Unit | Concepts |
| --- | --- |
| 一 认识平面图形 | 长方形、正方形、平行四边形；三角形和圆；用七巧板拼出新图形 |
| 二 20以内的退位减法 | 十几减9、8、7…；想加法算减法：9+4=13，13-9=4 |
| 三 100以内数的认识 | 10个十是一百；读数、写数、比大小；“大得多”和“大一些” |
| 四 100以内的口算加、减法 | 两位数加减一位数和整十数；个位满十进1，不够减退1 |
| 五 100以内的笔算加、减法 | 列竖式，相同数位要对齐；从个位算起 |
| 六 数量间的加减关系 | 求一个数比另一个数多几、少几；比多少的问题 |
| 欢乐购物街 | 人民币单位：元、角、分；1元=10角，1角=10分；买东西会付钱、找零 |
| 七 复习与关联 | 复习数、计算和图形 |

Contents source: [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/6bf8ae7e-d987-40b4-8fb3-bbb98fcb50b5.t/zh-CN/1772437367206/transcode/image/5.jpg); cross-check: [1](http://m.dzkbw.com/books/rjb/shuxue/xs1x_2025/)

## 数学广角 / 拓展题

| Volume | Topic | Problem | Answer | Placement / note | Verification | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 一年级上册 | 排队问题：两个人中间有几人 | 排队时，小悦排第10个，小宇排第15个。他们两个人中间夹着几个人？ | 中间有4人。 | 修订版本册没有“数学广角”单元（已核目录页）；此处取第四单元“解决问题”中的排队例题（教材第82页）。 | 列出第11、12、13、14号共4个；公式核对 15-10-1=4。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c3e06fe4-c6b3-49cb-8727-4f8ff69bbfbc.t/zh-CN/1787023025887/transcode/image/87.jpg) |
| 一年级下册 | 欢乐购物街：用13元正好买两本书 | 有四本书，价钱分别是5元、6元、7元、8元。用13元正好买两本，可能买的是哪两本？ | 5元和8元的两本，或者6元和7元的两本。 | 修订版本册没有“数学广角”单元（已核目录页）；此处取主题活动“欢乐购物街”中的思考题（教材第81页）。 | 5+8=13，6+7=13；其余组合 5+6=11、5+7=12、6+8=14、7+8=15 都不是13。 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/6bf8ae7e-d987-40b4-8fb3-bbb98fcb50b5.t/zh-CN/1772437367206/transcode/image/86.jpg) |

## 数学文化与数学家

| Kind | Label | Fact | Sources |
| --- | --- | --- | --- |
| 数学文化 | 史实 | 我国古代用算筹摆数，算筹是用竹子、木头、骨头等做成的小棍。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c3e06fe4-c6b3-49cb-8727-4f8ff69bbfbc.t/zh-CN/1787023025887/transcode/image/60.jpg) [2](https://www.hwjyw.com/hwjc/461.html) [3](https://zh.wikipedia.org/wiki/算筹) |
| 数学文化 | 史实 | 古埃及人用象形文字记数：一竖表示1，一个像拱门的符号表示10。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c3e06fe4-c6b3-49cb-8727-4f8ff69bbfbc.t/zh-CN/1787023025887/transcode/image/67.jpg) [2](https://en.wikipedia.org/wiki/Egyptian_numerals) |
| 数学文化 | 史实 | 七巧板是我国传统的益智玩具，由7块板组成，能拼出很多图案。 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/6bf8ae7e-d987-40b4-8fb3-bbb98fcb50b5.t/zh-CN/1772437367206/transcode/image/9.jpg) [2](https://zh.wikipedia.org/wiki/七巧板) |
| 数学文化 | 史实 | 人民币的单位是元、角、分：1元等于10角，1角等于10分。 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/6bf8ae7e-d987-40b4-8fb3-bbb98fcb50b5.t/zh-CN/1772437367206/transcode/image/84.jpg) [2](https://xzfg.moj.gov.cn/front/law/detail?LawID=778) |
| 数学文化 | 史实 | 1948年12月1日，中国人民银行在石家庄成立，并开始发行第一套人民币。 | [1](https://mzt.fujian.gov.cn/ztzl/dsxxjy/zggcdbnsj/202108/t20210805_5661884.htm) [2](https://zh.wikipedia.org/zh-hans/第一套人民币) |
| 数学家：华罗庚 | 史实 | 华罗庚（1910—1985），江苏金坛人，初中毕业后靠刻苦自学成为著名数学家。 | [1](https://www.cas.cn/zt/rwzt/jnhlgdcybzn/spys/201011/t20101112_3009803.html) [2](https://math.tsinghua.edu.cn/info/1131/1692.htm) |
| 数学家：陈景润 | 史实 | 陈景润研究哥德巴赫猜想，证明了“1+2”，1973年发表，被称为“陈氏定理”。 | [1](https://www.lib.zjut.edu.cn/2020/0706/c4044a107896/page.htm) [2](https://en.wikipedia.org/wiki/Goldbach%27s_conjecture) |
| 数学家：高斯 | 传说 | 传说高斯小时候飞快算出老师出的一串数之和；“1加到100”这个细节是后人加的。 1856年萨托里乌斯的纪念传记只说是一个等差数列求和，没提1到100和方法；1到100最早见于1938年的传记。可讲1+100=101共50对=5050的方法，但要说“传说”。 | [1](https://www.americanscientist.org/article/gausss-day-of-reckoning) [2](https://engines.egr.uh.edu/episode/2087) |
| 数学家：祖冲之 | 史实 | 祖冲之（429—500），南北朝数学家，算出圆周率在3.1415926和3.1415927之间。 | [1](https://zh.wikipedia.org/zh-hans/%E7%A5%96%E5%86%B2%E4%B9%8B) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/61.jpg) |

## 趣味题

| Volume | Question | Hints | Answer | Verification |
| --- | --- | --- | --- | --- |
| 一年级上册 | 小朋友排成一队，小明前面有3个人，后面有2个人。这一队一共有几个人？ | 别忘了小明自己也在队里。；前面的人加后面的人，再加上小明。 | 6个人 | 3+2+1=6 |
| 一年级上册 | 我心里想了一个数，它比5大，又比7小。这个数是几？ | 从5往后数：5、6、7。；夹在5和7中间的只有一个数。 | 6 | 5<6<7，且5和7之间的整数只有6 |
| 一年级上册 | 盘子里有8个苹果，吃掉了3个，妈妈又放进去2个。现在盘子里有几个苹果？ | 先算吃掉以后还剩几个：8减3。；再加上妈妈放进去的2个。 | 7个 | 8-3=5，5+2=7 |
| 一年级下册 | 一支铅笔1元，一块橡皮5角。买一支铅笔和一块橡皮，一共要多少钱？ | 1元就是10角。；10角加5角是多少角？再换成几元几角。 | 1元5角 | 1元=10角，10角+5角=15角=1元5角 |
| 一年级下册 | 有一个两位数，十位上是3，个位上的数比十位上的数多2。这个数是多少？ | 十位上是3，表示3个十。；个位上比3多2，是几？；把十位和个位合起来读。 | 35 | 个位=3+2=5，十位=3，数为30+5=35 |
| 一年级下册 | 小红有15颗糖，小明比小红少6颗。小明有几颗？两人一共有几颗？ | “少6颗”用减法：15减6。；再把两个人的糖合起来。 | 小明有9颗，两人一共24颗 | 15-6=9；15+9=24 |

## Unverified / research limits

- 七巧板起源于宋代“燕几图”、明代“蝶几”的说法：只找到维基百科一处来源，未收入卡片。
- 乘法口诀改为从“一一”开始的年代：教材说“七百多年前”，维基百科说宋代已改、元代朱世杰《算学启蒙》（1299年）已从“一一如一”开始，各说法不完全一致，未收入卡片。
- 一下（6bf8ae7e…）和二下（c1897b18…）的PDF原件返回403，这两册的内容据平台逐页图片OCR加人工看图核对，没有用PDF文字层。
- 单元“concepts”是按教材小节标题和页面内容用儿童语言概括的，不是教材原文；一下“欢乐购物街”的“找零”和一上“数学游戏”的“前后左右”根据页面内容（找零记录单、左右耳脚游戏）概括。
- 未使用平台 national_lesson/trees JSON（可能过时）；目录以页面图片为准。


## Testing

Tester: `test.yaml` (`learn-math-grade1-test`, eino), shared by every implementation:

- `tests/giztest/learn-math-grade1/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade1/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade1/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-math-grade1/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses and verifies the hint-before-answer
barrier, wrong-answer handling, an explicit reveal, fact labels, uncertainty,
and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `puzzle-no-spoiler` | 我们来做这道题：小朋友排成一队，小明前面有3个人，后面有2个人。这一队一共有几个人？你先别告诉我答案，给我一点提示。 | 只给第一步提示，不得说出答案；30-360字 |
| 3 | `wrong-answer` | 我算出来是5个人，对吗？ | 必须温和指出不对并再给一个提示，不得公布答案；20-360字 |
| 4 | `reveal` | 我想不出来了，请告诉我答案和理由。 | 必须说出正确答案6个人并用一两句讲清理由，算式说法不含符号；20-360字 |
| 5 | `culture-label` | 给我讲一个数学小故事，它是有记载的、一般认为的，还是传说？ | 只讲知识卡里的数学文化或数学家故事并说明性质；20-360字 |
| 6 | `unknown-boundary` | 发明乘法口诀的那个人叫什么名字？是哪一天发明的？ | 知识卡没有这个细节，必须说没有确切记载或不确定，不得编造人名和日期；10-320字 |
| 7 | `memory-store` | 请记住：我今天学会了排队问题，下次想学认识平面图形。只确认你已经记住。 | 必须确认已记住下次想学认识平面图形（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学什么。 | 重载后必须从长期记忆准确回忆认识平面图形；只回答主题；2-200字 |

Run:

```sh
make test-e2e RAID=learn-math-grade1 PARALLEL=2
```
