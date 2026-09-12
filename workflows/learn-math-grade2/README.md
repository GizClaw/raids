# Grade 2 Math Explorer (`learn-math-grade2`) — 二年级数学拓展

Explore grade 2 People's Education Press primary math through Math Corner topics, puzzles, and verified mathematical culture, with hints before answers.

- Category: `learn`; rating: `6+`; tags: `learn`, `math`, `grade-2`, `curriculum`, `puzzles`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-math-grade2` | eino | learner | `eino-learn-math-grade2.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-math-grade2` | flowcraft | learner | `flowcraft-learn-math-grade2.model` | `flowcraft-learn-math-grade2.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-math-grade2 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-math-grade*` packages. Its prompt
embeds the units, verified extension problems, puzzles, mathematical culture,
and mathematician facts for 人教版小学数学二年级, plus a title-only unit index
for every other grade, about 3516 characters in total. The tutor checks
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

### 二年级上册（修订版）

| Unit | Concepts |
| --- | --- |
| 一 分类与整理 | 按一个标准分一分、数一数；自己定标准，一层一层分 |
| 二 1~6的表内乘法 | 几个相同的数相加，可以用乘法；背1到6的乘法口诀 |
| 三 1~6的表内除法 | 平均分：每份一样多；用乘法口诀求商 |
| 校园小导游 | 认识东、南、西、北；东和西相对，南和北相对 |
| 四 厘米和米 | 1米=100厘米；认识线段；量短的用厘米，量长的用米 |
| 身体上的尺子 | 用一拃、一步当尺子量长度；拃和步是古代用过的“身体尺” |
| 五 7~9的表内乘、除法 | 背7、8、9的乘法口诀；用口诀求商；解决连续两问的问题 |
| 六 复习与关联 | 复习乘除法、方向和长度 |

Contents source: [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8cfc5a2a-425c-4b9a-a97c-e78d4a4c1e3a.t/zh-CN/1787023026468/transcode/image/5.jpg); cross-check: [1](http://m.dzkbw.com/books/rjb/shuxue/xs2s_2025/)

### 二年级下册（修订版）

| Unit | Concepts |
| --- | --- |
| 时间在哪里 | 时、分、秒是时间单位；1时=60分；按时间顺序安排一天 |
| 一 有余数的除法 | 分不完剩下的叫余数；余数要比除数小 |
| 二 数量间的乘除关系 | 求一个数是另一个数的几倍；求一个数的几倍是多少 |
| 三 万以内数的认识 | 10个百是1千，10个千是1万；用算盘和计数器拨数；近似数：约等于几千 |
| 四 万以内的加法和减法 | 相同数位对齐，从个位算起；估算：只看百位也能判断；数独游戏（选学） |
| 数学连环画 | 用连环画讲一个数学故事 |
| 五 复习与关联 | 复习数、运算和数量关系 |

Contents source: [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c1897b18-b302-4e8d-9fd4-40915c4b05c2.t/zh-CN/1772437368178/transcode/image/5.jpg); cross-check: [1](http://m.dzkbw.com/books/rjb/shuxue/xs2x_2026/)

## 数学广角 / 拓展题

| Volume | Topic | Problem | Answer | Placement / note | Verification | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 二年级上册 | 校园小导游：认识东、南、西、北 | 早上起床，你面对着太阳站好。这时你的前、后、左、右分别是什么方向？ | 前面东，后面西，左面北，右面南。 | 修订版本册没有“数学广角”单元（已核目录页）；此处取主题活动“校园小导游”中辨认方向的内容（教材第50—51页）。 | 方向按顺时针依次为东→南→西→北；面向东时向右转90°为南、向左转90°为北、转180°为西，与答案一致（教材第50页原文同此结论）。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8cfc5a2a-425c-4b9a-a97c-e78d4a4c1e3a.t/zh-CN/1787023026468/transcode/image/55.jpg) |
| 二年级下册 | 数独游戏（4×4） | 一个4行4列的方格，每行、每列、每个2×2的小宫里都要有1、2、3、4，不能重复。某个空格所在的列已经有1和3，所在的行已经有4，这个空格填几？ | 填2。 | 修订版本册没有“数学广角”单元（已核目录页）；此处取第四单元中标“*”的选学内容“数独游戏”（教材第78—79页）。 | {1,2,3,4} 去掉 {1,3,4} 只剩 {2}。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c1897b18-b302-4e8d-9fd4-40915c4b05c2.t/zh-CN/1772437368178/transcode/image/83.jpg) |

## 数学文化与数学家

| Kind | Label | Fact | Sources |
| --- | --- | --- | --- |
| 数学文化 | 史实 | 乘号“×”是17世纪开始使用的，英国数学家奥特雷德1631年在书里用过它。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8cfc5a2a-425c-4b9a-a97c-e78d4a4c1e3a.t/zh-CN/1787023026468/transcode/image/20.jpg) [2](https://en.wikipedia.org/wiki/Multiplication_sign) |
| 数学文化 | 史实 | 除号“÷”也是17世纪开始用的，1659年瑞士人拉恩的代数书里第一次用它表示除法。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8cfc5a2a-425c-4b9a-a97c-e78d4a4c1e3a.t/zh-CN/1787023026468/transcode/image/45.jpg) [2](https://en.wikipedia.org/wiki/Division_sign) |
| 数学文化 | 史实 | 两千多年前的秦代竹简上就刻有乘法口诀，是从“九九八十一”开始倒着背的。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8cfc5a2a-425c-4b9a-a97c-e78d4a4c1e3a.t/zh-CN/1787023026468/transcode/image/91.jpg) [2](https://news.qq.com/rain/a/20251009A012JC00) |
| 数学文化 | 史实 | 《孙子算经》里有“物不知数”题：一个数除以3余2、除以5余3、除以7余2，最小是23。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c1897b18-b302-4e8d-9fd4-40915c4b05c2.t/zh-CN/1772437368178/transcode/image/28.jpg) [2](https://zh.wikipedia.org/wiki/中国剩余定理) |
| 数学文化 | 史实 | 中国珠算在2013年被列入联合国教科文组织人类非物质文化遗产代表作名录。 | [1](https://ich.unesco.org/en/RL/chinese-zhusuan-knowledge-and-practices-of-mathematical-calculation-through-the-abacus-00853) [2](https://zh.wikipedia.org/wiki/算盘) |
| 数学文化 | 史实 | 古人用日晷看太阳影子的位置来知道时间，还用漏壶靠滴水来计时。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c1897b18-b302-4e8d-9fd4-40915c4b05c2.t/zh-CN/1772437368178/transcode/image/13.jpg) [2](https://zh.wikipedia.org/wiki/日晷) [3](https://zh.wikipedia.org/wiki/漏刻) |
| 数学家：华罗庚 | 史实 | 华罗庚（1910—1985），江苏金坛人，初中毕业后靠刻苦自学成为著名数学家。 | [1](https://www.cas.cn/zt/rwzt/jnhlgdcybzn/spys/201011/t20101112_3009803.html) [2](https://math.tsinghua.edu.cn/info/1131/1692.htm) |
| 数学家：陈景润 | 史实 | 陈景润研究哥德巴赫猜想，证明了“1+2”，1973年发表，被称为“陈氏定理”。 | [1](https://www.lib.zjut.edu.cn/2020/0706/c4044a107896/page.htm) [2](https://en.wikipedia.org/wiki/Goldbach%27s_conjecture) |
| 数学家：高斯 | 传说 | 传说高斯小时候飞快算出老师出的一串数之和；“1加到100”这个细节是后人加的。 1856年萨托里乌斯的纪念传记只说是一个等差数列求和，没提1到100和方法；1到100最早见于1938年的传记。可讲1+100=101共50对=5050的方法，但要说“传说”。 | [1](https://www.americanscientist.org/article/gausss-day-of-reckoning) [2](https://engines.egr.uh.edu/episode/2087) |
| 数学家：祖冲之 | 史实 | 祖冲之（429—500），南北朝数学家，算出圆周率在3.1415926和3.1415927之间。 | [1](https://zh.wikipedia.org/zh-hans/%E7%A5%96%E5%86%B2%E4%B9%8B) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/61.jpg) |

## 趣味题

| Volume | Question | Hints | Answer | Verification |
| --- | --- | --- | --- | --- |
| 二年级上册 | 院子里有3只小鸡和2只小狗。它们一共有几条腿？ | 一只小鸡2条腿，一只小狗4条腿。；3只小鸡：3个2；2只小狗：2个4。；把两个结果加起来。 | 14条腿 | 2×3=6，4×2=8，6+8=14 |
| 二年级上册 | 12个桃子平均分给4只小猴，每只小猴分到几个？ | 平均分就是每只分得一样多。；想口诀：几乘4等于12？ | 3个 | 12÷4=3，口诀三四十二，3×4=12 |
| 二年级上册 | 一根彩带长1米，剪掉40厘米，还剩多少厘米？ | 先把1米换成厘米：1米=100厘米。；再用100厘米减40厘米。 | 60厘米 | 1米=100厘米，100-40=60 |
| 二年级下册 | 有17个苹果，每个盘子放5个。能放满几盘？还剩几个？ | 想一想：17里面最多有几个5？；5×3=15，再放一盘就不够了。；17减15就是剩下的。 | 能放满3盘，还剩2个 | 17÷5=3……2；5×3+2=17，余数2<5 |
| 二年级下册 | 20个小朋友去划船，每条船最多坐6人。至少要几条船才能让大家都坐上？ | 先算20里面有几个6：3个6是18。；坐满3条船后还剩2人。；剩下的2人也要一条船。 | 至少4条船 | 20÷6=3……2，3+1=4；6×3=18<20，6×4=24≥20 |
| 二年级下册 | 用8、5、1、0这四个数字各用一次，组成一个最大的四位数，是多少？ | 要最大，最大的数字放在千位。；按从大到小的顺序排：8、5、1、0。 | 8510 | 数字从大到小排列 8>5>1>0 得 8510；0不能放在千位，若求最小应为1058 |

## Unverified / research limits

- 七巧板起源于宋代“燕几图”、明代“蝶几”的说法：只找到维基百科一处来源，未收入卡片。
- 乘法口诀改为从“一一”开始的年代：教材说“七百多年前”，维基百科说宋代已改、元代朱世杰《算学启蒙》（1299年）已从“一一如一”开始，各说法不完全一致，未收入卡片。
- 一下（6bf8ae7e…）和二下（c1897b18…）的PDF原件返回403，这两册的内容据平台逐页图片OCR加人工看图核对，没有用PDF文字层。
- 单元“concepts”是按教材小节标题和页面内容用儿童语言概括的，不是教材原文；一下“欢乐购物街”的“找零”和一上“数学游戏”的“前后左右”根据页面内容（找零记录单、左右耳脚游戏）概括。
- 未使用平台 national_lesson/trees JSON（可能过时）；目录以页面图片为准。


## Testing

Tester: `test.yaml` (`learn-math-grade2-test`, eino), shared by every implementation:

- `tests/giztest/learn-math-grade2/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade2/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade2/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-math-grade2/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses and verifies the hint-before-answer
barrier, wrong-answer handling, an explicit reveal, fact labels, uncertainty,
and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `puzzle-no-spoiler` | 我们来做这道题：院子里有3只小鸡和2只小狗。它们一共有几条腿？你先别告诉我答案，给我一点提示。 | 只给第一步提示，不得说出答案；30-360字 |
| 3 | `wrong-answer` | 我算出来是10条腿，对吗？ | 必须温和指出不对并再给一个提示，不得公布答案；20-360字 |
| 4 | `reveal` | 我想不出来了，请告诉我答案和理由。 | 必须说出正确答案14条腿并用一两句讲清理由，算式说法不含符号；20-360字 |
| 5 | `culture-label` | 给我讲一个数学小故事，它是有记载的、一般认为的，还是传说？ | 只讲知识卡里的数学文化或数学家故事并说明性质；20-360字 |
| 6 | `unknown-boundary` | 发明乘法口诀的那个人叫什么名字？是哪一天发明的？ | 知识卡没有这个细节，必须说没有确切记载或不确定，不得编造人名和日期；10-320字 |
| 7 | `memory-store` | 请记住：我今天学会了表内乘法，下次想学有余数的除法。只确认你已经记住。 | 必须确认已记住下次想学有余数的除法（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学什么。 | 重载后必须从长期记忆准确回忆有余数的除法；只回答主题；2-200字 |

Run:

```sh
make test-e2e RAID=learn-math-grade2 PARALLEL=2
```
