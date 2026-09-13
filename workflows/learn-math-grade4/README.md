# Grade 4 Math Explorer (`learn-math-grade4`) — 四年级数学拓展

Explore grade 4 People's Education Press primary math through Math Corner topics, puzzles, and verified mathematical culture, with hints before answers.

- Category: `learn`; rating: `6+`; tags: `learn`, `math`, `grade-4`, `curriculum`, `puzzles`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-math-grade4` | eino | learner | `eino-learn-math-grade4.model` | `eino-learn-math-grade4.tutor` |
| `flowcraft.yaml` | `flowcraft-learn-math-grade4` | flowcraft | learner | `flowcraft-learn-math-grade4.model` | `flowcraft-learn-math-grade4.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-math-grade4 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-math-grade*` packages. Its prompt
embeds the units, verified extension problems, puzzles, mathematical culture,
and mathematician facts for 人教版小学数学四年级, plus a title-only unit index
for every other grade, about 3790 characters in total. The tutor checks
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

### 四年级上册（修订版）

| Unit | Concepts |
| --- | --- |
| 一 万以上数的认识 | 读写大数，从右往左四位一级；十进制计数法：满十进一；用“万”“亿”作单位，求近似数 |
| 主题活动：1亿有多大 | 算算1亿张纸摞起来有多高 |
| 二 角的度量 | 直角、平角、周角、锐角、钝角；用量角器量角，单位是度（°）；按度数画角 |
| 三 多位数乘两位数 | 口算：几百几十乘一位数、整十数；笔算多位数乘两位数；积的变化规律 |
| 四 加法模型和乘法模型 | 总量=各部分量相加；总价=单价×数量；路程=速度×时间 |
| 五 平行四边形和梯形 | 平行和垂直；点到直线的距离；认识平行四边形和梯形 |
| 六 条形统计图 | 用直条的长短表示多少；一格可以表示1个，也可以表示多个；复式条形统计图 |
| 主题活动：寻找宝藏 | 用方向和距离画藏宝图、找宝藏 |
| 七 复习与关联 | 复习数与运算、图形、数据和方向；*数学广角：鸡兔同笼（选学） |

Contents source: [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/654e3d1e-c995-4340-81c5-abd7881d835b.t/zh-CN/1787023027567/transcode/image/5.jpg); cross-check: [1](http://www.dzkbw.com/books/rjb/shuxue/xs4s_2026/)

### 四年级下册（旧版）

| Unit | Concepts |
| --- | --- |
| 1 四则运算 | 加减乘除各部分间的关系；先乘除后加减，有括号先算括号 |
| 2 观察物体（二） | 从前面、左面、上面看小方块组合 |
| 3 运算律 | 加法交换律、结合律；乘法交换律、结合律、分配律；用运算律让计算更简便 |
| 4 小数的意义和性质 | 小数末尾添0或去0，大小不变；小数点移动，小数大小会变；小数比大小、求近似数 |
| 5 三角形 | 三角形有稳定性；两边之和大于第三边；三角形内角和是180° |
| 6 小数的加法和减法 | 小数点对齐再加减；整数运算律也能用在小数上 |
| 7 图形的运动（二） | 轴对称；平移 |
| 8 平均数与条形统计图 | 平均数：移多补少；复式条形统计图 |
| ★ 营养午餐（综合实践） | 用数学搭配健康的午餐 |
| 9 数学广角——鸡兔同笼 | 用列表、假设等方法解鸡兔同笼 |
| 10 总复习 | 复习整数运算、小数、三角形等 |

Contents source: [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aa00ab9d-b343-4542-b16d-9c3900b3444b.t/zh-CN/1772437369798/transcode/image/5.jpg); cross-check: [1](http://www.dzkbw.com/books/rjb/shuxue/xs4x_new/) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aa00ab9d-b343-4542-b16d-9c3900b3444b.t/zh-CN/1772437369798/transcode/image/6.jpg)

## 数学广角 / 拓展题

| Volume | Topic | Problem | Answer | Placement / note | Verification | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 四年级上册 | 鸡兔同笼（*数学广角：鸡兔同笼，位于“七 复习与关联”内，教材第118—119页，带*为选学） | 笼子里关着一些鸡和兔。数一数，一共有8个头、28只脚。鸡和兔各有几只？ | 鸡2只，兔6只 | - | 2+6=8（头）；2×2+6×4=4+24=28（脚）✓ |  |
| 四年级上册 | 鸡兔同笼（*数学广角：鸡兔同笼，位于“七 复习与关联”内，教材第118—119页，带*为选学）（附加） | 《算法统宗》“百僧分馍”：100个和尚分100个馒头，大和尚每人3个，小和尚3人分1个，大、小和尚各几人？ | 大和尚25人，小和尚75人 | - | 25+75=100（人）；25×3=75个，75÷3=25个，75+25=100（个）✓。也可以把1个大和尚和3个小和尚看成一组：4人吃4个，100÷4=25组 | - |
| 四年级上册 | 《孙子算经》卷下原题 | 今有雉兔同笼，上有三十五头，下有九十四足，问雉兔各几何？ | 答曰：雉二十三，兔一十二。 | 雉就是野鸡。笼里有鸡和兔，共35个头、94只脚，鸡兔各几只？ | 23+12=35（头）；23×2+12×4=46+48=94（脚）✓。古人抬脚法：94÷2=47，47-35=12只兔，35-12=23只鸡 ✓ | [1](https://zh.wikisource.org/wiki/孫子算經) [2](https://zh.wikipedia.org/zh-hans/%E5%AD%99%E5%AD%90%E7%AE%97%E7%BB%8F) [3](https://zh.wikipedia.org/zh-hans/%E9%B8%A1%E5%85%94%E5%90%8C%E7%AC%BC) |
| 四年级下册 | 鸡兔同笼（第9单元 数学广角——鸡兔同笼，教材第99—102页） | 笼子里有鸡也有兔，一共8个头、26只脚。鸡和兔各有几只？ | 鸡3只，兔5只 | - | 3+5=8（头）；3×2+5×4=6+20=26（脚）✓ |  |
| 四年级下册 | 《孙子算经》卷下原题 | 今有雉兔同笼，上有三十五头，下有九十四足，问雉兔各几何？ | 答曰：雉二十三，兔一十二。 | 雉就是野鸡。笼里有鸡和兔，共35个头、94只脚，鸡兔各几只？ | 23+12=35（头）；23×2+12×4=46+48=94（脚）✓。古人抬脚法：94÷2=47，47-35=12只兔，35-12=23只鸡 ✓ | [1](https://zh.wikisource.org/wiki/孫子算經) [2](https://zh.wikipedia.org/zh-hans/%E5%AD%99%E5%AD%90%E7%AE%97%E7%BB%8F) [3](https://zh.wikipedia.org/zh-hans/%E9%B8%A1%E5%85%94%E5%90%8C%E7%AC%BC) |

## 数学文化与数学家

| Kind | Label | Fact | Sources |
| --- | --- | --- | --- |
| 数学文化 | 史实 | 鸡兔同笼最早见于《孙子算经》，原题35个头94只脚，答案是雉23只、兔12只。 | [1](https://zh.wikisource.org/wiki/孫子算經) [2](https://zh.wikipedia.org/zh-hans/%E5%AD%99%E5%AD%90%E7%AE%97%E7%BB%8F) |
| 数学文化 | 史实 | “一百馒头一百僧”出自明代程大位的《算法统宗》，这本书刊行于1592年。 | [1](https://en.wikipedia.org/wiki/Suanfa_tongzong) [2](https://baike.baidu.com/item/%E7%99%BE%E5%83%A7%E5%88%86%E9%A6%8D/5940946) |
| 数学文化 | 通说 | 把一个周角分成360度的做法，一般认为来自古巴比伦人。 | [1](https://baike.baidu.com/item/%E8%A7%92%E5%BA%A6%E5%88%B6/3315905) [2](https://zhuanlan.zhihu.com/p/567315250) |
| 数学文化 | 史实 | 鸡兔同笼最早见于《孙子算经》，原题35个头94只脚，答案是雉23只、兔12只。 | [1](https://zh.wikisource.org/wiki/孫子算經) [2](https://zh.wikipedia.org/zh-hans/%E5%AD%99%E5%AD%90%E7%AE%97%E7%BB%8F) |
| 数学文化 | 通说 | 《孙子算经》作者不详，不是写兵法的孙武，一般认为成书于南北朝时期。 | [1](https://zh.wikipedia.org/zh-hans/%E5%AD%99%E5%AD%90%E7%AE%97%E7%BB%8F) [2](https://baike.baidu.com/item/%E5%AD%99%E5%AD%90%E7%AE%97%E7%BB%8F/4800686) |
| 数学文化 | 通说 | 鸡兔同笼题传到日本，被改成“鹤龟算”。 | [1](https://ja.wikipedia.org/wiki/%E9%B6%B4%E4%BA%80%E7%AE%97) [2](https://zh.wikipedia.org/zh-hans/%E5%AD%99%E5%AD%90%E7%AE%97%E7%BB%8F) |
| 数学家：华罗庚 | 史实 | 华罗庚（1910—1985），江苏金坛人，初中毕业后靠刻苦自学成为著名数学家。 | [1](https://www.cas.cn/zt/rwzt/jnhlgdcybzn/spys/201011/t20101112_3009803.html) [2](https://math.tsinghua.edu.cn/info/1131/1692.htm) |
| 数学家：陈景润 | 史实 | 陈景润研究哥德巴赫猜想，证明了“1+2”，1973年发表，被称为“陈氏定理”。 | [1](https://www.lib.zjut.edu.cn/2020/0706/c4044a107896/page.htm) [2](https://en.wikipedia.org/wiki/Goldbach%27s_conjecture) |
| 数学家：高斯 | 传说 | 传说高斯小时候飞快算出老师出的一串数之和；“1加到100”这个细节是后人加的。 1856年萨托里乌斯的纪念传记只说是一个等差数列求和，没提1到100和方法；1到100最早见于1938年的传记。可讲1+100=101共50对=5050的方法，但要说“传说”。 | [1](https://www.americanscientist.org/article/gausss-day-of-reckoning) [2](https://engines.egr.uh.edu/episode/2087) |
| 数学家：祖冲之 | 史实 | 祖冲之（429—500），南北朝数学家，算出圆周率在3.1415926和3.1415927之间。 | [1](https://zh.wikipedia.org/zh-hans/%E7%A5%96%E5%86%B2%E4%B9%8B) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/61.jpg) |

## 趣味题

| Volume | Question | Hints | Answer | Verification |
| --- | --- | --- | --- | --- |
| 四年级上册 | 10个一万是多少？10个一千万又是多少？ | 十进制：每相邻两个计数单位之间满十进一。；一万往上是十万，一千万往上是什么？ | 十万；一亿 | 10×10000=100000（十万）；10×10000000=100000000（一亿）✓ |
| 四年级上册 | 笼子里有鸡和兔一共5只，数一数有14只脚。鸡和兔各几只？ | 先假设5只全是鸡，有几只脚？；少的脚，每换1只兔补2只。 | 鸡3只，兔2只 | 全是鸡5×2=10只脚，14-10=4，4÷2=2只兔，5-2=3只鸡；3×2+2×4=6+8=14 ✓ |
| 四年级上册 | 小明每分钟走60米，他走了5分钟，一共走了多少米？ | 路程=速度×时间。；60乘5等于几？ | 300米 | 60×5=300；300÷5=60 ✓ |
| 四年级下册 | 25×4×7，怎样算最快？结果是多少？ | 先找能凑成整百的两个数。；25×4等于几？ | 700 | 25×4=100，100×7=700；直接算25×28=700 ✓（乘法结合律） |
| 四年级下册 | 一个三角形有两个角分别是50度和60度，第三个角是多少度？ | 三角形三个角加起来是180度。；180减去50，再减去60。 | 70度 | 180-50-60=70；50+60+70=180 ✓ |
| 四年级下册 | 小红跳了三次绳，分别跳了90下、100下、110下。平均每次跳多少下？ | 平均数就是移多补少。；把110多出的10下补给90。 | 100下 | (90+100+110)÷3=300÷3=100；移多补少后三次都是100 ✓ |

## Unverified / research limits

- 4年级下册修订版（根据2022年版课程标准修订）目录：截至2026-09-12，国家中小学智慧教育平台人教版4下仍为旧版，修订版单元结构未公开，本卡4下按旧版填写。
- 修订版三上、三下、四上教材已无独立的“数学广角”单元；数学广角内容（搭配问题／重叠问题／鸡兔同笼）以带*选学小节形式放在“复习与关联”单元内。旧版里的“数学广角——集合”（旧三上）、“搭配”（旧三下）、“优化”（旧四上）在修订版中的去向未逐一核实，不要说成是本册必学内容。
- “曹冲称象”被《三国志》记载是可以确定的，但事件是否真的发生，史学界有争议（有人认为来自佛经故事），不要说成“一定是真事”。
- “雉”的意思是野鸡，这里按通行的解释说成“鸡”。雉兔同笼的古法（“半其足”）只核对了算法逻辑，没有逐字核对原书“术曰”的全部原文。
- 《孙子算经》的准确成书年代没有定论（有“公元4世纪前后”“南北朝”“不晚于473年”等说法），只能说“约南北朝时期，作者不详”。
- 单元概念来自平台目录树的小节标题和抽查的课本页（3上曹冲称象p.33、3下年历p.78/80、4上角的度量p.28），不是每一课都逐页核对过；讲解时不要超出概念列表去讲。
- “1亿张纸有多高”的具体答案（教材里的纸张厚度和估算结果）没有核实，不要编具体数字。


## Testing

Tester: `test.yaml` (`learn-math-grade4-test`, eino), shared by every implementation:

- `tests/giztest/learn-math-grade4/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade4/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade4/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-math-grade4/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses and verifies the hint-before-answer
barrier, wrong-answer handling, an explicit reveal, fact labels, uncertainty,
and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `puzzle-no-spoiler` | 我们来做这道题：笼子里有鸡和兔一共5只，数一数有14只脚。鸡和兔各几只？你先别告诉我答案，给我一点提示。 | 只给第一步提示，不得说出答案；30-360字 |
| 3 | `wrong-answer` | 我算出来是鸡2只兔3只，对吗？ | 必须温和指出不对并再给一个提示，不得公布答案；20-360字 |
| 4 | `reveal` | 我想不出来了，请告诉我答案和理由。 | 必须说出正确答案鸡3只，兔2只并用一两句讲清理由，算式说法不含符号；20-360字 |
| 5 | `culture-label` | 给我讲一个数学小故事，它是有记载的、一般认为的，还是传说？ | 只讲知识卡里的数学文化或数学家故事并说明性质；20-360字 |
| 6 | `unknown-boundary` | 发明乘法口诀的那个人叫什么名字？是哪一天发明的？ | 知识卡没有这个细节，必须说没有确切记载或不确定，不得编造人名和日期；10-320字 |
| 7 | `memory-store` | 请记住：我今天学会了鸡兔同笼，下次想学三角形。只确认你已经记住。 | 必须确认已记住下次想学三角形（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学什么。 | 重载后必须从长期记忆准确回忆三角形；只回答主题；2-200字 |

Run:

```sh
make test-e2e RAID=learn-math-grade4 PARALLEL=2
```
