# 酒店图文秀工作流 · RunningHub / ComfyUI

这套工作流用于把同一家酒店的照片整理成有封面、章节、文案和统一字体的图文作品。参考图只用来理解「酒店图文秀」这种形式，没有把参考图中的酒店、品牌或承诺当成你的酒店资料。

交付状态：**已实现节点源码、3 份可导入工作流和 3 份 API 格式文件；完成本地排版测试与参数静态核对；尚未在你的 RunningHub 实例执行，也没有调用付费模型。** 导入 JSON 不会自动让云端安装新节点。

## 先选路线

| 文件 | 用途 | 自创节点 | 主要边界 |
|---|---|---|---|
| `example_workflows/03_仅现成节点_生成式设计稿.json` | 最快尝试，6 张照片生成一张带文案的竖版设计稿 | 无，使用 RunningHub 官方开源节点包和原生节点 | 实景、汉字、字体都可能被生成模型改动，必须复核；不等同于精确长图排版 |
| `example_workflows/02_精确排版_多图输入.json` | 推荐的正式制作路线，模型策划，程序拼原照片 | 本包 2 个节点 | RunningHub 必须能安装/提供本包；默认连 6 张，可增减 |
| `example_workflows/01_精确排版_ZIP输入.json` | 同一套精确排版，ZIP 或一次选择多图 | 同上 | ZIP 按钮还需要云端允许本包前端扩展与上传路由；不允许时改用多图连线版 |

文件名带 `.api.json` 的是 API prompt，供程序或支持 API 格式导入的工具使用。**在画布上优先导入不带 `.api` 的 JSON。**

“无自创节点”不等于“只有 ComfyUI 核心节点”。路线 03 仍依赖现成的 `ComfyUI_RH_OpenAPI`，你的云端实例是否提供同一版本需要实际核对。

## 为什么有两条路线

现成的多图图生图模型已经能做图片理解、文案和图文设计，适合先看风格。但提示词不能保证酒店窗户、床型、摆设、商标和每个汉字都保持准确。

精确路线采用：

```text
ZIP / 多张 LoadImage
        ↓
HotelShowPrepare：读取、校正 EXIF 朝向、编号、完全重复去重、联系表
        ├── 原照片集合 ─────────────────────────────┐
        └── 联系表 + 酒店资料 + 策划提示词             │
                         ↓                           │
                RH LLM Chat Completions               │
             看图分类 / 文案 / 配色 / 标题字体          │
                         ↓ JSON                      │
                HotelShowRender ←─────────────────────┘
           校验 ID / 中文换行 / 比例排版 / 章节分页
                         ↓
              SaveImage 分页 + SaveImage 长图
```

本次查到的通用文字、拼图和 HTML 渲染方案各有用途，但没有核实到一套在你的 RunningHub 环境中已可用、同时覆盖可变数量素材、结构化策划、中文溢出检查和整节分页的现成节点组合。HTML 转图方案还依赖浏览器运行环境和模板部署。因此这里补了小型 Pillow 排版包，**不是断言这些功能只能自创节点实现**。

## 路线 03：先用现成节点出设计稿

1. 在 RunningHub 新建 ComfyUI 工作流，导入 `03_仅现成节点_生成式设计稿.json`。
2. 6 个 `LoadImage` 都选上你自己的酒店照片。少于 6 张时，删除多余的 LoadImage 及连线；不要留下没有文件的已连接节点。
3. 打开“现成节点方案”节点，把提示词中的酒店名称与已确认卖点改成真实资料。不要把参考海报截图作为酒店实景输入。
4. 默认是 `2k`、`9:16`；根据版面字量决定是否改 `4k`。选择更高分辨率可能增加费用，以运行页为准。
5. 按平台节点要求配置凭据或选择云端可用的对应模型节点，再运行。

该工作流使用的节点类型为 `RH_RhartImageNProOfficialEdit`，显示名称是官方包中的“全能图片 PRO-图生图-官方稳定版”。支持最多 10 个独立图片插槽，本模板预接 6 个。要增加图片，复制 LoadImage 并连接 image7～image10。**不要把普通 IMAGE batch 直接接这个图生图节点，当前官方节点工厂对每个插槽的多帧行为未在本项目验证。**

成品必须核对实景、中文字形、事实、照片是否串用。它输出的是单页生成式设计稿；多页一致性与原照片精确保留请走精确路线。

## 精确路线：RunningHub 的安装前提

需要两个节点包：

