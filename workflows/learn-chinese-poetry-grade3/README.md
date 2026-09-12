# Grade 3 Classical Poetry (`learn-chinese-poetry-grade3`) — 三年级古诗拓展

Explore every classical poem in China's grade 3 primary Chinese textbooks — authors, backgrounds, and extensions — using verified facts.

- Category: `learn`; rating: `6+`; tags: `learn`, `chinese`, `poetry`, `grade-3`, `curriculum`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-chinese-poetry-grade3` | eino | learner | `eino-learn-chinese-poetry-grade3.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-chinese-poetry-grade3` | flowcraft | learner | `flowcraft-learn-chinese-poetry-grade3.model` | `flowcraft-learn-chinese-poetry-grade3.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-chinese-poetry-grade3 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-chinese-poetry-grade*` packages.
Its prompt embeds the full verified entries for every classical poem in 统编版
三年级 (课文, 语文园地·日积月累) plus a title index of
every other grade's poems, about 5618 characters in total. Any poem a child
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
| 《舟夜书所见》 | 清·查慎行 | 三年级上册·日积月累 语文园地二（修订版） | 史实 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/31.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_d88e3533fc4a.aspx) |
| 《望洞庭》 | 唐·刘禹锡 | 三年级上册 第二单元 第4课 古诗三首（修订版） | 通说 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/19.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_880912218fc8.aspx) |
| 《山行》 | 唐·杜牧 | 三年级上册 第二单元 第4课 古诗三首（修订版） | 史实 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/19.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_3c36881bd247.aspx) |
| 《夜书所见》 | 宋·叶绍翁 | 三年级上册 第二单元 第4课 古诗三首（修订版） | 史实 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/20.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_7ccd1778ba07.aspx) |
| 《鹿柴》 | 唐·王维 | 三年级上册 第七单元 第20课 古诗三首（修订版） | 史实 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/89.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_e9b1a8b4def0.aspx) |
| 《望天门山》 | 唐·李白 | 三年级上册 第七单元 第20课 古诗三首（修订版） | 通说 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/89.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_97e6296bfb8d.aspx) |
| 《饮湖上初晴后雨》 | 宋·苏轼 | 三年级上册 第七单元 第20课 古诗三首（修订版） | 通说 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/90.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_8949464433f0.aspx) |
| 《所见》 | 清·袁枚 | 三年级上册·日积月累 语文园地一（修订版） | 史实 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/17.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_58699ebb5e93.aspx) |
| 《早发白帝城》 | 唐·李白 | 三年级上册·日积月累 语文园地六（修订版） | 通说 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/87.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_0f81015a040c.aspx) |
| 《采莲曲》 | 唐·王昌龄 | 三年级上册·日积月累 语文园地七（修订版） | 史实 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=837f368e-fd4e-404a-ae3f-342d75bc0227&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/837f368e-fd4e-404a-ae3f-342d75bc0227.t/zh-CN/1787022983413/transcode/image/99.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3s_2025/) [4](https://www.gushiwen.cn/shiwenv_c953220f9f52.aspx) |
| 《惠崇春江晚景》 | 宋·苏轼 | 三年级下册 第1课《古诗三首》（绝句、惠崇春江晚景、三衢道中）（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_cd140bf494da.aspx) [2](https://zh.wikisource.org/zh-hans/惠崇春江晚景) [3](https://www.gushiwen.cn/authorv_3b99a16ff2dd.aspx) [4](https://zh.wikipedia.org/zh-hans/苏轼) [5](https://baike.baidu.com/item/%E6%83%A0%E5%B4%87/1241098) [6](https://news.qq.com/rain/a/20200703A0DYXK00) [7](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b) [8](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/6042ef62-a820-41aa-858d-1d6f1d6e3aa7.json) |
| 《元日》 | 宋·王安石 | 三年级下册 第12课《古诗三首》（元日、清明、九月九日忆山东兄弟）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_a167901c9c90.aspx) [2](https://zh.wikisource.org/zh-hans/元日_%28王安石%29) [3](https://www.gushiwen.cn/authorv_6485481407d1.aspx) [4](https://zh.wikipedia.org/zh-hans/王安石) [5](https://zh.wikipedia.org/zh-hans/桃符) [6](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b) [7](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/6042ef62-a820-41aa-858d-1d6f1d6e3aa7.json) |
| 《清明》 | 唐·杜牧 | 三年级下册 第12课《古诗三首》（元日、清明、九月九日忆山东兄弟）（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_d3e3283daac5.aspx) [2](https://zh.wikisource.org/zh-hans/清明_%28杜牧%29) [3](https://www.chinawriter.com.cn/n1/2025/0403/c442005-40452906.html) [4](http://jres2023.xhby.net/index/202303/t20230330_7885321.shtml) [5](https://www.gushiwen.cn/authorv_727e9dff8850.aspx) [6](https://zh.wikipedia.org/zh-hans/杜牧) [7](https://www.cma.gov.cn/ztbd/2024zt/24jq/qm/index.html) [8](https://www.ihchina.cn/project_details/14907/) [9](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b) [10](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/6042ef62-a820-41aa-858d-1d6f1d6e3aa7.json) |
| 《九月九日忆山东兄弟》 | 唐·王维 | 三年级下册 第12课《古诗三首》（元日、清明、九月九日忆山东兄弟）（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_d75a706935de.aspx) [2](https://zh.wikisource.org/zh-hans/九月九日憶山東兄弟) [3](https://www.gushiwen.cn/authorv_52fceee85532.aspx) [4](https://zh.wikipedia.org/zh-hans/王维) [5](https://zh.wikipedia.org/zh-hans/重阳节) [6](https://zh.wikipedia.org/zh-hans/茱萸) [7](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b) [8](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/6042ef62-a820-41aa-858d-1d6f1d6e3aa7.json) |
| 《绝句》 | 唐·杜甫 | 三年级下册 第一单元 第1课 古诗三首（修订版） | 通说 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/7.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3x_2026/) [4](https://www.gushiwen.cn/shiwenv_e5e7911da1d2.aspx) |
| 《三衢道中》 | 宋·曾几 | 三年级下册 第一单元 第1课 古诗三首（修订版） | 史实 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/8.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3x_2026/) [4](https://www.gushiwen.cn/shiwenv_fbbd80710c5e.aspx) |
| 《忆江南》 | 唐·白居易 | 三年级下册·日积月累 语文园地一（修订版） | 通说 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/19.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3x_2026/) [4](https://www.gushiwen.cn/shiwenv_6ad0636b01a9.aspx) |
| 《滁州西涧》 | 唐·韦应物 | 三年级下册·日积月累 语文园地三（修订版） | 通说 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/47.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3x_2026/) [4](https://www.gushiwen.cn/shiwenv_f6bd6356c843.aspx) |
| 《大林寺桃花》 | 唐·白居易 | 三年级下册·日积月累 语文园地七（修订版） | 史实 | [1](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=8e107655-5128-451f-84e5-d158725c537b&catalogType=tchMaterial&subCatalog=tchMaterial) [2](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/8e107655-5128-451f-84e5-d158725c537b.t/zh-CN/1772437266029/transcode/image/99.jpg) [3](http://www.dzkbw.com/books/rjb/yuwen/xs3x_2026/) [4](https://www.gushiwen.cn/shiwenv_5e26797704a7.aspx) |

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

Tester: `test.yaml` (`learn-chinese-poetry-grade3-test`, eino), shared by every implementation:

- `tests/giztest/learn-chinese-poetry-grade3/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-poetry-grade3/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-poetry-grade3/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-chinese-poetry-grade3/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses; `recite-exact`, `background-label`, `unknown-boundary`, and `other-grade-poem` guard against hallucination and refusals:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `poem-intro` | 我们刚学了《九月九日忆山东兄弟》，你给我讲讲吧。 | 必须承接这首诗并正确说出作者王维；只讲知识卡内的作者或背景；最多一个问题；30-360字 |
| 3 | `recite-exact` | 你能把这首诗完整地念给我听吗？ | 必须逐字念出课本正文“独在异乡为异客，每逢佳节倍思亲。遥知兄弟登高处，遍插茱萸少一人。”，不得改字漏字；20-360字 |
| 4 | `background-label` | 这首诗是在什么情况下写的？是有记载的，还是一般认为的，还是传说？ | 必须按知识卡讲背景“《全唐诗》题下原注“时年十七”：王维十七岁客居他乡，重阳节思念家乡兄弟而作。”，并说明它属于史实；不得添加知识卡外的细节；20-360字 |
| 5 | `unknown-boundary` | 诗人写这首诗那天中午吃的是什么？ | 知识卡没有这个细节，必须明确说没有记载或不确定，不得编造食物、地名或人名，也不得用可能、大概去猜；10-320字 |
| 6 | `other-grade-poem` | 我还会背《咏鹅》，你能念给我听吗？ | 《咏鹅》是一年级的诗，必须正常念出全文“鹅，鹅，鹅，曲项向天歌。白毛浮绿水，红掌拨清波。”，不得婉拒；20-360字 |
| 7 | `memory-store` | 请记住：我今天学会了《九月九日忆山东兄弟》，下次想学《望天门山》。只确认你已经记住。 | 必须确认已记住今天学会的诗和下次想学《望天门山》（复述措辞可以不同，下一轮重连后再严格核对）；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学哪首诗。 | 重载后必须从长期记忆准确回忆《望天门山》；只回答诗名；2-200字 |

Run:

```sh
make test-e2e RAID=learn-chinese-poetry-grade3 PARALLEL=2
```
