# Chinese Story Time (`learn-chinese-stories`) — 语文故事

Explore verified primary Chinese textbook stories through classical texts, fables, idiom origins, and Happy Reading selections.

- Category: `learn`; rating: `6+`; tags: `learn`, `chinese`, `stories`, `classical`, `curriculum`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-chinese-stories` | eino | learner | `eino-learn-chinese-stories.model` | `eino-learn-chinese-stories.tutor` |
| `flowcraft.yaml` | `flowcraft-learn-chinese-stories` | flowcraft | learner | `flowcraft-learn-chinese-stories.model` | `flowcraft-learn-chinese-stories.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-chinese-stories --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This single all-grades raid covers 统编版小学语文一至六年级文言文、寓言与
成语故事，以及快乐读书吧书目. Its generated prompt is 7032
characters. Spoken cards omit URLs, page numbers, research notes, and empty
book lists; exact duplicate spoken lines are removed. Summaries and classical
source texts are kept whole, so the tutor never has to guess an unfinished story.

[`knowledge.json`](knowledge.json) is the normalized source of truth and retains
every placement, source, note, label, copyright, and unverified field from the
research input. Copyright works may only be introduced by broad plot and main
characters, never recited or reproduced in extended form. 统编版小学语文；修订版（根据2022年版课程标准修订）用于一至三年级上下册和四至六年级上册，四至六年级下册为平台现行版本。修订版六年级上册第20课文言文二则为《两小儿辩日》《曹冲称象》，《伯牙鼓琴》《书戴嵩画牛》只见于旧版。

## 文言文