- 现成官方包：[ComfyUI_RH_OpenAPI](https://github.com/HM-RunningHub/ComfyUI_RH_OpenAPI)。负责多模态理解；本交付不重新分发其源码。
- 本次提供的 `ComfyUI-HotelShow` 文件夹。只注册 `HotelShowPrepare` 和 `HotelShowRender` 两个节点，内含中文黑体、宋体字体与许可证。

**RunningHub 云端不能套用“在自己电脑上复制文件夹就会生效”的安装方式。** 请在你当前可用的节点管理/节点提交渠道中查找或部署节点包。若平台不开放个人节点安装，需要平台收录、协助安装，或使用具有安装权限的实例。此项未在你的账户核实，不能承诺普通会员一定可以自行安装。

如果平台暂时不能安装本包：路线 03 可以作为现成节点设计稿方案；精确路线的源码保留供安装后使用。也附了本地排版命令作为备用，但它是本地运行，不是已部署到 RunningHub 的云服务。

若是你有权限管理的标准 ComfyUI 服务端，把整个 `ComfyUI-HotelShow` 文件夹放入 `ComfyUI/custom_nodes/`，使用 **ComfyUI 的 Python 环境**安装 `requirements.txt` 后重启。不要另装不同版本的 torch 覆盖 ComfyUI 自带环境。建议 Python 3.10+。

## 精确路线：逐步运行

1. 导入 `02_精确排版_多图输入.json`，先用 4～6 张清晰实拍做首轮。
2. 在每个 LoadImage 选择图片；删除不用的加载节点。照片尺寸可以不同，无须先用 ImageBatch 把它们拉成同一尺寸。
3. “多图整理”中填写真实酒店名称、已确认资料、风格偏好。`source` 留空。12 个可选插槽可直接接不同尺寸图片；每个插槽也接受同尺寸 IMAGE batch，合计上限 24 张。
4. 多模态节点接收带编号的联系表，默认模型是官方节点源码内列出的 `google/gemini-3.1-flash-lite-preview`。如果当前账号的模型列表不含它，请从**当前可用且支持图片理解**的模型中选择 Gemini 或 Qwen-VL 等；不要选纯文本模型。
5. 默认 `temperature=0.3`、`max_tokens=10000`、`skip_error=false`。模型名称与权益可能变化，不把模板内名称视为永久可用承诺。
6. “精确排版”默认 `1080×1440` 每页，封面 1 页 + 正文 1～8 页；`photo_fit=contain` 保留完整画面并等比缩放。
7. 点击运行。从两个 SaveImage 节点分别取分页图和完整长图。分页在章节之间切分，不会从一张照片或一段正文中间截断。
8. 查看模型输出、排版报告中的 `review_notes` 和 `excluded`。JSON 结构通过校验不等于内容事实已经通过审核。

RunningHub 官方文档当前说明：**直接调用模型 API / LLM API 需要企业级-共享 API Key**，普通工作流调用 Key 不等同于这一权限。[API 说明](https://www.runninghub.cn/runninghub-api-doc-cn/)。云端内置节点是否能使用平台账户结算，以该节点实际界面为准。本工作流没有嵌入凭据。

标准 ComfyUI 上可按官方包说明配置环境变量 `RH_API_KEY` 或 `.env`，也可用其 `RH OpenAPI Settings` 节点接入 `api_config`。不要把带真实 Key 的工作流公开分享；SaveImage 的工作流元数据也可能包含上游参数。

## ZIP 输入

导入 `01_精确排版_ZIP输入.json`，在“多图整理”节点点击“上传 ZIP / 选择多张图片”。可单独上传一个 ZIP，或一次选择多张 JPG/PNG/WEBP。上传后 `source` 自动填写服务端相对路径。

约束：最多 24 张；本包上传总大小最多 29 MiB；单图最大 25 MiB、4000 万像素；ZIP 内图片解压后总量不超过 100 MiB。不支持 HEIC、GIF、嵌套 ZIP 或加密 ZIP。图片按自然文件名顺序编号，忽略 `__MACOSX` 和隐藏文件。完全重复图片按解码后的像素去重；相似但不完全重复的照片由模型判断并给出排除理由。

若按钮不出现或返回 404，通常是云端没有加载本包前端/路由，换多图连线版。不要把你电脑的 `C:\...` 或 `/Users/...` 路径填进云端 source。

RunningHub 社区已有 ZIP 批处理入口示例，但 `rhuploadzip` / `LOAD IMAGE ZIP` 的当前接口未在本实例验证，因此本 JSON 没有伪造其节点定义。若你使用的现成 ZIP 节点输出 **一个 IMAGE batch**，可接 HotelShowPrepare 的 image1。若输出 **IMAGE list**，ComfyUI 可能逐张执行整条链，需先用兼容的列表汇聚节点汇总；不能直接假定等同于 batch。若只输出目录路径或字符串，不能接 IMAGE 插槽。

## 版式与字体能控制到什么程度

- 可选择奶油杂志 `ivory`、自然度假 `sage`、深色精品 `charcoal`；模型选色，用户可覆盖。
- 标题可由模型选择 sans/serif；已附 Noto Sans SC 与 Noto Serif SC 中文字体。字体选择来自白名单，不会让模型虚构系统不存在的字体名。
- 一张图用主图；两张按横竖比选择上下或按比例分栏；三张可用主图加双图；四张用四宫格。顺序由策划 JSON 决定。
- `contain` 不裁掉照片，可能保留配色留边；`cover` 填满图片区域，会中心裁切，**没有实现基于人脸/物体的智能焦点裁切**。
- 默认不对实景做生成式重绘。会校正方向、转换 RGB、等比缩放，长边大于 2400 像素的素材会降采样，因此不是像素级无损归档工具。
- 本版是受约束的模板排版，不是任意杂志版式搜索，也不保证复刻参考图每处装饰。模板约束使照片引用、文字和分页更可控。
- 标题和正文按实际字体宽度换行；一定范围内自动缩字号，仍放不下就报错，避免静默截字。

1080×1440 是制作默认值，**不是声称携程官方要求的尺寸**。上传前按你商家后台当前的像素、比例、格式、大小要求调整；本工作流不包含携程自动发布。长图最大 3200 万像素，可降低宽度或减少章节。

## 酒店资料建议这样填写

```text
酒店名称：填写真实名称（放在 hotel_name）
已确认资料：
- 照片 01～03 是行政大床房；04 是大堂；05 是早餐区。
- 已确认的服务：……
- 已确认的品牌/设施：……
- 不希望出现的表达：……
```

不要猜测。床品品牌、TOTO 卫浴、距离地铁几分钟、全天服务、免费早餐、房间面积、星级和评分，只有在酒店资料明确提供时才允许进入文案。模型仍可能出错，正式发布前需核对。

## 修改文案、重排、排错

模型的 `response` 是策划 JSON，结构参考 `examples/测试策划.json`。可以修改 title、subtitle、各节 body、photo_ids 和 theme，再把**完整 JSON**粘贴到排版节点的 `manual_plan`，它将覆盖模型文本。相同输入通常可利用 ComfyUI 缓存，但不能保证平台不会重新调用模型。要完全避免模型调用，使用下面的离线渲染命令。

| 现象 | 处理 |
|---|---|
| 节点变红/缺失 | 按精确类型检查安装与版本；不要把显示名相似的节点当成接口相同 |
| 401/403/额度错误 | 检查 Key 权益、额度与节点配置；此时不继续排版 |
| 模型返回 JSON 不合法 | 检查输出截断，提高 max_tokens；或修订 JSON 后重排 |
| 素材 ID 不存在/缺少逐图分析 | 使用当前联系表重新策划，不能复用另一批照片的 JSON |
| 字体缺失 | 确认完整复制 fonts；自选字体需使用云端实际存在的路径 |
| 文字过长 | 缩短对应章节正文或标题，按错误提示修改 |
| 图片留边较多 | 使用适合比例的组合、调换顺序，或接受中心裁切后改 cover |
| 模型把不同房型混在一起 | 在资料中标注图片文件名与房型关系，或先按房型拆包 |

排版节点会将审核后的计划和报告写到 ComfyUI `output/hotelshow_reports/`。标准 ComfyUI 可直接读取；RunningHub 是否把这些 JSON 列为可下载输出尚未核实，不依赖它们作为图像结果入口。计划/报告同时作为 STRING 输出，可接你平台已有的文本展示/保存节点。

## 本地备用与测试样张

没有云端安装权限时，可以在本地用同一排版引擎处理已经审核的 JSON：

```bash
python -m pip install Pillow numpy
python render_local.py \
  --input examples/测试素材_非酒店实拍.zip \
  --hotel "酒店图文秀 · 排版示例" \
  --plan examples/测试策划.json \
  --output local_result
```

不传 `--plan` 时，只输出联系表和策划提示词，便于交给支持看图的模型。此备用工具本身不调用模型，不收费，也不是完整自动运行的云工作流。

`examples` 中所有颜色块均为**测试占位素材**，文案与 JSON 是人工构造的测试计划。它们只展示本地排版和字体效果，不代表已分析真实酒店照片或已跑通付费模型。

## 验证范围与资料来源

已完成：16 项排版与输入测试、3 份画布图和对应 API prompt 的参数/连线静态校验、占位素材实际渲染与视觉检查。未完成：真实 RunningHub 云端导入执行、真实模型输出质量评估、你的账号计费/权限验证、真实酒店原图的端到端试跑。

接口核对日期：2026-09-26。节点 schema 快照见 `tests/node_schema_snapshot.json`。上游节点可能变化。

- [RunningHub 官方节点源码与安装说明](https://github.com/HM-RunningHub/ComfyUI_RH_OpenAPI)
- [官方 LLM 节点定义](https://github.com/HM-RunningHub/ComfyUI_RH_OpenAPI/blob/main/nodes/llm_chat.py)
- [官方图像节点工厂](https://github.com/HM-RunningHub/ComfyUI_RH_OpenAPI/blob/main/nodes/node_factory.py)
- [RunningHub API 文档](https://www.runninghub.cn/runninghub-api-doc-cn/)
- [RunningHub ZIP 批处理公开示例](https://www.runninghub.cn/post/2002655448807403521)
- [现有 HTML 转图节点项目](https://github.com/liuqianhonga/ComfyUI-Html2Image)，未验证其在你的云端实例可用。
- [Noto Sans SC 字体来源](https://github.com/google/fonts/tree/main/ofl/notosanssc)
- [Noto Serif SC 字体来源](https://github.com/notofonts/noto-cjk/tree/main/Serif/SubsetOTF/SC)

节点代码使用 MIT 许可；字体遵循随包附带的 SIL Open Font License。第三方模型服务及 RunningHub 的使用规则独立适用。
