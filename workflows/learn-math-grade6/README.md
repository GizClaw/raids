# Grade 6 Math Explorer (`learn-math-grade6`) — 六年级数学拓展

Explore grade 6 People's Education Press primary math through Math Corner topics, puzzles, and verified mathematical culture, with hints before answers.

- Category: `learn`; rating: `6+`; tags: `learn`, `math`, `grade-6`, `curriculum`, `puzzles`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-math-grade6` | eino | learner | `eino-learn-math-grade6.model` | `eino-learn-math-grade6.tutor` |
| `flowcraft.yaml` | `flowcraft-learn-math-grade6` | flowcraft | learner | `flowcraft-learn-math-grade6.model` | `flowcraft-learn-math-grade6.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-math-grade6 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-math-grade*` packages. Its prompt
embeds the units, verified extension problems, puzzles, mathematical culture,
and mathematician facts for 人教版小学数学六年级, plus a title-only unit index
for every other grade, about 3758 characters in total. The tutor checks
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

### 六年级上册（修订版）

| Unit | Concepts |
| --- | --- |
| 一 确定位置 | 用数对（列，行）表示位置，如（2，3）；用方向和距离确定位置；描述物体的运动路线 |
| 二 分数乘法 | 分数乘整数：分子乘整数，分母不变；分数乘分数：分子乘分子，分母乘分母；求一个数的几分之几是多少，用乘法 |
| 三 分数除法 | 乘积是1的两个数互为倒数；除以一个数，等于乘它的倒数；工程问题：把总工作量看作1 |
| 生活中的负数 | 负数表示相反意义的量，如零下4℃；数轴上，负数在0的左边 |
| 四 圆 | 圆心、半径、直径；认识扇形；周长C=πd=2πr，π约等于3.14；圆面积S=πr² |
| 体育中的数学 | 研究体育里的数学，如跑道起跑线 |
| 五 百分数 | 百分数表示一个数是另一个数的百分之几；百分率、折扣、利率、增长率 |
| 水是生命之源 | 调查用水情况，设计节水方案 |
| 六 复习与关联 | 整理分数乘除法、圆等知识；选学：数学广角·鸽巢问题 |

Contents source: [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/5.jpg); cross-check: [1](http://www.dzkbw.com/books/rjb/shuxue/xs6s_2026/) [2](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=845136d4-e27b-4e7e-b9a9-00cadf4f9e20)

### 六年级下册（旧版）

| Unit | Concepts |
| --- | --- |
| 1 负数 | 用正数、负数表示相反意义的量；0既不是正数，也不是负数 |
| 2 百分数（二） | 折扣：八折就是原价的80%；成数、税率、利率 |
| 生活与百分数 | 调查利率，设计合理的理财方案 |
| 3 圆柱与圆锥 | 圆柱体积=底面积×高；等底等高的圆锥，体积是圆柱的三分之一；圆柱侧面展开是长方形 |
| 4 比例 | 两个比相等的式子叫比例；正比例和反比例；比例尺=图上距离∶实际距离 |
| 自行车里的数学 | 用齿轮齿数算自行车能走多远 |
| 5 数学广角——鸽巢问题 | 4支笔放进3个笔筒，总有一个至少2支；物体数÷抽屉数有余数时，至少数=商+1 |
| 6 整理和复习 | 整理小学六年学过的数学 |

Contents source: [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e650f4c-e616-4699-ac0a-4911b22e2f2e.t/zh-CN/1772437371296/transcode/image/5.jpg%20;%20https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e650f4c-e616-4699-ac0a-4911b22e2f2e.t/zh-CN/1772437371296/transcode/image/6.jpg); cross-check: [1](http://www.dzkbw.com/books/rjb/shuxue/xs6x_new/) [2](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e650f4c-e616-4699-ac0a-4911b22e2f2e)

## 数学广角 / 拓展题

| Volume | Topic | Problem | Answer | Placement / note | Verification | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 六年级上册 | 鸽巢问题 | 7只鸽子飞回3个鸽笼，为什么总有一个鸽笼里至少有3只鸽子？ | 总有一个鸽笼至少有3只 | 六 复习与关联 内，标“*数学广角：鸽巢问题”（选学），课本第116—117页 | 7÷3=2……1，至少数=2+1=3。反证：若每笼最多2只，最多2×3=6只<7只，矛盾。 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/121.jpg) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/122.jpg) |
| 六年级下册 | 鸽巢问题（抽屉原理） | 把4支铅笔放进3个笔筒，不管怎么放，为什么总有一个笔筒里至少有2支？ | 总有一个笔筒至少有2支 | 第5单元 数学广角——鸽巢问题，课本第67—69页 | 4÷3=1……1，至少数=1+1=2。反证：若每个笔筒最多1支，最多1×3=3支<4支，矛盾。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e650f4c-e616-4699-ac0a-4911b22e2f2e.t/zh-CN/1772437371296/transcode/image/72.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e650f4c-e616-4699-ac0a-4911b22e2f2e.t/zh-CN/1772437371296/transcode/image/73.jpg) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e650f4c-e616-4699-ac0a-4911b22e2f2e.t/zh-CN/1772437371296/transcode/image/74.jpg) |

## 数学文化与数学家

| Kind | Label | Fact | Sources |
| --- | --- | --- | --- |
| 数学文化 | 史实 | 祖冲之算出圆周率在3.1415926和3.1415927之间，还给出密率355/113。 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/61.jpg) [2](https://zh.wikipedia.org/zh-hans/%E7%A5%96%E5%86%B2%E4%B9%8B) |
| 数学文化 | 史实 | 刘徽用割圆术：从圆内接正六边形开始，边数不断加倍，越来越接近圆。 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/67.jpg) [2](https://zh.wikipedia.org/wiki/%E5%88%98%E5%BE%BD%E5%89%B2%E5%9C%86%E6%9C%AF) |
| 数学文化 | 史实 | 《墨经》说“圜，一中同长也”：圆有一个中心，到圆上各点一样长。 | [1](https://cn.chinadaily.com.cn/a/202305/17/WS64647beea310537989374947.html) [2](https://www.thepaper.cn/newsDetail_forward_1514369) |
| 数学文化 | 史实 | 《九章算术》讲了正负数的加减法；刘徽用红算筹表示正数、黑算筹表示负数。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e650f4c-e616-4699-ac0a-4911b22e2f2e.t/zh-CN/1772437371296/transcode/image/10.jpg) [2](https://zh.wikipedia.org/zh-cn/%E4%B9%9D%E7%AB%A0%E7%AE%97%E6%9C%AF) |
| 数学文化 | 史实 | 1834年德国数学家狄利克雷把它叫“抽屉原理”，所以也叫狄利克雷原理。 | [1](https://en.wikipedia.org/wiki/Pigeonhole_principle) [2](https://baike.baidu.com/item/%E6%8A%BD%E5%B1%89%E5%8E%9F%E7%90%86/233776) |
| 数学家：华罗庚 | 史实 | 华罗庚（1910—1985），江苏金坛人，初中毕业后靠刻苦自学成为著名数学家。 | [1](https://www.cas.cn/zt/rwzt/jnhlgdcybzn/spys/201011/t20101112_3009803.html) [2](https://math.tsinghua.edu.cn/info/1131/1692.htm) |
| 数学家：陈景润 | 史实 | 陈景润研究哥德巴赫猜想，证明了“1+2”，1973年发表，被称为“陈氏定理”。 | [1](https://www.lib.zjut.edu.cn/2020/0706/c4044a107896/page.htm) [2](https://en.wikipedia.org/wiki/Goldbach%27s_conjecture) |
| 数学家：高斯 | 传说 | 传说高斯小时候飞快算出老师出的一串数之和；“1加到100”这个细节是后人加的。 1856年萨托里乌斯的纪念传记只说是一个等差数列求和，没提1到100和方法；1到100最早见于1938年的传记。可讲1+100=101共50对=5050的方法，但要说“传说”。 | [1](https://www.americanscientist.org/article/gausss-day-of-reckoning) [2](https://engines.egr.uh.edu/episode/2087) |
| 数学家：祖冲之 | 史实 | 祖冲之（429—500），南北朝数学家，算出圆周率在3.1415926和3.1415927之间。 | [1](https://zh.wikipedia.org/zh-hans/%E7%A5%96%E5%86%B2%E4%B9%8B) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/61.jpg) |

## 趣味题

| Volume | Question | Hints | Answer | Verification |
| --- | --- | --- | --- | --- |
| 六年级上册 | 一根绳子长12米，用去了三分之二，还剩多少米？ | 还剩几分之几？1减三分之二。；还剩三分之一。；12米的三分之一，就是12除以3。 | 4米 | 12×2/3=8（米），12−8=4（米）；或12×(1−2/3)=4。 |
| 六年级上册 | 早上气温是零下3度，中午比早上升高了8度，中午是多少度？ | 从零下3度往上数。；先升3度，到0度。；8度还剩5度，再往上升5度。 | 5℃（零上5度） | −3+8=5。 |
| 六年级上册 | 一个圆的半径是1米，它的周长大约是多少米？（π取3.14） | 周长=2×π×半径。；半径1米，直径就是2米。；3.14×2是多少？ | 6.28米 | C=2πr=2×3.14×1=6.28（米）。 |
| 六年级下册 | 抽屉里有很多红袜子和白袜子，闭着眼睛拿，至少拿几只才能保证有两只颜色一样？ | 颜色只有两种，就像两个鸽笼。；最不走运时，前两只一红一白。；第三只一定和其中一只同色。 | 3只 | 2只可能一红一白，不能保证；3只放进2种颜色：3÷2=1……1，至少1+1=2只同色。 |
| 六年级下册 | 一个圆柱和一个圆锥等底等高，圆柱的体积是12立方分米，圆锥的体积是多少？ | 等底等高时，圆锥体积是圆柱的三分之一。；就是12的三分之一。；12除以3。 | 4立方分米 | V锥=1/3×S×h=1/3×12=4（立方分米）。 |
| 六年级下册 | 在比例尺是1比100000的地图上，两个地方相距3厘米，实际相距多少千米？ | 图上1厘米表示实际100000厘米。；3×100000=300000厘米。；100000厘米是1千米。 | 3千米 | 3×100000=300000（厘米）=3000（米）=3（千米）。 |

## Unverified / research limits

- 修订版五年级下册、六年级下册（根据2022年版课标）截至2026-09-12未见公开；平台上人教版5下/6下仍为现行旧版（2026-03更新，无“修订”字样）。
- 修订版6上目录中没有“比”单元；“比”移到哪一册未核实。
- 修订版5上“用字母表示数和数量关系”单元（据平台目录树）未列解方程；方程内容移到哪一册未核实。
- 单元内小节名称部分来自国家平台national_lesson目录树，已用课本页图抽查（小数乘整数、轴对称、公顷和平方千米、格点多边形、圆和扇形的认识、倒数的认识、百分数的意义等），未逐页核对全部小节。
- 高斯速算故事的年龄、老师、具体题目均无可靠一手记录，只能作为“传说”讲。
- 5下课本说“截至2021年找到51个完全数”已过时：2024年10月发现第52个梅森素数，已知偶完全数52个；卡片未写个数。
- 抽屉原理并非狄利克雷最早提出：已知最早记载见于1622年Leurechon的书；卡片只写他1834年的命名。
- 《墨经》是墨家著作，“圆，一中同长也”是否墨子本人所说不能确定；卡片只写《墨经》。
- “《九章算术》是世界上最早使用负数的书”为常见说法，卡片未采用“世界最早”措辞。
- 旧版6上“数与形”、旧版5上“植树问题”作为独立数学广角单元已不在修订版中；修订版5上/6上的数学广角为“复习与关联”中的选学内容。


## Testing

Tester: `test.yaml` (`learn-math-grade6-test`, eino), shared by every implementation:

- `tests/giztest/learn-math-grade6/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade6/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade6/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-math-grade6/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses and verifies the hint-before-answer
barrier, wrong-answer handling, an explicit reveal, fact labels, uncertainty,
and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `puzzle-no-spoiler` | 我们来做这道题：在比例尺是1比100000的地图上，两个地方相距3厘米，实际相距多少千米？你先别告诉我答案，给我一点提示。 | 只给第一步提示，不得说出答案；30-360字 |
| 3 | `wrong-answer` | 我算出来是300米，对吗？ | 必须温和指出不对并再给一个提示，不得公布答案；20-360字 |
| 4 | `reveal` | 我想不出来了，请告诉我答案和理由。 | 必须说出正确答案3千米并用一两句讲清理由，算式说法不含符号；20-360字 |
| 5 | `culture-label` | 给我讲一个数学小故事，它是有记载的、一般认为的，还是传说？ | 只讲知识卡里的数学文化或数学家故事并说明性质；20-360字 |
| 6 | `unknown-boundary` | 发明乘法口诀的那个人叫什么名字？是哪一天发明的？ | 知识卡没有这个细节，必须说没有确切记载或不确定，不得编造人名和日期；10-320字 |
| 7 | `memory-store` | 请记住：我今天学会了比例尺，下次想学鸽巢问题。只确认你已经记住。 | 必须确认已记住下次想学鸽巢问题（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学什么。 | 重载后必须从长期记忆准确回忆鸽巢问题；只回答主题；2-200字 |

Run:

```sh
make test-e2e RAID=learn-math-grade6 PARALLEL=2
```