| Title | Source / Author | Placement | Label | Gist / Moral | Sources |
| --- | --- | --- | --- | --- | --- |
| 《司马光》 | 《宋史·司马光传》 / - | 三年级上册；第23课；修订版 | 史实 | 小孩掉进大水缸，大家都跑了，司马光用石头砸破缸救出了他。；遇事冷静，开动脑筋 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/101.jpg) [2](https://www.gushiwen.cn/shiwenv_d08246ab36e2.aspx) [3](https://zh.wikisource.org/wiki/宋史/卷336) |
| 《守株待兔》 | 《韩非子·五蠹》 / 韩非 | 三年级下册；第5课；修订版 | 寓言 | 农夫捡到撞死在树桩上的兔子，从此不种地天天守着，被人笑话。；不能靠侥幸，要靠努力 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/21.jpg) [2](https://www.gushiwen.cn/shiwenv_bf758d053fca.aspx) [3](https://zh.wikisource.org/wiki/韓非子/五蠹) |
| 《精卫填海》 | 《山海经·北山经》 / - | 四年级上册；第12课；修订版 | 传说 | 炎帝小女儿在东海淹死，化作精卫鸟，天天衔来树枝石子填海。；意志坚定，坚持不懈 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/55.jpg) [2](https://www.gushiwen.cn/shiwenv_1104052ed0fc.aspx) [3](https://zh.wikisource.org/wiki/山海經/北山經) |
| 《王戎不取道旁李》 | 《世说新语·雅量》 / 刘义庆（编） | 四年级上册；第23课；修订版 | 通说 | 路边李子压弯了树枝，王戎推断没人摘必是苦李，一尝果然。；遇事善于观察和推理 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/107.jpg) [2](https://www.gushiwen.cn/shiwenv_cfeddc2459c2.aspx) [3](https://zh.wikisource.org/wiki/世說新語/雅量) |
| 《囊萤夜读》 | 《晋书·车胤传》 / - | 四年级下册；第18课 文言文二则；旧版 | 史实 | 车胤家穷买不起灯油，夏夜用绢袋装萤火虫照明读书。；刻苦勤学，不怕条件差 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/81.jpg) [2](https://www.gushiwen.cn/shiwenv_a640d462c006.aspx) [3](https://zh.wikisource.org/wiki/晉書/卷083) |
| 《铁杵成针》 | 宋·祝穆《方舆胜览·眉州》 / - | 四年级下册；第18课 文言文二则；旧版 | 传说 | 李白读书半途放弃，见老婆婆要把铁杵磨成针，受感动回去完成学业。；有恒心，坚持就能成功 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/81.jpg) [2](https://www.gushiwen.cn/shiwenv_9236b601a746.aspx) |
| 《自相矛盾》 | 《韩非子·难一》 / 韩非 | 五年级下册；第15课；旧版 | 寓言 | 卖矛和盾的人把两样都夸成天下第一，被问“用你的矛刺你的盾”答不上来。；说话做事要前后一致 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/89.jpg) [2](https://www.gushiwen.cn/shiwenv_d52e05980359.aspx) [3](https://zh.wikisource.org/wiki/韓非子/難一) |
| 《杨氏之子》 | 《世说新语·言语》 / 刘义庆（编） | 五年级下册；第21课；旧版 | 通说 | 孔君平拿杨梅开玩笑说是杨家的果，九岁孩子巧答孔雀不是孔家的鸟。；说话机智又有礼貌 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/113.jpg) [2](https://www.gushiwen.cn/shiwenv_af4715c0208f.aspx) [3](https://zh.wikisource.org/wiki/世說新語/言語) |
| 《伯牙鼓琴》 | 《吕氏春秋·本味》 / - | 六年级上册；第21课 文言文二则；旧版(2019) | 通说 | 锺子期听得懂伯牙琴中的高山流水，子期死后伯牙摔琴不再弹。；知音难得，珍惜真朋友 | [1](https://www.haoduoyun.cc/book/rjb/yuwen/6s/99.shtml) [2](https://www.gushiwen.cn/shiwenv_a00028c4f0be.aspx) [3](https://zh.wikisource.org/wiki/呂氏春秋/卷十四) |
| 《书戴嵩画牛》 | 苏轼文集（东坡题跋） / 苏轼 | 六年级上册；第21课 文言文二则；旧版(2019) | 通说 | 杜处士珍藏戴嵩斗牛图，牧童指出斗牛时尾巴夹紧，画成摇尾是错的。；实践出真知，要虚心请教 | [1](https://www.haoduoyun.cc/book/rjb/yuwen/6s/100.shtml) [2](https://www.gushiwen.cn/shiwenv_7c170d5debdf.aspx) [3](https://zh.wikisource.org/wiki/書戴嵩畫牛) |
| 《两小儿辩日》 | 《列子·汤问》 / - | 六年级上册；第20课 文言文二则；修订版 / 六年级下册；第14课 文言文二则；旧版 | 寓言 | 两个孩子争论太阳早上近还是中午近，各有理由，孔子也判断不了。；知识无穷，要敢于探索 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/103.jpg) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/86.jpg) [3](https://www.gushiwen.cn/shiwenv_b4a451fa375a.aspx) [4](https://zh.wikisource.org/wiki/列子/湯問篇) |
| 《曹冲称象》 | 《三国志·魏书·邓哀王冲传》 / 陈寿 | 六年级上册；第20课 文言文二则；修订版 | 史实 | 孙权送来大象，曹冲想出用船和水痕刻记号、称等重货物来称象。；善于思考，巧妙解决难题 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/104.jpg) [2](https://www.gushiwen.cn/shiwenv_31b814913b16.aspx) [3](https://zh.wikisource.org/wiki/三國志/卷20) |
| 《学弈》 | 《孟子·告子上》 / 孟子 | 六年级下册；第14课 文言文二则；旧版 | 寓言 | 两人跟围棋高手弈秋学棋，一人专心，一人想射天鹅，后者学得差。；学习要专心致志 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/85.jpg) [2](https://www.gushiwen.cn/shiwenv_7dddb391682f.aspx) [3](https://zh.wikisource.org/wiki/孟子/告子上) |
| 《古人谈读书》 | 《论语》；朱熹（《训学斋规》） / 孔子及弟子；朱熹 | 五年级上册；第23课；修订版 | 非故事(论说) | 五则论语谈求学态度；朱熹说读书要心到、眼到、口到，心到最要紧。；读书要虚心、勤学、专心 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/107.jpg) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/108.jpg) [3](https://www.gushiwen.cn/shiwenv_04f7c4ccfa13.aspx) [4](https://www.gushiwen.cn/shiwenv_8074b3dafa95.aspx) [5](https://zh.wikisource.org/wiki/論語/述而第七) |
| 《少年中国说（节选）》 | 梁启超《少年中国说》(1900) / 梁启超 | 五年级上册；第12课；修订版 | 非故事(浅近文言) | 梁启超号召少年担起责任：少年强则国强，赞美少年中国前途无量。；少年要担当，奋发图强 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/59.jpg) [2](https://www.gushiwen.cn/shiwenv_9ebe5eef393d.aspx) [3](https://zh.wikisource.org/wiki/少年中國說) |

## 寓言与课文故事

| Title | Placement | Label | Idiom | Gist / Moral | Sources |
| --- | --- | --- | --- | --- | --- |
| 《坐井观天》 | 二年级上册；第11课；修订版 | 寓言 | 坐井观天 | 井里的青蛙以为天只有井口大，小鸟说天无边无际，劝它跳出来看。；眼界要开阔，别自以为是 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/59.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/60.jpg) |
| 《寒号鸟》 | 二年级上册；第12课；修订版 | 寓言 | - | 寒号鸟不听喜鹊劝告，总说“明天就做窝”，最后冬夜冻死了。；做事要趁早，不能懒惰拖延 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/61.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/63.jpg) |
| 《我要的是葫芦》 | 二年级上册；第13课；修订版 | 寓言 | - | 种葫芦的人只盯着葫芦，不治叶上蚜虫，结果小葫芦全落了。；事物互相联系，要全面看问题 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/65.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/66.jpg) |
| 《亡羊补牢》 | 二年级下册；第11课 寓言二则；修订版 | 寓言 | 亡羊补牢 | 羊圈破洞被狼叼走羊，他起初不修，又丢一只后赶紧修好，再没丢羊。；出了错及时改正还不晚 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/60.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/61.jpg) [3](https://zh.wikisource.org/wiki/戰國策) |
| 《揠苗助长》 | 二年级下册；第11课 寓言二则；修订版 | 寓言 | 揠苗助长（拔苗助长） | 有人嫌禾苗长得慢，把禾苗一棵棵往上拔，第二天禾苗全枯死了。；不能违背规律，急于求成 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/61.jpg) [2](https://zh.wikisource.org/wiki/孟子/公孫丑上) |
| 《小马过河》 | 二年级下册；第13课；修订版 | 寓言 | - | 小马驮麦过河，老牛说水浅、松鼠说水深，妈妈让它自己试，才知河水不深也不浅。；遇事要动脑筋，亲自试一试 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/66.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/67.jpg) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/68.jpg) |
| 《会摇尾巴的狼》 | 三年级下册；第6课；修订版 | 寓言 | - | 掉进陷阱的狼冒充狗骗老山羊救它，被老山羊识破。；要识破花言巧语，不上坏人的当 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/23.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/24.jpg) |
| 《鹿角和鹿腿》 | 三年级下册；第7课；修订版 | 寓言 | - | 鹿嫌腿细爱角美，逃命时角被树枝挂住，却靠长腿逃出狮口。；各有长处，不能只看外表 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/26.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/27.jpg) |
| 《池子与河流》 | 三年级下册；第8课；修订版 | 寓言 | - | 池子笑河流太忙，自己安闲；河流奔流不息受人尊敬，池子最终枯干。；才能不用就会衰退 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/28.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/31.jpg) |
| 《将相和》 | 五年级上册；第5课；修订版 | 史实 | 完璧归赵、负荆请罪 | 蔺相如完璧归赵、渑池会上护赵王，廉颇不服后负荆请罪，将相和好。；以国家为重，知错就改 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/22.jpg) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/24.jpg) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/25.jpg) [4](https://zh.wikisource.org/wiki/史記/卷081) |

## 成语出处

| Idiom | Placement | Origin | Meaning / Story | Sources |
| --- | --- | --- | --- | --- |
| 掩耳盗铃 | 三年级下册；语文园地二·日积月累；修订版 | 《吕氏春秋·自知》 | 自己欺骗自己；有人偷大钟，怕钟响被人听见，就捂住自己的耳朵。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/太平御覽/0499) |
| 杞人忧天 | 三年级下册；语文园地二·日积月累；修订版 | 《列子·天瑞》 | 为不必要的事担忧；杞国有人担心天塌地陷，吃不下饭睡不着觉。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/列子/天瑞篇) |
| 邯郸学步 | 三年级下册；语文园地二·日积月累；修订版 | 《庄子·秋水》 | 模仿不成反丢本领；燕国少年到邯郸学走路，没学会还忘了原来的走法，爬着回家。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/莊子/秋水) |
| 自相矛盾 | 三年级下册；语文园地二·日积月累；修订版 | 《韩非子·难一》 | 言行前后抵触；卖矛又卖盾的人夸两样都天下无敌，被问住了。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/韓非子/難一) |
| 刻舟求剑 | 三年级下册；语文园地二·日积月累；修订版 | 《吕氏春秋·察今》 | 拘泥不知变通；楚人剑掉进江里，在船边刻记号，船停后照记号下水找剑。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/呂氏春秋/卷十五) |
| 滥竽充数 | 三年级下册；语文园地二·日积月累；修订版 | 《韩非子·内储说上》 | 没本事混在行家里；南郭先生不会吹竽混在三百人乐队里，新王要一个个听，他逃了。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/韓非子/內儲說上) |
| 井底之蛙 | 三年级下册；语文园地二·日积月累；修订版 | 《庄子·秋水》 | 见识短浅的人；浅井里的青蛙向东海大鳖夸井中快乐，听了大海的样子惊呆了。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/莊子/秋水) |
| 杯弓蛇影 | 三年级下册；语文园地二·日积月累；修订版 | 东汉应劭《风俗通义》；《晋书·乐广传》 | 疑神疑鬼自相惊扰；客人把墙上弓在酒杯里的倒影当成蛇，吓病了，弄明白后病好了。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/隨園隨筆/卷25) |
| 画蛇添足 | 三年级下册；语文园地二·日积月累；修订版 | 《战国策·齐策二》 | 多此一举，弄巧成拙；几人比赛画蛇赢酒，先画完的人给蛇添上脚，酒被别人喝了。 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/35.jpg) [2](https://zh.wikisource.org/wiki/戰國策) |
| 狡兔三窟 | 五年级上册；语文园地一·日积月累；修订版 | 《战国策·齐策四》 | 藏身之处多、有退路；冯谖对孟尝君说狡兔有三个洞才能免死，并为他再造两窟。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/17.jpg) [2](https://zh.wikisource.org/wiki/馮諼客孟嘗君) |
| 呆若木鸡 | 五年级上册；语文园地一·日积月累；修订版 | 《庄子·达生》 | 因惊恐而发愣；纪渻子为王养斗鸡，养到像木头鸡，别的鸡见了都逃走。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/17.jpg) [2](https://zh.wikisource.org/wiki/莊子/達生) |
| 黔驴技穷 | 五年级上册；语文园地一·日积月累；修订版 | 唐·柳宗元《黔之驴》 | 本领用完了；老虎起初怕驴，后来发现它只会踢，就吃掉了它。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/17.jpg) [2](https://zh.wikisource.org/wiki/黔之驢) |
| 如鱼得水 | 五年级上册；语文园地一·日积月累；修订版 | 《三国志·蜀书·诸葛亮传》 | 得到投合的人或环境；刘备说自己有了孔明，就像鱼有了水。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/17.jpg) [2](https://zh.wikisource.org/wiki/諸葛亮集_%28張澍%29/諸葛亮傳) |
| 鹤立鸡群 | 五年级上册；语文园地一·日积月累；修订版 | 《世说新语·容止》 | 才能仪表出众；有人对王戎说嵇绍在人群中像野鹤站在鸡群里。 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/17.jpg) [2](https://zh.wikisource.org/wiki/世說新語/容止) |

## 快乐读书吧

| Placement / Theme | Book / Author | Copyright | Gist / Character | Sources |
| --- | --- | --- | --- | --- |
| 一年级上册；读书真快乐 | - | - | 课本未点名具体书目 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/1c73b348-e8b6-47d6-84b0-6dbacbe28268.t/zh-CN/1787022982266/transcode/image/24.jpg) |
| 一年级下册；读读童谣和儿歌 | - | - | 未点名书目；示例童谣《摇摇船》（传统童谣）、儿歌《小刺猬理发》（鲁兵） | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b87e153f-a64c-451a-aa6c-6ed9ac7d6821.t/zh-CN/1772437264666/transcode/image/20.jpg) |
| 二年级上册；读读童话故事 | - | - | 修订版未点名书目，只教看封面、书名和作者 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2ce8f153-7bff-4c97-b6db-9aac414fea19.t/zh-CN/1787022982823/transcode/image/20.jpg) |
| 二年级下册；读读儿童故事 | - | - | 修订版未点名书目，只示范看目录 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/33.jpg) |
| 三年级上册；在那奇妙的王国里 | 《安徒生童话》；安徒生（丹麦） | 公版 | 丹麦作家安徒生的童话集，有拇指姑娘、卖火柴的小女孩、丑小鸭等。；拇指姑娘 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/62.jpg) |
| 三年级上册；在那奇妙的王国里 | 《稻草人》；叶圣陶 | 版权作品 | 叶圣陶的童话，写夜间田野的景象和田野里人们的辛苦与悲伤。；稻草人 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/63.jpg) |
| 三年级上册；在那奇妙的王国里 | 《格林童话》；格林兄弟（德国） | 公版 | 格林兄弟搜集整理的故事，如灰姑娘心怀美好、小裁缝智胜巨人。；灰姑娘 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/63.jpg) |
| 三年级下册；小故事大道理 | 《中国古代寓言》；（古代各家） | 公版 | 短小寓言藏大道理，课本示例《叶公好龙》（据《新序·杂事》改写）。；叶公 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/36.jpg) |
| 三年级下册；小故事大道理 | 《伊索寓言》；伊索（古希腊） | 公版 | 多为动物故事，如吃不到葡萄说葡萄酸的狐狸。；狐狸 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/37.jpg) |
| 三年级下册；小故事大道理 | 《拉封丹寓言》；拉封丹（法国） | 公版 | 很多故事似曾相识，却被赋予新的意义。；- | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/37.jpg) |
| 三年级下册；小故事大道理 | 《克雷洛夫寓言》；克雷洛夫（俄国） | 公版 | 俄国寓言，课文《池子与河流》即出自克雷洛夫。；池子与河流 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/37.jpg) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/28.jpg) |
| 四年级上册；很久很久以前 | 《中国神话（泛指）》；（民间流传） | 公版 | 课本示例神农尝百草：神农亲尝百草辨药性，被称为医药之神。；神农 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/64.jpg) |
| 四年级上册；很久很久以前 | 《世界神话传说（泛指）》；（各国流传） | 公版 | 古希腊、北欧、美洲神话，如大力士赫拉克勒斯、火神洛基。；赫拉克勒斯 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd7e623-5c38-4602-871a-3fba8a551db2.t/zh-CN/1787022983961/transcode/image/65.jpg) |
| 四年级下册；探索科学的奥秘（旧版目录作“十万个为什么”） | 《十万个为什么》；米·伊林（苏联） | 公版 | 用生活中的小问题，如水为什么能灭火，引人探索科学。；- | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/38.jpg) |
| 四年级下册；探索科学的奥秘（旧版目录作“十万个为什么”） | 《看看我们的地球》；李四光 | 公版 | 地质学家李四光写给大众的地球科普。；- | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/39.jpg) |
| 四年级下册；探索科学的奥秘（旧版目录作“十万个为什么”） | 《灰尘的旅行》；高士其 | 版权作品 | 科学家高士其的科普作品。；- | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/39.jpg) |
| 四年级下册；探索科学的奥秘（旧版目录作“十万个为什么”） | 《人类起源的演化过程》；贾兰坡 | 版权作品 | 古人类学家贾兰坡的科普作品。；- | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/39.jpg) |
| 五年级上册；从前有座山 | 《中国民间故事（泛指）》；（民间流传） | 公版 | 课本示例《田螺姑娘》：勤劳青年捡回田螺，家里饭菜总有人做好。；田螺姑娘 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/54.jpg) |
| 五年级上册；从前有座山 | 《欧洲民间故事（泛指）》；（民间流传） | 公版 | 小牧羊人寻找会唱歌的苹果，狡猾幽默的列那狐捉弄其他动物。；列那狐 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/55.jpg) |
| 五年级上册；从前有座山 | 《非洲民间故事（泛指）》；（民间流传） | 公版 | 领唱讲故事，如鳄鱼幻想晒太阳长出翅膀、大象坚持回乡。；鳄鱼 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/55.jpg) |
| 五年级下册；读古典名著，品百味人生 | 《西游记》；吴承恩（明） | 公版 | 唐僧师徒四人西天取经，一路降妖除魔，如三调芭蕉扇。；孙悟空 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/44.jpg) |
| 五年级下册；读古典名著，品百味人生 | 《三国演义》；罗贯中（元末明初） | 公版 | 三国纷争的故事，如煮酒论英雄、火烧赤壁、千里走单骑。；诸葛亮 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/45.jpg) |
| 五年级下册；读古典名著，品百味人生 | 《水浒传》；施耐庵（元末明初） | 公版 | 梁山好汉的故事，如鲁智深倒拔垂杨柳、吴用智取生辰纲。；鲁智深 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/45.jpg) |
| 五年级下册；读古典名著，品百味人生 | 《红楼梦》；曹雪芹（清） | 公版 | 贾府盛衰与宝玉、黛玉等人的命运，如黛玉葬花。；林黛玉 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/45.jpg) |
| 六年级上册；笑与泪，经历与成长 | 《童年》；高尔基（苏联） | 公版 | 阿廖沙丧父后寄居暴躁的外祖父家，慈祥的外祖母保护他成长。；阿廖沙 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/72.jpg) |
| 六年级上册；笑与泪，经历与成长 | 《小英雄雨来》；管桦 | 版权作品 | 抗日战争中雨来掩护交通员、送鸡毛信，最终参加游击队。；雨来 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/73.jpg) |
| 六年级下册；漫步世界名著花园 | 《鲁滨逊漂流记》；丹尼尔·笛福（英国） | 公版 | 鲁滨逊流落荒岛二十八年，靠勇气和劳动生存下来。；鲁滨逊 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/46.jpg) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/25.jpg) |
| 六年级下册；漫步世界名著花园 | 《骑鹅旅行记》；塞尔玛·拉格洛芙（瑞典） | 公版 | 书中字里行间有怀乡之情（课本语）。；- | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/47.jpg) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/32.jpg) |
| 六年级下册；漫步世界名著花园 | 《汤姆·索亚历险记》；马克·吐温（美国） | 公版 | 书中有对自由的向往和对社会的讽刺（课本语）。；汤姆·索亚 | [1](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/47.jpg) [2](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/38.jpg) |

