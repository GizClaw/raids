# Grade 5 Classical Poetry (`learn-chinese-poetry-grade5`) — 五年级古诗拓展

Explore every classical poem in China's grade 5 primary Chinese textbooks — authors, backgrounds, and extensions — using verified facts.

- Category: `learn`; rating: `6+`; tags: `learn`, `chinese`, `poetry`, `grade-5`, `curriculum`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-chinese-poetry-grade5` | eino | learner | `eino-learn-chinese-poetry-grade5.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-chinese-poetry-grade5` | flowcraft | learner | `flowcraft-learn-chinese-poetry-grade5.model` | `flowcraft-learn-chinese-poetry-grade5.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-chinese-poetry-grade5 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-chinese-poetry-grade*` packages.
Its prompt embeds the full verified entries for every classical poem in 统编版
五年级 (课文, 语文园地·日积月累) plus a title index of
every other grade's poems, about 5574 characters in total. Any poem a child
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
| 《示儿》 | 宋·陆游 | 五年级上册 第11课《古诗三首》（示儿、题临安邸、己亥杂诗）（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_966c8a76211f.aspx) [2](https://zh.wikisource.org/zh-hans/示兒_%28陸游%29) [3](https://www.gushiwen.cn/authorv_efd5da0ed1a1.aspx) [4](https://zh.wikipedia.org/zh-hans/陆游) [5](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=aabf2e4a-3ceb-4e86-8804-22c10223cc57) [6](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/edbd7846-7206-42ec-8be5-f690e9d873aa.json) |
| 《己亥杂诗》 | 清·龚自珍 | 五年级上册 第11课《古诗三首》（示儿、题临安邸、己亥杂诗）（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_838d9b401572.aspx) [2](https://zh.wikisource.org/zh-hans/己亥雜詩) [3](https://zhuanlan.zhihu.com/p/572537225) [4](https://www.gushiwen.cn/authorv_e0c140ccdde2.aspx) [5](https://zh.wikipedia.org/zh-hans/龚自珍) [6](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=aabf2e4a-3ceb-4e86-8804-22c10223cc57) [7](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/edbd7846-7206-42ec-8be5-f690e9d873aa.json) |
| 《山居秋暝》 | 唐·王维 | 五年级上册 第20课《古诗三首》（山居秋暝、枫桥夜泊、早春呈水部张十八员外）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_44ba4afb80db.aspx) [2](https://zh.wikisource.org/zh-hans/山居秋暝) [3](https://www.gushiwen.cn/authorv_52fceee85532.aspx) [4](https://zh.wikipedia.org/zh-hans/王维) [5](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=aabf2e4a-3ceb-4e86-8804-22c10223cc57) [6](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/edbd7846-7206-42ec-8be5-f690e9d873aa.json) |
| 《枫桥夜泊》 | 唐·张继 | 五年级上册 第20课《古诗三首》（山居秋暝、枫桥夜泊、早春呈水部张十八员外）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_6fb73f607ad3.aspx) [2](https://zh.wikisource.org/zh-hans/楓橋夜泊) [3](https://zh.wikipedia.org/zh-hans/张继) [4](https://zh.wikipedia.org/zh-hans/寒山寺) [5](https://www.fjdh.cn/Item/91636.aspx) [6](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=aabf2e4a-3ceb-4e86-8804-22c10223cc57) [7](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/edbd7846-7206-42ec-8be5-f690e9d873aa.json) |
| 《题临安邸》 | 宋·林升 | 五年级上册 第四单元 11 古诗三首（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_63f2cb1073ff.aspx) [2](https://zh.wikisource.org/wiki/%E9%A1%8C%E8%87%A8%E5%AE%89%E9%82%B8) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/57.jpg) [4](https://www.haoduoyun.cc/book/rjb/yuwen/5s.shtml) |
| 《早春呈水部张十八员外》 | 唐·韩愈 | 五年级上册 第七单元 20 古诗三首（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_7e09f12b287c.aspx) [2](https://zh.wikisource.org/wiki/%E5%88%9D%E6%98%A5%E5%B0%8F%E9%9B%A8) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/98.jpg) [4](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/119.jpg) |
| 《乞巧》 | 唐·林杰 | 五年级上册·日积月累 语文园地三（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_e152d043be94.aspx) [2](https://zh.wikisource.org/wiki/%E4%B9%9E%E5%B7%A7) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/53.jpg) [4](https://www.haoduoyun.cc/book/rjb/yuwen/5s.shtml) |
| 《游子吟》 | 唐·孟郊 | 五年级上册·日积月累 语文园地六（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_161d06b0b556.aspx) [2](https://zh.wikisource.org/wiki/%E9%81%8A%E5%AD%90%E5%90%9F%20%28%E5%AD%9F%E9%83%8A%29) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/95.jpg) [4](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/21.jpg) |
| 《渔歌子》 | 唐·张志和 | 五年级上册·日积月累 语文园地七（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_ee72baa043c8.aspx) [2](https://zh.wikisource.org/wiki/%E6%BC%81%E6%AD%8C%E5%AD%90%20%28%E5%BC%B5%E5%BF%97%E5%92%8C%29) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/105.jpg) [4](https://www.haoduoyun.cc/book/rjb/yuwen/5s.shtml) |
| 《观书有感（其一）》 | 宋·朱熹 | 五年级上册·日积月累 语文园地八（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_4c1364cb1da5.aspx) [2](https://zh.wikisource.org/wiki/%E8%A7%80%E6%9B%B8%E6%9C%89%E6%84%9F) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/aabf2e4a-3ceb-4e86-8804-22c10223cc57.t/zh-CN/1787022984543/transcode/image/119.jpg) [4](https://www.dolike.com/3891.html) |
| 《蝉》 | 唐·虞世南 | 五年级上册·日积月累 语文园地一（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_c8414cce04e1.aspx) [2](https://zh.wikisource.org/wiki/%E8%9F%AC%20%28%E8%99%9E%E4%B8%96%E5%8D%97%29) [3](https://www.haoduoyun.cc/book/rjb/yuwen/5s.shtml) [4](http://www.haoduoyun.cc/book/rjb/yuwen/5s/17.shtml) |
| 《长相思》 | 清·纳兰性德 | 五年级上册 第七单元 21 古诗词三首（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_0a4d69889c65.aspx) [2](https://zh.wikisource.org/wiki/%E9%95%B7%E7%9B%B8%E6%80%9D%20%28%E7%B4%8D%E8%98%AD%E6%80%A7%E5%BE%B7%29) [3](https://www.haoduoyun.cc/book/rjb/yuwen/5s.shtml) |
| 《四时田园杂兴（其三十一）》 | 宋·范成大 | 五年级下册 第一单元 1 古诗三首（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_9d5e3f5ee21f.aspx) [2](https://zh.wikisource.org/wiki/%E7%94%B0%E5%AE%B6%20%28%E8%8C%83%E6%88%90%E5%A4%A7%29) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/7.jpg) |
| 《稚子弄冰》 | 宋·杨万里 | 五年级下册 第一单元 1 古诗三首（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_4bb194abd528.aspx) [2](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/7.jpg) |
| 《村晚》 | 宋·雷震 | 五年级下册 第一单元 1 古诗三首（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_be04bba6288c.aspx) [2](https://zh.wikisource.org/wiki/%E6%9D%91%E6%99%9A) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/8.jpg) |
| 《从军行（其四）》 | 唐·王昌龄 | 五年级下册 第四单元 9 古诗三首（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_d1129db241ec.aspx) [2](https://zh.wikisource.org/wiki/%E5%BE%9E%E8%BB%8D%E8%A1%8C%20%28%E9%9D%92%E6%B5%B7%E9%95%B7%E9%9B%B2%E6%9A%97%E9%9B%AA%E5%B1%B1%29) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/59.jpg) |
| 《秋夜将晓出篱门迎凉有感》 | 宋·陆游 | 五年级下册 第四单元 9 古诗三首（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_dbabcfab1a1b.aspx) [2](https://zh.wikisource.org/wiki/%E7%A7%8B%E5%A4%9C%E5%B0%87%E6%9B%89%E5%87%BA%E7%B1%AC%E9%96%80%E8%BF%8E%E6%B6%BC%E6%9C%89%E6%84%9F) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/59.jpg) |
| 《闻官军收河南河北》 | 唐·杜甫 | 五年级下册 第四单元 9 古诗三首（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_519029b7355c.aspx) [2](https://zh.wikisource.org/wiki/%E8%81%9E%E5%AE%98%E8%BB%8D%E6%94%B6%E6%B2%B3%E5%8D%97%E6%B2%B3%E5%8C%97) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/60.jpg) |
| 《鸟鸣涧》 | 唐·王维 | 五年级下册·日积月累 语文园地二（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_8ec950bd1395.aspx) [2](https://zh.wikisource.org/wiki/%E7%8E%8B%E5%8F%B3%E4%B8%9E%E9%9B%86%E7%AE%8B%E8%A8%BB/%E5%8D%B7%E4%B9%8B%E5%8D%81%E4%B8%89) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/43.jpg) [4](https://zh.wikisource.org/wiki/%E7%9A%87%E7%94%AB%E5%B2%B3%E4%BA%91%E6%BA%AA%E6%9D%82%E9%A2%98%E4%BA%94%E9%A6%96/%E9%B8%9F%E9%B8%A3%E6%B6%A7) |
| 《凉州词》 | 唐·王之涣 | 五年级下册·日积月累 语文园地四（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_3963afd966bc.aspx) [2](https://zh.wikisource.org/wiki/%E5%87%BA%E5%A1%9E%20%28%E7%8E%8B%E4%B9%8B%E6%B8%99%29) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/73.jpg) [4](https://zh.wikisource.org/wiki/%E5%87%89%E5%B7%9E%E8%AF%8D%20%28%E7%8E%8B%E4%B9%8B%E6%B6%A3%29) |
| 《乡村四月》 | 宋·翁卷 | 五年级下册·日积月累 语文园地七（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_07f5e3403665.aspx) [2](https://zh.wikisource.org/wiki/%E9%84%89%E6%9D%91%E5%9B%9B%E6%9C%88) [3](https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets/98172dc9-8fba-4da6-9fae-6a3d1166f038.t/zh-CN/1772437267582/transcode/image/111.jpg) |

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

Tester: `test.yaml` (`learn-chinese-poetry-grade5-test`, eino), shared by every implementation:

- `tests/giztest/learn-chinese-poetry-grade5/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-poetry-grade5/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-poetry-grade5/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-chinese-poetry-grade5/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses; `recite-exact`, `background-label`, `unknown-boundary`, and `other-grade-poem` guard against hallucination and refusals:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `poem-intro` | 我们刚学了《示儿》，你给我讲讲吧。 | 必须承接这首诗并正确说出作者陆游；只讲知识卡内的作者或背景；最多一个问题；30-360字 |
| 3 | `recite-exact` | 你能把这首诗完整地念给我听吗？ | 必须逐字念出课本正文“死去元知万事空，但悲不见九州同。王师北定中原日，家祭无忘告乃翁。”，不得改字漏字；20-360字 |
| 4 | `background-label` | 这首诗是在什么情况下写的？是有记载的，还是一般认为的，还是传说？ | 必须按知识卡讲背景“陆游临终前写给儿子们的绝笔诗，作于他去世前不久（1210年初）。”，并说明它属于史实；不得添加知识卡外的细节；20-360字 |
| 5 | `unknown-boundary` | 诗人写这首诗那天中午吃的是什么？ | 知识卡没有这个细节，必须明确说没有记载或不确定，不得编造食物、地名或人名，也不得用可能、大概去猜；10-320字 |
| 6 | `other-grade-poem` | 我还会背《咏鹅》，你能念给我听吗？ | 《咏鹅》是一年级的诗，必须正常念出全文“鹅，鹅，鹅，曲项向天歌。白毛浮绿水，红掌拨清波。”，不得婉拒；20-360字 |
| 7 | `memory-store` | 请记住：我今天学会了《示儿》，下次想学《山居秋暝》。只确认你已经记住。 | 必须确认已记住今天学会的诗和下次想学《山居秋暝》；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学哪首诗。 | 重载后必须从长期记忆准确回忆《山居秋暝》；只回答诗名；2-200字 |

Run:

```sh
make test-e2e RAID=learn-chinese-poetry-grade5 PARALLEL=2
```
