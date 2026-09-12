# Grade 5 Math Explorer (`learn-math-grade5`) — 五年级数学拓展

Explore grade 5 People's Education Press primary math through Math Corner topics, puzzles, and verified mathematical culture, with hints before answers.

- Category: `learn`; rating: `6+`; tags: `learn`, `math`, `grade-5`, `curriculum`, `puzzles`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-math-grade5` | eino | learner | `eino-learn-math-grade5.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-math-grade5` | flowcraft | learner | `flowcraft-learn-math-grade5.model` | `flowcraft-learn-math-grade5.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-math-grade5 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-math-grade*` packages. Its prompt
embeds the units, verified extension problems, puzzles, mathematical culture,
and mathematician facts for 人教版小学数学五年级, plus a title-only unit index
for every other grade, about 3900 characters in total. The tutor checks
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

### 五年级上册（修订版）

| Unit | Concepts |
| --- | --- |
| 一 观察简单组合体 | 从前面、上面、左面看小正方体搭的形状；根据看到的形状，把组合体搭出来 |
| 二 小数乘法 | 小数乘整数、小数乘小数；积有几位小数，看两个因数一共几位小数；整数的运算律也能用在小数上 |
| 三 小数除法 | 除数是整数的小数除法；除数是小数：先把除数变成整数再除；循环小数：如1÷3=0.333… |
| 四 图形的运动 | 轴对称：对应点到对称轴距离相等；平移和旋转的特征及画法；用图形的运动设计图案 |
| 五 用字母表示数和数量关系 | 用字母表示数，如爸爸年龄=a+25；用字母写运算律和公式 |
| 六 多边形的面积 | 平行四边形面积=底×高；三角形=底×高÷2，梯形=(上底+下底)×高÷2；1公顷=10000平方米，1平方千米=100公顷 |
| 有趣的密铺 | 密铺：图形不重叠、没空隙地铺满平面；正五边形不能密铺，角拼不成360° |
| 七 可能性 | 有的事一定发生，有的不可能、有的可能；可能性有大有小 |
| 八 复习与关联 | 整理本学期学过的知识；选学：数学广角·植树问题 |

Contents source: [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/d0d6252f-2233-4f66-9ac9-440638d56fec.t/zh-CN/1787023028106/transcode/image/5.jpg); cross-check: [1](http://www.dzkbw.com/books/rjb/shuxue/xs5s_2026/) [2](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=d0d6252f-2233-4f66-9ac9-440638d56fec)

### 五年级下册（旧版）

| Unit | Concepts |
| --- | --- |
| 1 观察物体（三） | 根据从一个方向看到的形状，想想怎么搭 |
| 2 因数和倍数 | 12=3×4，3和4是12的因数，12是它们的倍数；个位是0、2、4、6、8的是2的倍数；质数只有1和它本身两个因数 |
| 3 长方体和正方体 | 长方体有6个面、12条棱、8个顶点；表面积是6个面的面积和；长方体体积=长×宽×高 |
| 探索图形 | 大正方体表面涂色，数小正方体的规律 |
| 4 分数的意义和性质 | 把单位“1”平均分，表示其中几份；分子分母同乘或同除一个数，大小不变；约分和通分 |
| 5 图形的运动（三） | 图形绕一个点旋转，如顺时针转90° |
| 6 分数的加法和减法 | 同分母分数：分母不变，分子相加减；异分母分数：先通分再算 |
| 怎样通知最快 | 每分钟通知1人，设计最快的通知方案 |
| 7 折线统计图 | 折线图能看出数量增减变化；复式折线图可以比较两组数据 |
| 8 数学广角——找次品 | 用天平找出轻一点的次品；分成3份来称，次数最少 |
| 9 总复习 | 整理全册学过的知识 |

Contents source: [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/83339b94-2b33-4a9b-ba0e-026b4fdd4f0e.t/zh-CN/1772437370495/transcode/image/5.jpg%20;%20https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/83339b94-2b33-4a9b-ba0e-026b4fdd4f0e.t/zh-CN/1772437370495/transcode/image/6.jpg); cross-check: [1](http://www.dzkbw.com/books/rjb/shuxue/xs5x_new/) [2](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=83339b94-2b33-4a9b-ba0e-026b4fdd4f0e)

## 数学广角 / 拓展题

| Volume | Topic | Problem | Answer | Placement / note | Verification | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 五年级上册 | 植树问题 | 在一条100米长的小路一边种树，每隔5米种一棵，两头都要种，一共种几棵？ | 21棵 | 八 复习与关联 内，标“*数学广角：植树问题”（选学），课本第116—117页 | 100÷5=20（段）；两端都种：20+1=21（棵）。小例验证：20÷5=4段，树5棵=4+1。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/d0d6252f-2233-4f66-9ac9-440638d56fec.t/zh-CN/1787023028106/transcode/image/121.jpg) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/d0d6252f-2233-4f66-9ac9-440638d56fec.t/zh-CN/1787023028106/transcode/image/122.jpg) |
| 五年级下册 | 找次品 | 8个零件里有1个是次品，比别的轻一点。用天平称，至少称几次能保证找出它？ | 至少2次 | 第8单元 数学广角——找次品，课本第112—114页 | 第1次后最坏剩3个；第2次在3个中称1比1即可确定。1次最多分辨3个（3<8），2次最多分辨3×3=9个（8≤9），所以最少2次。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/83339b94-2b33-4a9b-ba0e-026b4fdd4f0e.t/zh-CN/1772437370495/transcode/image/117.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/83339b94-2b33-4a9b-ba0e-026b4fdd4f0e.t/zh-CN/1772437370495/transcode/image/118.jpg) |

## 数学文化与数学家

| Kind | Label | Fact | Sources |
| --- | --- | --- | --- |
| 数学文化 | 史实 | 刘徽给《九章算术》作注时用“出入相补”：把图形割开再拼，面积不变。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/d0d6252f-2233-4f66-9ac9-440638d56fec.t/zh-CN/1787023028106/transcode/image/87.jpg) [2](https://zh.wikipedia.org/zh-hans/%E5%87%BA%E5%85%A5%E7%9B%B8%E8%A1%A5) |
| 数学文化 | 史实 | 格点多边形面积=内部点数+边上点数÷2−1，叫皮克定理，1899年皮克提出。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/d0d6252f-2233-4f66-9ac9-440638d56fec.t/zh-CN/1787023028106/transcode/image/96.jpg) [2](https://en.wikipedia.org/wiki/Pick%27s_theorem) |
| 数学文化 | 史实 | 荷兰艺术家埃舍尔用密铺原理创作了《天空和水》，鸟和鱼拼满画面。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/d0d6252f-2233-4f66-9ac9-440638d56fec.t/zh-CN/1787023028106/transcode/image/102.jpg) [2](https://en.wikipedia.org/wiki/Sky_and_Water_I) |
| 数学文化 | 史实 | 1742年哥德巴赫在给欧拉的信里提出哥德巴赫猜想，至今还没有被证明。 | [1](https://en.wikipedia.org/wiki/Goldbach%27s_conjecture) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/83339b94-2b33-4a9b-ba0e-026b4fdd4f0e.t/zh-CN/1772437370495/transcode/image/22.jpg) |
| 数学文化 | 史实 | 6=1+2+3，像6、28、496、8128这样的数叫完全数。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/83339b94-2b33-4a9b-ba0e-026b4fdd4f0e.t/zh-CN/1772437370495/transcode/image/13.jpg) [2](https://en.wikipedia.org/wiki/Perfect_number) |
| 数学文化 | 史实 | 《九章算术》“方田”章里就记载了约分的方法，叫“约分术”。 | [1](https://zh.wikipedia.org/zh-cn/%E4%B9%9D%E7%AB%A0%E7%AE%97%E6%9C%AF) [2](https://baike.baidu.com/item/%E7%BA%A6%E5%88%86%E6%9C%AF/3312409) |
| 数学家：华罗庚 | 史实 | 华罗庚（1910—1985），江苏金坛人，初中毕业后靠刻苦自学成为著名数学家。 | [1](https://www.cas.cn/zt/rwzt/jnhlgdcybzn/spys/201011/t20101112_3009803.html) [2](https://math.tsinghua.edu.cn/info/1131/1692.htm) |
| 数学家：陈景润 | 史实 | 陈景润研究哥德巴赫猜想，证明了“1+2”，1973年发表，被称为“陈氏定理”。 | [1](https://www.lib.zjut.edu.cn/2020/0706/c4044a107896/page.htm) [2](https://en.wikipedia.org/wiki/Goldbach%27s_conjecture) |
| 数学家：高斯 | 传说 | 传说高斯小时候飞快算出老师出的一串数之和；“1加到100”这个细节是后人加的。 1856年萨托里乌斯的纪念传记只说是一个等差数列求和，没提1到100和方法；1到100最早见于1938年的传记。可讲1+100=101共50对=5050的方法，但要说“传说”。 | [1](https://www.americanscientist.org/article/gausss-day-of-reckoning) [2](https://engines.egr.uh.edu/episode/2087) |
| 数学家：祖冲之 | 史实 | 祖冲之（429—500），南北朝数学家，算出圆周率在3.1415926和3.1415927之间。 | [1](https://zh.wikipedia.org/zh-hans/%E7%A5%96%E5%86%B2%E4%B9%8B) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/845136d4-e27b-4e7e-b9a9-00cadf4f9e20.t/zh-CN/1787023028637/transcode/image/61.jpg) |

## 趣味题

| Volume | Question | Hints | Answer | Verification |
| --- | --- | --- | --- | --- |
| 五年级上册 | 我想了一个数，先乘10，再除以100，得到0.35。我想的数是多少？ | 倒着想：最后一步是除以100。；0.35乘100，得到35。；35再除以10，就是原来的数。 | 3.5 | 3.5×10=35，35÷100=0.35，正确。 |
| 五年级上册 | 把一根木头锯成4段，每锯一次要3分钟，一共要锯几分钟？ | 锯成4段，要锯几次？；段数比锯的次数多1，所以锯3次。；3次，每次3分钟。 | 9分钟 | 4−1=3（次），3×3=9（分钟）。 |
| 五年级上册 | 正五边形的每个角是108度。把三个正五边形的角拼在一个点上，一共多少度？够一圈360度吗？ | 算108×3。；108×3=324。；和360比一比，差多少？ | 324度，比360度少36度，会留空隙，所以正五边形不能密铺。 | 108×3=324<360；108×4=432>360会重叠，所以拼不成正好360度。 |
| 五年级下册 | 我是一个两位数，同时是2、3、5的倍数，而且是这样的数里最小的。我是几？ | 2和5的倍数，个位一定是0。；个位是0的两位数：10、20、30……；再看各位数字加起来是不是3的倍数。 | 30 | 30÷2=15，30÷3=10，30÷5=6；10（1+0=1）和20（2+0=2）都不是3的倍数。 |
| 五年级下册 | 一个蛋糕，哥哥吃了二分之一，妹妹吃了四分之一，还剩几分之几？ | 二分之一等于四分之二。；两人一共吃了四分之三。；整个蛋糕是1，减去四分之三。 | 四分之一 | 1/2+1/4=2/4+1/4=3/4，1−3/4=1/4。 |
| 五年级下册 | 9个一模一样的小球，有1个稍轻一点。用天平至少称几次，一定能找出轻的那个？ | 把9个分成3、3、3三份。；称两份：平了，轻球在第三份；不平，在轻的那边。；剩下3个，再称一次1比1就知道了。 | 2次 | 9=3×3；1次最多分辨3个（3<9），2次最多分辨9个（9≤9），所以至少2次。 |

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

Tester: `test.yaml` (`learn-math-grade5-test`, eino), shared by every implementation:

- `tests/giztest/learn-math-grade5/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade5/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-math-grade5/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-math-grade5/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses and verifies the hint-before-answer
barrier, wrong-answer handling, an explicit reveal, fact labels, uncertainty,
and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `puzzle-no-spoiler` | 我们来做这道题：在一条100米长的小路一边种树，每隔5米种一棵，两头都要种，一共种几棵？你先别告诉我答案，给我一点提示。 | 只给第一步提示，不得说出答案；30-360字 |
| 3 | `wrong-answer` | 我算出来是20棵，对吗？ | 必须温和指出不对并再给一个提示，不得公布答案；20-360字 |
| 4 | `reveal` | 我想不出来了，请告诉我答案和理由。 | 必须说出正确答案21棵并用一两句讲清理由，算式说法不含符号；20-360字 |
| 5 | `culture-label` | 给我讲一个数学小故事，它是有记载的、一般认为的，还是传说？ | 只讲知识卡里的数学文化或数学家故事并说明性质；20-360字 |
| 6 | `unknown-boundary` | 发明乘法口诀的那个人叫什么名字？是哪一天发明的？ | 知识卡没有这个细节，必须说没有确切记载或不确定，不得编造人名和日期；10-320字 |
| 7 | `memory-store` | 请记住：我今天学会了植树问题，下次想学找次品。只确认你已经记住。 | 必须确认已记住下次想学找次品（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学什么。 | 重载后必须从长期记忆准确回忆找次品；只回答主题；2-200字 |

Run:

```sh
make test-e2e RAID=learn-math-grade5 PARALLEL=2
```