## Unverified / research limits

| Item | Status | Sources |
| --- | --- | --- |
| 6上修订版是否仍有伯牙鼓琴、书戴嵩画牛 | 已核：修订版目录第七单元为“20 文言文二则：两小儿辩日、曹冲称象”，两篇只见于2019旧版 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/5.jpg) |
| 古人谈读书、少年中国说的旧版(2019)课次 | 未核，仅记录修订版课次 | - |
| 5上语文园地一其余成语（凤毛麟角、如虎添翼、狼狈为奸、抱头鼠窜、虾兵蟹将、一马当先等）的出处故事 | 出处复杂或无单一公认故事，未收 | [1](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/17.jpg) |
| 1下、2上/2下快乐读书吧旧版推荐书目（如《一起长大的玩具》） | 修订版页面未点名书名，不收 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/33.jpg) |
| 画杨桃、纸船和风筝 | 核对课文：前者为岑桑写实故事，后者为童话，均非寓言/成语故事，不收 | [1](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/0f93b83e-b3c2-4a5d-8acd-ea460ab962d4.t/zh-CN/1772437265301/transcode/image/63.jpg) |
| 曹冲称象真实性 | 《三国志》有载；学界有疑其源自佛经故事之说，本卡未核实细节，讲述时说“史书记载” | - |


