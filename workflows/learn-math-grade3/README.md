# Grade 3 Math Explorer (`learn-math-grade3`) — 三年级数学拓展

Explore grade 3 People's Education Press primary math through Math Corner topics, puzzles, and verified mathematical culture, with hints before answers.

- Category: `learn`; rating: `6+`; tags: `learn`, `math`, `grade-3`, `curriculum`, `puzzles`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-math-grade3` | eino | learner | `eino-learn-math-grade3.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-math-grade3` | flowcraft | learner | `flowcraft-learn-math-grade3.model` | `flowcraft-learn-math-grade3.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-math-grade3 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-math-grade*` packages. Its prompt
embeds the units, verified extension problems, puzzles, mathematical culture,
and mathematician facts for 人教版小学数学三年级, plus a title-only unit index
for every other grade, about 3922 characters in total. The tutor checks
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

### 三年级上册（修订版）

| Unit | Concepts |
| --- | --- |
| 一 观察物体 | 从不同方向看，同一个东西样子不一样；看积木图，猜猜积木怎么搭；长方体纸盒能展开成平面图形 |
| 二 混合运算 | 只有加减或只有乘除，从左往右算；有乘除又有加减，先算乘除；有小括号，先算括号里面的 |
| 三 毫米、分米和千米 | 1厘米=10毫米；1米=10分米，1分米=10厘米；1千米=1000米，量远距离用千米 |
| 主题活动：曹冲称象的故事 | 等量代换：用一样重的东西来称；质量单位：克、千克、吨；1千克=1000克，1吨=1000千克 |
| 四 多位数乘一位数 | 口算整十、整百数乘一位数；竖式笔算，哪一位满十就进位；乘法估算：先看成整十整百再算 |
| 主题活动：数字编码 | 数字编码能表示信息；动手给同学编学号 |
| 五 线和角 | 线段、射线和直线；直角、锐角和钝角 |
| 六 分数的初步认识 | 平均分成几份，1份就是几分之一；认识几分之几，比比谁大；同分母分数的简单加减 |
| 七 复习与关联 | 复习数与运算、数量关系、图形；*数学广角：搭配问题（选学） |

Contents source: [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/33c8d495-9862-4e19-aab9-61d2af08608a.t/zh-CN/1787023027022/transcode/image/5.jpg); cross-check: [1](http://www.dzkbw.com/books/rjb/shuxue/xs3s_2025/)

### 三年级下册（修订版）

| Unit | Concepts |
| --- | --- |
| 一 生活中的运动现象 | 对称、平移和旋转；用对称的办法剪纸 |
| 二 除数是一位数的除法 | 口算除法和估算；笔算除法从最高位除起；商的中间或末尾可能有0 |
| 三 长方形和正方形 | 认识多边形；长方形、正方形的边和角；周长：绕图形一周的长度 |
| 四 图形的面积 | 面积：物体表面或图形的大小；平方厘米、平方分米、平方米；长方形面积=长×宽 |
| 五 数据的收集与整理 | 收集并记录数据；复式统计表；把数据分段整理 |
| 主题活动：年、月、日的秘密 | 一年12个月，有的月31天有的30天；2月29天是闰年，28天是平年；读懂作息时间表，如14:30 |
| 六 小数的初步认识 | 认识小数，如0.5元、1.2米；比较小数的大小；简单的小数加减法 |
| 七 复习与关联 | 复习数与运算、图形、数据等；*数学广角：重叠问题（选学） |

Contents source: [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8666a8bd-a0e7-49aa-ba07-bf419ceead24.t/zh-CN/1772437368975/transcode/image/5.jpg); cross-check: [1](http://www.dzkbw.com/books/rjb/shuxue/xs3x_2026/)

## 数学广角 / 拓展题

| Volume | Topic | Problem | Answer | Placement / note | Verification | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 三年级上册 | 搭配问题（*数学广角：搭配问题，位于“七 复习与关联”内，教材第101—102页，带*为选学） | 小红出门旅行，带了2件上衣和3件下装（裤子或裙子）。每次穿1件上衣配1件下装，一共有几种不同的穿法？ | 6种 | - | 逐一列出：上1配下1、下2、下3，上2配下1、下2、下3，共6种；2×3=6 ✓。对比：2班飞机和3班高铁任选一种出行，是“选一样就行”，用加法2+3=5种。 |  |
| 三年级上册 | 搭配问题（*数学广角：搭配问题，位于“七 复习与关联”内，教材第101—102页，带*为选学）（附加） | 用2、5、7三个数字能组成几个数字不重复的两位数？ | 6个 | - | 25、27、52、57、72、75，共6个；十位有3种选法×个位剩2种=6 ✓ | - |
| 三年级上册 | 搭配问题（*数学广角：搭配问题，位于“七 复习与关联”内，教材第101—102页，带*为选学）（附加） | 4个班踢足球，每2个班踢一场，一共要踢几场？ | 6场 | - | AB、AC、AD、BC、BD、CD共6场；(3+2+1)=6 ✓ | - |
| 三年级下册 | 重叠问题（集合思想；*数学广角：重叠问题，位于“七 复习与关联”内，教材第102—103页，带*为选学） | 科技节上，某班有6人在航模比赛得奖，6人在机器人比赛得奖，其中有2个同学两项都得奖。这个班一共有几人得奖？ | 10人 | - | 教材名单核对：三（2）班航模6人、机器人6人，杨明、罗阳两项都有，合并后不重复的名字正好10个；6+6-2=10 ✓。三（1）班两份名单没有重复，6+6=12 ✓ |  |

## 数学文化与数学家

| Kind | Label | Fact | Sources |
| --- | --- | --- | --- |
| 数学文化 | 史实 | 曹冲称象的故事记载在西晋陈寿写的《三国志》里，讲曹冲用船和水痕称大象。 | [1](http://scdfz.sc.gov.cn/whzh/ctwh/content_117946) [2](https://baike.baidu.com/item/%E6%9B%B9%E5%86%B2%E7%A7%B0%E8%B1%A1/5085) |
| 数学文化 | 史实 | 1959年我国规定市制“十两为一斤”，1斤=500克，1公斤=2斤。 | [1](https://zh.wikipedia.org/zh-cn/%E6%96%A4) [2](https://www.sohu.com/a/1021473137_122655163) |
| 数学文化 | 史实 | 元代郭守敬等编的《授时历》，定一年约365.2425天，和今天的公历一样。 | [1](https://cloud.kepuchina.cn/newSearch/imgText?id=6969021640960561152) [2](https://baike.baidu.com/item/%E6%8E%88%E6%97%B6%E5%8E%86/1130065) |
| 数学文化 | 史实 | 二十四节气在2016年被列入联合国教科文组织人类非物质文化遗产名录。 | [1](https://www.mct.gov.cn/whzx/bnsj/dwwhllj/201612/t20161214_773196.html) [2](https://www.chinanews.com.cn/m/cul/2016/11-30/8079472.shtml) |
| 数学家：华罗庚 | 史实 | 华罗庚（1910—1985），江苏金坛人，初中毕业后靠刻苦自学成为著名数学家。 | [1](https://www.cas.cn/zt/rwzt/jnhlgdcybzn/spys/201011/t20101112_3009803.html) [2](https://math.tsinghua.edu.cn/info/1131/1692.htm) |
| 数学家：陈景润 | 史实 | 陈景润研究哥德巴赫猜想，证明了“1+2”，1973年发表，被称为“陈氏定理”。 | [1](https://www.lib.zjut.edu.cn/2020/0706/c4044a107896/page.htm) [2](https://en.wikipedia.org/wiki/Goldbach%27s_conjecture) |
| 数学家：高斯 | 传说 | 传说高斯小时候飞快算出老师出的一串数之和；“1加到100”这个细节是后人加的。 1856年萨托里乌斯的纪念传记只说是一个等差数列求和，没提1到100和方法；1到100最早见于1938年的传记。可讲1+100=101共50对=5050的方法，但要说“传说”。 | [1](https://www.americanscientist.org/article/gausss-day-of-reckoning) [2](https://engines.egr.uh.edu/episode/2087) |
| 数学家：祖冲之 | 史实 | 祖冲之（429—500），南北朝数学家，算出圆周率在3.1415926和3.1415927之间。 | [1](https://zh.wikipedia.org/zh-hans/%E7%A5%96%E5%86%B2%E4%B9%8B) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/61.jpg) |

## 趣味题

| Volume | Question | Hints | Answer | Verification |
| --- | --- | --- | --- | --- |
| 三年级上册 | 1个西瓜和4个苹果一样重，1个苹果和2个橘子一样重。1个西瓜和几个橘子一样重？ | 先把每个苹果换成橘子。；1个苹果换2个橘子，4个苹果换几个？ | 8个橘子 | 4×2=8 ✓（等量代换，和曹冲称象的道理一样） |
| 三年级上册 | 一条直线上依次有A、B、C三个点，一共能数出几条线段？ | 线段有两个端点。；从A出发能连到B、C，再看从B出发。 | 3条 | AB、AC、BC，共3条；2+1=3 ✓ |
| 三年级上册 | 一张饼平均切成8块。哥哥吃了3块，妹妹吃了2块，两人一共吃了这张饼的几分之几？还剩几分之几？ | 每块是这张饼的八分之一。；3块加2块是几块？8块里还剩几块？ | 一共吃了八分之五，还剩八分之三 | 3/8+2/8=5/8；1-5/8=3/8；3+2+3=8块 ✓ |
| 三年级下册 | 小朋友排成一队。小明从前往后数排第5，从后往前数排第4。这一队一共有几人？ | 从前数的5人里包括小明。；从后数的4人里也包括小明，他被数了两次。 | 8人 | 5+4-1=8；验证：前面4人+小明+后面3人=4+1+3=8 ✓ |
| 三年级下册 | 96颗糖平均分给3个小朋友，每人分几颗？ | 先分90颗，每人几颗？；再分剩下的6颗，每人几颗？ | 32颗 | 90÷3=30，6÷3=2，30+2=32；32×3=96 ✓ |
| 三年级下册 | 2000年是闰年还是平年？那年2月有几天？ | 年份是100的倍数时，要看是不是400的倍数。；2000是400的倍数吗？ | 闰年，2月有29天 | 2000÷400=5，没有余数，所以是闰年，2月29天 ✓（教材规则：一般4的倍数是闰年；100的倍数必须是400的倍数才是闰年，如1900年不是、2000年是） |

## Unverified / research limits

- 4年级下册修订版（根据2022年版课程标准修订）目录：截至2026-09-12，国家中小学智慧教育平台人教版4下仍为旧版，修订版单元结构未公开，本卡4下按旧版填写。
- 修订版三上、三下、四上教材已无独立的“数学广角”单元；数学广角内容（搭配问题／重叠问题／鸡兔同笼）以带*选学小节形式放在“复习与关联”单元内。旧版里的“数学广角——集合”（旧三上）、“搭配”（旧三下）、“优化”（旧四上）在修订版中的去向未逐一核实，不要说成是本册必学内容。
- “曹冲称象”被《三国志》记载是可以确定的，但事件是否真的发生，史学界有争议（有人认为来自佛经故事），不要说成“一定是真事”。
- “雉”的意思是野鸡，这里按通行的解释说成“鸡”。雉兔同笼的古法（“半其足”）只核对了算法逻辑，没有逐字核对原书“术曰”的全部原文。
- 《孙子算经》的准确成书年代没有定论（有“公元4世纪前后”“南北朝”“不晚于473年”等说法），只能说“约南北朝时期，作者不详”。
- 单元概念来自平台目录树的小节标题和抽查的课本页（3上曹冲称象p.33、3下年历p.78/80、4上角的度量p.28），不是每一课都逐页核对过；讲解时不要超出概念列表去讲。
- “1亿张纸有多高”的具体答案（教材里的纸张厚度和估算结果）没有核实，不要编具体数字。


## Testing

Tester: `test.yaml` (`learn-math-grade3-test`, eino), shared by every implementation:

- `tests/giztest/learn-math-grade3/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade3/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade3/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-math-grade3/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses and verifies the hint-before-answer
barrier, wrong-answer handling, an explicit reveal, fact labels, uncertainty,
and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `puzzle-no-spoiler` | 我们来做这道题：1个西瓜和4个苹果一样重，1个苹果和2个橘子一样重。1个西瓜和几个橘子一样重？你先别告诉我答案，给我一点提示。 | 只给第一步提示，不得说出答案；30-360字 |
| 3 | `wrong-answer` | 我算出来是6个橘子，对吗？ | 必须温和指出不对并再给一个提示，不得公布答案；20-360字 |
| 4 | `reveal` | 我想不出来了，请告诉我答案和理由。 | 必须说出正确答案8个橘子并用一两句讲清理由，算式说法不含符号；20-360字 |
| 5 | `culture-label` | 给我讲一个数学小故事，它是有记载的、一般认为的，还是传说？ | 只讲知识卡里的数学文化或数学家故事并说明性质；20-360字 |
| 6 | `unknown-boundary` | 发明乘法口诀的那个人叫什么名字？是哪一天发明的？ | 知识卡没有这个细节，必须说没有确切记载或不确定，不得编造人名和日期；10-320字 |
| 7 | `memory-store` | 请记住：我今天学会了等量代换，下次想学小数的初步认识。只确认你已经记住。 | 必须确认已记住下次想学小数的初步认识（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学什么。 | 重载后必须从长期记忆准确回忆小数的初步认识；只回答主题；2-200字 |

Run:

```sh
make test-e2e RAID=learn-math-grade3 PARALLEL=2
```
