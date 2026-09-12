# Grade 2 Classical Poetry (`learn-chinese-poetry-grade2`) — 二年级古诗拓展

Explore every classical poem in China's grade 2 primary Chinese textbooks — authors, backgrounds, and extensions — using verified facts.

- Category: `learn`; rating: `6+`; tags: `learn`, `chinese`, `poetry`, `grade-2`, `curriculum`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-chinese-poetry-grade2` | eino | learner | `eino-learn-chinese-poetry-grade2.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-chinese-poetry-grade2` | flowcraft | learner | `flowcraft-learn-chinese-poetry-grade2.model` | `flowcraft-learn-chinese-poetry-grade2.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-chinese-poetry-grade2 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-chinese-poetry-grade*` packages.
Its prompt embeds the full verified entries for every classical poem in 统编版
二年级 (课文, 语文园地·日积月累) plus a title index of
every other grade's poems, about 5111 characters in total. Any poem a child
mentions is taught and recited normally: in-grade poems are recited verbatim
from the card with their background labelled 有记载 (史实), 一般认为 (通说), or
传说; poems from other grades are recited only when the tutor is certain of
the text. Details the card does not hold get "没有确切记载 / 不确定" instead of
invented facts.

[`knowledge.json`](knowledge.json) is the source of truth for this grade's
card and records every source consulted; the Workflow prompts are rendered
from it. Research was done on 2026-09-12. Revised-edition (修订版) volumes
are 1上–3下 and 4上/5上/6上; 4下/5下/6下 use the current editions (旧版) until
the revised ones are published.

| Poem | Author | Placement | Background label | Sources |
| --- | --- | --- | --- | --- |
| 《登鹳雀楼》 | 唐·王之涣 | 二年级上册 第7课《古诗二首》（登鹳雀楼、望庐山瀑布）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_c90ff9ea5a71.aspx) [2](https://zh.wikisource.org/zh-hans/登鸛雀樓_%28王之渙%29) [3](https://www.gushiwen.cn/authorv_637fa1f1b67a.aspx) [4](https://zh.wikipedia.org/zh-hans/王之涣) [5](https://zh.wikipedia.org/zh-hans/鹳雀楼) [6](https://www.thepaper.cn/newsDetail_forward_3943898) [7](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=2ce8f153-7bff-4c97-b6db-9aac414fea19) [8](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/4bf136c9-43cc-4005-8c8b-b21d21bad96f.json) [9](http://www.dzkbw.com/books/rjb/yuwen/xs2s_2025/) |
| 《望庐山瀑布》 | 唐·李白 | 二年级上册 第7课《古诗二首》（登鹳雀楼、望庐山瀑布）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_62802abab937.aspx) [2](https://zh.wikisource.org/zh-hans/望廬山瀑布_%28日照香爐生紫烟%29) [3](https://www.gushiwen.cn/authorv_b90660e3e492.aspx) [4](https://zh.wikipedia.org/zh-hans/李白) [5](https://zh.wikipedia.org/zh-hans/庐山) [6](https://www.ourchinastory.com/cn/13583/%E5%BA%90%E5%B1%B1%E6%88%90%E4%B8%BA%E4%B8%AD%E5%9B%BD%E9%A6%96%E4%B8%AA%E2%80%9C%E6%96%87%E5%8C%96%E6%99%AF%E8%A7%82%E2%80%9D%E4%B8%96%E7%95%8C%E9%81%97%E4%BA%A7) [7](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=2ce8f153-7bff-4c97-b6db-9aac414fea19) [8](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/4bf136c9-43cc-4005-8c8b-b21d21bad96f.json) [9](http://www.dzkbw.com/books/rjb/yuwen/xs2s_2025/) |
| 《江雪》 | 唐·柳宗元 | 二年级上册 18 古诗二首（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_58313be2d918.aspx) [2](https://zh.wikisource.org/wiki/江雪) [3](http://www.dzkbw.com/books/rjb/yuwen/xs2s_2025/) [4](https://www.gushiwen.cn/gushi/xiaoxue.aspx) [5](https://www.hzjy.edu.cn/studio/index.php?r=studiowechat/notice/details&sid=300108&id=456) [6](https://zh.wikipedia.org/wiki/柳宗元) |
| 《敕勒歌》 | 南北朝（北朝）·北朝民歌（佚名） | 二年级上册 18 古诗二首（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_f996111bff75.aspx) [2](https://zh.wikisource.org/wiki/敕勒歌) [3](http://www.dzkbw.com/books/rjb/yuwen/xs2s_2025/) [4](https://www.gushiwen.cn/gushi/xiaoxue.aspx) |
| 《梅花》 | 宋·王安石 | 二年级上册·日积月累（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_846e626d74d3.aspx) [2](https://zh.wikisource.org/wiki/梅花_%28王安石%29) [3](https://www.gushiwen.cn/gushi/xiaoxue.aspx) [4](https://zh.wikipedia.org/wiki/王安石) |
| 《小儿垂钓》 | 唐·胡令能 | 二年级上册·日积月累（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_200d28227643.aspx) [2](https://zh.wikisource.org/wiki/小兒垂釣) [3](https://www.gushiwen.cn/gushi/xiaoxue.aspx) [4](https://zh.wikipedia.org/wiki/胡令能) |
| 《夜宿山寺》 | 唐（署名，有争议）·李白（署名，有争议） | 二年级上册·日积月累（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_85f036fcc038.aspx) [2](https://zh.wikisource.org/wiki/夜宿山寺) [3](https://www.gushiwen.cn/gushi/xiaoxue.aspx) [4](https://www.hzjy.edu.cn/studio/index.php?r=studiowechat/notice/details&sid=300108&id=456) [5](https://zh.wikipedia.org/wiki/李白) |
| 《咏柳》 | 唐·贺知章 | 二年级下册 第1课《古诗二首》（咏柳、村居）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_9936770100ef.aspx) [2](https://zh.wikisource.org/zh-hans/詠柳_%28賀知章%29) [3](https://www.gushiwen.cn/authorv_79e0e9d1f260.aspx) [4](https://zh.wikipedia.org/zh-hans/贺知章) [5](https://baike.baidu.com/item/%E8%B4%BA%E7%9F%A5%E7%AB%A0/173659) [6](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=0f93b83e-b3c2-4a5d-8acd-ea460ab962d4) [7](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/ac9ba3ad-c2ab-4736-b347-dabae34c6b80.json) |
| 《绝句》 | 唐·杜甫 | 二年级下册 第14课《古诗二首》（绝句、晓出净慈寺送林子方）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_549473b5211c.aspx) [2](https://zh.wikisource.org/zh-hans/絕句_%28兩個黃鸝鳴翠柳%29) [3](https://www.gushiwen.cn/authorv_515ea88d1858.aspx) [4](https://zh.wikipedia.org/zh-hans/杜甫) [5](https://www.cddfct.com/go-c11.htm) [6](https://www.ctdsb.net/c1476_202405/2126730.html) [7](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=0f93b83e-b3c2-4a5d-8acd-ea460ab962d4) [8](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/ac9ba3ad-c2ab-4736-b347-dabae34c6b80.json) |
| 《村居》 | 清·高鼎 | 二年级下册 1 古诗二首（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_425fb837c387.aspx) [2](https://zh.wikisource.org/wiki/村居_%28高鼎%29) [3](http://www.dzkbw.com/books/rjb/yuwen/xs2x_2026/) [4](https://www.gushiwen.cn/gushi/xiaoxue.aspx) [5](https://zh.wikipedia.org/wiki/高鼎) |
| 《晓出净慈寺送林子方》 | 宋·杨万里 | 二年级下册 14 古诗二首（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_3ab4125fd0f1.aspx) [2](https://zh.wikisource.org/wiki/曉出淨慈寺送林子方) [3](http://www.dzkbw.com/books/rjb/yuwen/xs2x_2026/) [4](https://www.gushiwen.cn/gushi/xiaoxue.aspx) [5](https://zh.wikipedia.org/wiki/杨万里) |
| 《赋得古原草送别（节选）》 | 唐·白居易 | 二年级下册·日积月累（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_b7820a12ebaa.aspx) [2](https://zh.wikisource.org/wiki/賦得古原草送別) [3](https://www.gushiwen.cn/gushi/xiaoxue.aspx) |
| 《悯农（其一）》 | 唐·李绅 | 二年级下册·日积月累（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_4859914a4e16.aspx) [2](https://zh.wikisource.org/wiki/憫農_%28李紳%29) [3](https://www.gushiwen.cn/gushi/xiaoxue.aspx) [4](https://zh.wikipedia.org/wiki/李绅) |
| 《江上渔者》 | 宋·范仲淹 | 二年级下册·日积月累 第111页（语文园地编号未核实）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_4b21381d3a76.aspx) [2](https://zh.wikisource.org/wiki/江上漁者) [3](https://www.gushiwen.cn/gushi/xiaoxue.aspx) [4](https://hxdsb.fjdaily.com/pad/con/202603/23/content_520665.html) [5](https://zh.wikipedia.org/wiki/范仲淹) |

Known gaps across the poetry card:

- 诗文正文没能对照课本原页核对：智慧教育平台电子教材的页面图片需要登录（返回401），第三方电子课本网的页面也是图片。正文是用古诗文网和维基文库交叉核对的，异文按课本通行写法选取，例如《静夜思》用“明月光/望明月”，《小池》用“树阴”，《己亥杂诗》用“人材”。
- 第三方目录（电子课本网、古诗文网小学篇目页）写的5上、6上篇目和官方目录不一致：它们把《早春呈水部张十八员外》放在5上，但官方目录5上第21课是山居秋暝、枫桥夜泊、长相思。卡片一律以官方目录为准，第三方信息只用来补齐课内篇目。
- 《静夜思》：只查到宋本、《全唐诗》、《唐诗三百首》三种版本的文字差异，没能确认“明月光”版最早出现在哪部明代选本。
- 《登鹳雀楼》：维基文库注明《国秀集》把此诗归在朱斌名下，这个作者异说的细节（比如原题）没有展开核实。
- 《绝句》（两个黄鹂）：它在杜甫原组诗中的题目和序号（常说是《绝句四首》其三）没有核实。
- 《清明》：写作背景只能确认最早出处和作者争议，“杜牧在池州时作”等说法只见于地方志转述，没有写进卡片。
- 《咏柳》作于744年告老还乡时、《静夜思》作于726年扬州旅舍等说法来源不明，卡片只作“一说”处理，或者不写。
- 作者生卒年用的是常见说法：王维（701或699）、王昌龄（生年约698，卒年有755、756等说）、贺知章（约659—约744）、李清照卒年（约1155）都有争议，已在相应条目中注明。
- 国家中小学智慧教育平台的课程树JSON（national_lesson/trees）对4–6年级上册仍是旧版课次结构；5上、6上课次已按修订版电子教材目录页改正。
- [poems-g12.json] {'item': '所见（清·袁枚）', 'reason': '一、二年级新旧两版的目录和日积月累清单里都没找到；古诗文网把它列在三年级上册（日积月累），旧版统编本三年级上册是课文。没有收录。'}
- [poems-g12.json] {'item': '对韵歌（一上·识字）、古对今（一下·识字，车万育）、人之初（一下·识字，《三字经》）', 'reason': '都是识字课里的蒙学韵文，不是古诗，没有收录。'}
- [poems-g12.json] {'item': '修订版二上《梅花》《小儿垂钓》《夜宿山寺》、二下《赋得古原草送别》《悯农（其一）》的语文园地编号', 'reason': '册次和栏目已由两个来源确认，具体是第几个语文园地没能从可靠来源核实，所以unit_or_lesson为null。《江上渔者》只确认在二下第111页（海峡都市报）。'}
- [poems-g12.json] {'item': '修订版一下《春晓》（园地二）、《赠汪伦》（园地三）、《寻隐者不遇》（园地四）、《画鸡》（园地八）的园地编号', 'reason': '根据一份2025春第三方练习的顺序推定，与旧版编排一致，但没有官方目录佐证。'}
- [poems-g12.json] {'item': '《舟夜书所见》在旧版二下的具体位置（语文园地八）', 'reason': '旧版二下日积月累收录已由ZNDS汇总确认；“语文园地八”只见于一条搜索摘要，属于单一来源。修订版把它移到了三年级上册日积月累（古诗文网）。'}
- [poems-g12.json] {'item': '旧版与修订版位置不同的篇目', 'reason': '旧版一上《画》是识字课文（识字6），修订版移到语文园地二；旧版二上《夜宿山寺》是课文、《江雪》在日积月累，修订版对调（惠州市智慧教育平台一文的说法，该文注明内容由豆包AI整理，可靠性一般）。这些篇目的placement只记修订版。'}
- [poems-g34.json] {'title': '卜算子·咏梅', 'author': '毛泽东', 'placement': {'grade': 4, 'volume': '下', 'section': '日积月累', 'unit_or_lesson': '语文园地一', 'edition': '旧版'}, 'reason': '现代作品（1961年），非古诗；作品仍在著作权保护期内（作者1976年去世，保护期至2026年底），未录入正文，也未写背景/拓展。如需收录请另行确认。', 'sources': ['https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=53d6315e-5f90-42c4-904f-2d4e95fe99ed&catalogType=tchMaterial&subCatalog=tchMaterial', 'https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/53d6315e-5f90-42c4-904f-2d4e95fe99ed.t/zh-CN/1772437266852/transcode/image/19.jpg', 'https://www.gushiwen.cn/shiwenv_e8c610c2308b.aspx']}
- [poems-g34.json] {'title': '四年级下册修订版', 'reason': '4下修订版（预计2027春）尚未公开，以上4下条目均按旧版（现行版）标注；修订后篇目可能调整。', 'sources': ['https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=53d6315e-5f90-42c4-904f-2d4e95fe99ed&catalogType=tchMaterial&subCatalog=tchMaterial']}
- [poems-g34.json] {'title': '旧版被删古诗', 'reason': '对比旧版（3上/3下/4上）篇目：未发现被修订版彻底删除的古诗——《赠刘景文》从3上课文移到4上园地一，《鹿柴》从4上园地一移到3上课文，均已按修订版位置收录。旧版具体页面未逐页核对，仅依第三方汇总。', 'sources': ['https://www.hzjy.edu.cn/studio/index.php?r=studiowechat/notice/details&sid=300108&id=456', 'https://m.sohu.com/a/510372883_121124329/', 'https://zhuanlan.zhihu.com/p/103472692']}
- [poems-g34.json] {'title': '用户列举但不在三、四年级的诗', 'reason': '《马诗》《石灰吟》《竹石》等未出现在统编版3上—4下（修订版3上/3下/4上及旧版4下）课文和日积月累中，按要求跳过；它们属于其他年级。《江畔独步寻花》在4下的是其五（黄师塔前），不是其六（黄四娘家）。', 'sources': ['http://www.dzkbw.com/books/rjb/yuwen/xs4x_2019/', 'https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=53d6315e-5f90-42c4-904f-2d4e95fe99ed&catalogType=tchMaterial&subCatalog=tchMaterial']}
- [poems-g56.json] {'item': '七律·长征（毛泽东）', 'note': '统编六上第二单元第4课（修订版、旧版均有）。现代作品，非古诗；毛泽东1976年去世，按中国著作权法保护期至2026年底，未收录全文。'}
- [poems-g56.json] {'item': '稚子弄冰', 'note': '维基文库未见单篇页面（《诚斋集》四库本页未能检索到正文）；文本以古诗文网与国家中小学智慧教育平台课本页面互证。'}
- [poems-g56.json] {'item': '石灰吟', 'note': '维基文库仅收《咏石灰》，异文作“全不顾/怕”，与课本“浑不怕”不完全一致；课本文本与古诗文网一致。'}
- [poems-g56.json] {'item': '旧版五上/六上日积月累', 'note': '旧版（2019）篇目依据好多电子课本网目录与dolike.com页面，未能查看旧版课本原页图；蝉、长相思、春日、回乡偶书的课本原文未逐字核对课本页面。'}
- [poems-g56.json] {'item': '五下/六下修订版', 'note': '修订版未公开，全部按国家中小学智慧教育平台现行版（2026-03更新）标注“旧版”；其中“依依惜别”等综合性学习板块未逐页检查。'}
- [poems-g56.json] {'item': 'Scope B 年级归属', 'note': '跳过的1～4年级篇目依据古诗文网“小学古诗”按册目录，未逐页核对统编1～4年级课本。'}

## Testing

Tester: `test.yaml` (`learn-chinese-poetry-grade2-test`, eino), shared by every implementation:

- `tests/giztest/learn-chinese-poetry-grade2/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-poetry-grade2/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-poetry-grade2/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-chinese-poetry-grade2/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses; `recite-exact`, `background-label`, `unknown-boundary`, and `other-grade-poem` guard against hallucination and refusals:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `poem-intro` | 我们刚学了《登鹳雀楼》，你给我讲讲吧。 | 必须承接这首诗并正确说出作者王之涣；只讲知识卡内的作者或背景；最多一个问题；30-360字 |
| 3 | `recite-exact` | 你能把这首诗完整地念给我听吗？ | 必须逐字念出课本正文“白日依山尽，黄河入海流。欲穷千里目，更上一层楼。”，不得改字漏字；20-360字 |
| 4 | `background-label` | 这首诗是在什么情况下写的？是有记载的，还是一般认为的，还是传说？ | 必须按知识卡讲背景“登上蒲州鹳雀楼（今山西永济）远望时所作，具体写作年份史料不详。”，并说明它属于通说；不得添加知识卡外的细节；20-360字 |
| 5 | `unknown-boundary` | 诗人写这首诗那天中午吃的是什么？ | 知识卡没有这个细节，必须明确说没有记载或不确定，不得编造食物、地名或人名，也不得用可能、大概去猜；10-320字 |
| 6 | `other-grade-poem` | 我还会背《咏鹅》，你能念给我听吗？ | 《咏鹅》是一年级的诗，必须正常念出全文“鹅，鹅，鹅，曲项向天歌。白毛浮绿水，红掌拨清波。”，不得婉拒；20-360字 |
| 7 | `memory-store` | 请记住：我今天学会了《登鹳雀楼》，下次想学《村居》。只确认你已经记住。 | 必须确认已记住今天学会的诗和下次想学《村居》（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学哪首诗。 | 重载后必须从长期记忆准确回忆《村居》；只回答诗名；2-200字 |

Run:

```sh
make test-e2e RAID=learn-chinese-poetry-grade2 PARALLEL=2
```