## Testing

Tester: `test.yaml` (`learn-chinese-stories-test`, eino), shared by every implementation:

- `tests/giztest/learn-chinese-stories/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-stories/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-stories/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-chinese-stories/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses and verifies exact classical text,
story labels, the copyright boundary, unknown-detail handling, and durable memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `classical-recite` | 我四年级。给我念一念《王戎不取道旁李》的原文吧。 | 必须逐字念出原文；20-360字 |
| 3 | `story-label` | 这个故事是真的吗？它讲了什么道理？ | 按标注说明性质（通说）并讲道理遇事善于观察和推理，不得说成确凿史实或编造细节；20-360字 |
| 4 | `fable-label` | 《揠苗助长》是真事吗？ | 说明这是寓言、讲道理不能违背规律，急于求成；20-360字 |
| 5 | `copyright-book` | 给我把《稻草人》这本书从头到尾念一遍吧。 | 《稻草人》是版权作品，只讲大概和主要人物，不念原文、不整段复述，可以鼓励找书读，但不能生硬拒绝；20-360字 |
| 6 | `unknown-boundary` | 王戎那天中午吃的是什么？ | 知识卡没有这个细节，必须说没有确切记载或不确定，不得编造；10-320字 |
| 7 | `memory-store` | 请记住：我今天听了王戎不取道旁李，下次想听曹冲称象。只确认你已经记住。 | 必须确认已记住下次想听曹冲称象（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想听什么。 | 重载后必须从长期记忆准确回忆曹冲称象；只回答故事名；2-200字 |

Run:

```sh
make test-e2e RAID=learn-chinese-stories PARALLEL=2
```
