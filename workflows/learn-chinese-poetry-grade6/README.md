# Grade 6 Classical Poetry (`learn-chinese-poetry-grade6`) — 六年级古诗拓展

Explore every classical poem in China's grade 6 primary Chinese textbooks — authors, backgrounds, and extensions — using verified facts.

- Category: `learn`; rating: `6+`; tags: `learn`, `chinese`, `poetry`, `grade-6`, `curriculum`, `facts`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-learn-chinese-poetry-grade6` | eino | learner | `eino-learn-chinese-poetry-grade6.model` | - |
| `flowcraft.yaml` | `flowcraft-learn-chinese-poetry-grade6` | flowcraft | learner | `flowcraft-learn-chinese-poetry-grade6.model` | `flowcraft-learn-chinese-poetry-grade6.tutor` |

Install an implementation into a RuntimeProfile with `raids install learn-chinese-poetry-grade6 --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-chinese-poetry-grade*` packages.
Its prompt embeds the full verified entries for every classical poem in 统编版
六年级 (课文, 语文园地·日积月累, 古诗词诵读) plus a title index of
every other grade's poems, about 6561 characters in total. Any poem a child
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
| 《宿建德江》 | 唐·孟浩然 | 六年级上册 第3课《古诗词三首》（宿建德江、六月二十七日望湖楼醉书、西江月·夜行黄沙道中）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_63d3ff8f6b61.aspx) [2](https://zh.wikisource.org/zh-hans/宿建德江) [3](https://www.gushiwen.cn/authorv_3811e4e1f460.aspx) [4](https://zh.wikipedia.org/zh-hans/孟浩然) [5](https://so.gushiwen.cn/fanyi_694.aspx) [6](https://zh.wikipedia.org/zh-hans/新安江) [7](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=2e3dc199-9c42-486b-bbee-7731bd0ee227) [8](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/4d2e2415-46d3-47f4-8393-30707820123c.json) |
| 《六月二十七日望湖楼醉书》 | 宋·苏轼 | 六年级上册 第3课《古诗词三首》（宿建德江、六月二十七日望湖楼醉书、西江月·夜行黄沙道中）（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_0eda7b78250a.aspx) [2](https://zh.wikisource.org/zh-hans/六月二十七日望湖樓醉書五絶) [3](https://www.gushiwen.cn/authorv_3b99a16ff2dd.aspx) [4](https://zh.wikipedia.org/zh-hans/苏轼) [5](https://baike.baidu.com/item/%E6%9C%9B%E6%B9%96%E6%A5%BC/22182) [6](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=2e3dc199-9c42-486b-bbee-7731bd0ee227) [7](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/4d2e2415-46d3-47f4-8393-30707820123c.json) |
| 《浪淘沙（其一）》 | 唐·刘禹锡 | 六年级上册 第19课《古诗三首》（浪淘沙（其一）、江南春、书湖阴先生壁）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_857567307e6a.aspx) [2](https://zh.wikisource.org/zh-hans/浪淘沙九首) [3](https://www.gushiwen.cn/authorv_e3c4e8cf2646.aspx) [4](https://zh.wikipedia.org/zh-hans/刘禹锡) [5](https://zh.wikipedia.org/zh-hans/黄河) [6](https://www.neac.gov.cn/seac/c103391/202210/1158972.shtml) [7](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=2e3dc199-9c42-486b-bbee-7731bd0ee227) [8](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/4d2e2415-46d3-47f4-8393-30707820123c.json) |
| 《江南春》 | 唐·杜牧 | 六年级上册 第19课《古诗三首》（浪淘沙（其一）、江南春、书湖阴先生壁）（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_33cbdb2cf9b3.aspx) [2](https://zh.wikisource.org/zh-hans/%E4%B8%89%E9%AB%94%E5%94%90%E8%A9%A9_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B71) [3](https://www.gushiwen.cn/authorv_727e9dff8850.aspx) [4](https://zh.wikipedia.org/zh-hans/杜牧) [5](https://zh.wikipedia.org/zh-hans/南京市) [6](https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=2e3dc199-9c42-486b-bbee-7731bd0ee227) [7](https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/4d2e2415-46d3-47f4-8393-30707820123c.json) |
| 《江畔独步寻花（其五）》 | 唐·杜甫 | 六年级上册·日积月累 语文园地一（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_85e46c4b3dbc.aspx) [2](https://zh.wikisource.org/wiki/%E6%B1%9F%E7%95%94%E7%8D%A8%E6%AD%A5%E5%B0%8B%E8%8A%B1%E4%B8%83%E7%B5%B6%E5%8F%A5) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/17.jpg) |
| 《西江月·夜行黄沙道中》 | 宋·辛弃疾 | 六年级上册 第一单元 3 古诗词三首（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_f090d65212f4.aspx) [2](https://zh.wikisource.org/wiki/%E8%A5%BF%E6%B1%9F%E6%9C%88%20%28%E8%BE%9B%E6%A3%84%E7%96%BE%29) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/14.jpg) [4](https://www.haoduoyun.cc/book/rjb/yuwen/6s.shtml) |
| 《书湖阴先生壁》 | 宋·王安石 | 六年级上册 第六单元 19 古诗三首（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_3d787de04152.aspx) [2](https://zh.wikisource.org/wiki/%E6%9B%B8%E6%B9%96%E9%99%B0%E5%85%88%E7%94%9F%E5%A3%81) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/97.jpg) [4](https://www.haoduoyun.cc/book/rjb/yuwen/6s.shtml) |
| 《观书有感（其二）》 | 宋·朱熹 | 六年级上册·日积月累 语文园地三（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_dd1c97accf6e.aspx) [2](https://zh.wikisource.org/wiki/%E8%A7%80%E6%9B%B8%E6%9C%89%E6%84%9F) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/53.jpg) [4](https://www.dolike.com/3891.html) |
| 《送元二使安西》 | 唐·王维 | 六年级上册·日积月累 语文园地四（修订版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_12a2295aa76b.aspx) [2](https://zh.wikisource.org/wiki/%E9%80%81%E5%85%83%E4%BA%8C%E4%BD%BF%E5%AE%89%E8%A5%BF) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/71.jpg) [4](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/117.jpg) |
| 《过故人庄》 | 唐·孟浩然 | 六年级上册·日积月累 语文园地六（修订版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_4a0d548bebb3.aspx) [2](https://zh.wikisource.org/wiki/%E9%81%8E%E6%95%85%E4%BA%BA%E8%8E%8A) [3](https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/2e3dc199-9c42-486b-bbee-7731bd0ee227.t/zh-CN/1787022985331/transcode/image/101.jpg) [4](https://www.haoduoyun.cc/book/rjb/yuwen/6s.shtml) |
| 《春日》 | 宋·朱熹 | 六年级上册·日积月累 语文园地三（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_ba4626c44270.aspx) [2](https://zh.wikisource.org/wiki/%E6%98%A5%E6%97%A5%20%28%E6%9C%B1%E7%86%B9%29) [3](https://www.haoduoyun.cc/book/rjb/yuwen/6s.shtml) [4](https://www.haoduoyun.cc/book/rjb/yuwen/6s/52.shtml) |
| 《回乡偶书》 | 唐·贺知章 | 六年级上册·日积月累 语文园地四（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_f459f8ed8d23.aspx) [2](https://zh.wikisource.org/wiki/%E5%9B%9E%E4%B9%A1%E5%81%B6%E4%B9%A6%20%28%E5%B0%91%E5%B0%8F%E7%A6%BB%E5%AE%B6%E8%80%81%E5%A4%A7%E5%9B%9E%29) [3](https://www.haoduoyun.cc/book/rjb/yuwen/6s.shtml) [4](https://www.haoduoyun.cc/book/rjb/yuwen/6s/66.shtml) |
| 《寒食》 | 唐·韩翃 | 六年级下册 第一单元 3 古诗三首（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_f26e62f4bfc8.aspx) [2](https://zh.wikisource.org/wiki/%E5%AF%92%E9%A3%9F%20%28%E9%9F%93%E7%BF%83%29) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/16.jpg) |
| 《迢迢牵牛星》 | 汉·佚名（《古诗十九首》） | 六年级下册 第一单元 3 古诗三首（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_7f09a756c9c0.aspx) [2](https://zh.wikisource.org/wiki/%E8%BF%A2%E8%BF%A2%E7%89%BD%E7%89%9B%E6%98%9F) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/16.jpg) |
| 《十五夜望月》 | 唐·王建 | 六年级下册 第一单元 3 古诗三首（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_2367f5ae6dee.aspx) [2](https://zh.wikisource.org/wiki/%E5%8D%81%E4%BA%94%E5%A4%9C%E6%9C%9B%E6%9C%88%E5%AF%84%E6%9D%9C%E9%83%8E%E4%B8%AD) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/17.jpg) |
| 《马诗》 | 唐·李贺 | 六年级下册 第四单元 10 古诗三首（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_55174e6ebe20.aspx) [2](https://zh.wikisource.org/wiki/%E9%A6%AC%E8%A9%A9) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/63.jpg) |
| 《石灰吟》 | 明·于谦 | 六年级下册 第四单元 10 古诗三首（旧版） | 传说 | [1](https://www.gushiwen.cn/shiwenv_c6c93895df0a.aspx) [2](https://zh.wikisource.org/wiki/%E8%A9%A0%E7%9F%B3%E7%81%B0) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/63.jpg) |
| 《竹石》 | 清·郑燮 | 六年级下册 第四单元 10 古诗三首（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_e5c9337524b7.aspx) [2](https://zh.wikisource.org/wiki/%E7%AB%B9%E7%9F%B3) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/64.jpg) |
| 《长歌行》 | 汉·汉乐府 | 六年级下册·日积月累 语文园地一（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_183d69f50755.aspx) [2](https://zh.wikisource.org/wiki/%E9%95%B7%E6%AD%8C%E8%A1%8C%20%28%E6%BC%A2%E6%A8%82%E5%BA%9C%29) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/23.jpg) |
| 《采薇（节选）》 | 先秦·《诗经·小雅》 | 六年级下册·古诗词诵读 1 采薇（节选）（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_fa087546c81b.aspx) [2](https://zh.wikisource.org/wiki/%E8%A9%A9%E7%B6%93/%E9%87%87%E8%96%87) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/116.jpg) |
| 《春夜喜雨》 | 唐·杜甫 | 六年级下册·古诗词诵读 3 春夜喜雨（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_d48451f00541.aspx) [2](https://zh.wikisource.org/wiki/%E6%98%A5%E5%A4%9C%E5%96%9C%E9%9B%A8) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/118.jpg) |
| 《泊船瓜洲》 | 宋·王安石 | 六年级下册·古诗词诵读 6 泊船瓜洲（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_df14e6fd217b.aspx) [2](https://zh.wikisource.org/wiki/%E6%B3%8A%E8%88%B9%E7%93%9C%E6%B4%B2) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/121.jpg) |
| 《游园不值》 | 宋·叶绍翁 | 六年级下册·古诗词诵读 7 游园不值（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_a31b957aba53.aspx) [2](https://zh.wikisource.org/wiki/%E9%81%8A%E5%9C%92%E4%B8%8D%E5%80%BC) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/122.jpg) |
| 《卜算子·送鲍浩然之浙东》 | 宋·王观 | 六年级下册·古诗词诵读 8 卜算子·送鲍浩然之浙东（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_ee1bd6238d4a.aspx) [2](https://zh.wikisource.org/wiki/%E5%8D%9C%E7%AE%97%E5%AD%90%20%28%E7%8E%8B%E8%A7%80%29) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/123.jpg) |
| 《浣溪沙》 | 宋·苏轼 | 六年级下册·古诗词诵读 9 浣溪沙（旧版） | 史实 | [1](https://www.gushiwen.cn/shiwenv_a9a16104dd1b.aspx) [2](https://zh.wikisource.org/wiki/%E6%B5%A3%E6%BA%AA%E6%B2%99%20%28%E8%98%87%E8%BB%BE%29) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/124.jpg) |
| 《清平乐》 | 宋·黄庭坚 | 六年级下册·古诗词诵读 10 清平乐（旧版） | 通说 | [1](https://www.gushiwen.cn/shiwenv_315cf2d8892b.aspx) [2](https://zh.wikisource.org/wiki/%E6%B8%85%E5%B9%B3%E6%A8%82%20%28%E9%BB%83%E5%BA%AD%E5%A0%85%29) [3](https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/06422d77-21f1-45c3-b409-fa2947eee424.t/zh-CN/1772437268359/transcode/image/125.jpg) |

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

Tester: `test.yaml` (`learn-chinese-poetry-grade6-test`, eino), shared by every implementation:

- `tests/giztest/learn-chinese-poetry-grade6/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-poetry-grade6/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/learn-chinese-poetry-grade6/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/learn-chinese-poetry-grade6/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has 8 target responses; `recite-exact`, `background-label`, `unknown-boundary`, and `other-grade-poem` guard against hallucination and refusals:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请从指定中文开场开始。 | 必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字 |
| 2 | `poem-intro` | 我们刚学了《六月二十七日望湖楼醉书》，你给我讲讲吧。 | 必须承接这首诗并正确说出作者苏轼；只讲知识卡内的作者或背景；最多一个问题；30-360字 |
| 3 | `recite-exact` | 你能把这首诗完整地念给我听吗？ | 必须逐字念出课本正文“黑云翻墨未遮山，白雨跳珠乱入船。卷地风来忽吹散，望湖楼下水如天。”，不得改字漏字；20-360字 |
| 4 | `background-label` | 这首诗是在什么情况下写的？是有记载的，还是一般认为的，还是传说？ | 必须按知识卡讲背景“熙宁五年（1072）苏轼任杭州通判，六月二十七日游西湖，在望湖楼饮酒时写下。”，并说明它属于史实；不得添加知识卡外的细节；20-360字 |
| 5 | `unknown-boundary` | 诗人写这首诗那天中午吃的是什么？ | 知识卡没有这个细节，必须明确说没有记载或不确定，不得编造食物、地名或人名，也不得用可能、大概去猜；10-320字 |
| 6 | `other-grade-poem` | 我还会背《静夜思》，你能念给我听吗？ | 《静夜思》是一年级的诗，必须正常念出全文“床前明月光，疑是地上霜。举头望明月，低头思故乡。”，不得婉拒；20-360字 |
| 7 | `memory-store` | 请记住：我今天学会了《六月二十七日望湖楼醉书》，下次想学《泊船瓜洲》。只确认你已经记住。 | 必须确认已记住今天学会的诗和下次想学《泊船瓜洲》；4-320字 |
| 8 | `memory-recall` | 重连后，请只说我下次想学哪首诗。 | 重载后必须从长期记忆准确回忆《泊船瓜洲》；只回答诗名；2-200字 |

Run:

```sh
make test-e2e RAID=learn-chinese-poetry-grade6 PARALLEL=2
```
