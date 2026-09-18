# Giztest 测试

测试布局为 `tests/giztest/{smoke,quality,soak}/<raid>.<implementation>.giztest.yaml`，每个文件只运行一个实现，共 517 个三档文件。implementation 与 workflow 文件名一致，例如 `flowcraft`、`eino`、`flowcraft.multi-role`、`eino.multi-role`。文档名为 `<raid>.<tier>.<implementation>`。另有 `device/` 的 124 个设备流程测试和 `h106/` 的 2 个外部设备测试，合计 643 个 `.giztest.yaml`；`reports/` 仅存运行产物，不计入用例。

| 档位 | 文件数 | 定义 |
| --- | ---: | --- |
| smoke | 175 | 速度、延迟、响应度：开场、角色探针、RealTime，完整音频与独立首响应 |
| quality | 175 | 质量控制与安全围栏：剧情、转场、更正、语言、角色边界；只保留确定性断言 |
| soak | 167 | Tester 与被测 workflow 长回合对跑，检查记忆、重载及长程一致性 |
| device | 124 | H106 进入流程：`开始` → `我选第一个` → `继续` → 退出重进 → `继续上次的内容` → `开始`，每轮必须以问孩子的问题结尾 |

`device/` 覆盖 19 个 story、11 个 adventure 的四个实现和 Journey 的四个实现。H106 在孩子确认进入时只提交一次 `开始` 或 `继续上次的内容`，之后只有孩子按键说话才有输入，所以每轮回复都必须以问题结尾，文字匹配 `[？?][”"’」』）)]*\s*$`，并要求 text/audio EOS。原版 story 另外要求：两次 `开始` 都输出 `第 1 章` 与第一章标题，章节结束轮提到 `继续`，`继续` 后输出 `第 2 章` 与第二章标题，重进后的 `继续上次的内容` 含第二章标题且不含 `第 1 章` 或玩法说明；multi-role 不得残留 `【】`；Journey 的 `开始` 必须从石猴开场且不出现 Tester 路线里的 `明月`、`清禾`、`青铜铃`。文件由 `ruby scripts/test/device-flow.rb` 生成，`make test-unit-resources` 用 `--check` 校验文件未过期、目标 workflow 含对应契约；不登记在 `raid.json`，用 `make test-e2e TIER=device` 运行。

55 个 raid 均有 smoke/quality；`ast-translate` 和 `doubao-realtime` 是音频专用目标，没有 Tester 长回合协议，故无 soak，其余 53 个均有三档。Murder Mystery 只有 Flowcraft original/multi-role；Journey 分别运行 `flowcraft`、`eino-history`、`eino-memory-async`、`eino-memory-recall`。AST 按七个 workflow 拆分，`zh-en-auto` 同一文件保留两个方向，不把不同翻译方向当作等价实现；Doubao 使用 `conversation` 文件名。

```sh
export GIZCLAW_TEST_ENDPOINT=<host:port>
export GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-token>
make test-e2e TIER=smoke RAID=story-aesop
make test-e2e TIER=quality RAID=all
make test-e2e TIER=soak RAID=journey-guide
make test-e2e TIER=all RAID=story-aesop
make test-unit-resources
make test-unit-voices
```

默认 `TIER=all RAID=all PARALLEL=4 APPLY=0`。`TIER` 只接受 `smoke|quality|soak|all`，`RAID` 接受 raid 名或 `all`；选中 raid 时逐档选择 `<raid>.*.giztest.yaml`，通过 `gizclaw test run --parallel "$PARALLEL"` 并发运行文件。`all` 跳过不适用档，显式选择不存在的档会失败。H106 不进入 `make test-e2e`，按其设备环境单独执行 `gizclaw test run tests/giztest/h106`。`REPORT` 可指定 JSON 路径，默认写入 `reports/`。

`APPLY=1` 的原行为保持：使用 `GIZCLAW_CONTEXT` 应用全部 workflows、testing RuntimeProfile 与 testing token，再执行选中的测试。它需要 Admin 权限，普通运行只需 Peer 接入点与 token。

非 RealTime 往返的完整响应保留 6s 首字、90s 完整响应等原门槛；smoke 检查 text/audio EOS、非空音频、音频流闭合且无重叠、按设备听感检查 `/audio_pacing/underruns == 0` 且 `/audio_pacing/minimum_buffer_ms >= 0`（Giztest 的 500ms 预缓冲播放模型）。开始播放前的包间隔不代表设备听到卡顿；`max_interval_ms` 保留在 evidence 中用于诊断，不作为失败条件。独立 `completion: first_response` 探针要求首字 2s、首音 3s，主动结束流，因此不要求该探针 EOS。两分钟是速度目标，后期角色前置和完整语音可能超过；文件总 timeout 是运行预算，不能作为放宽单步门槛的依据。运行 CLI 必须支持 `/audio_integrity` 与 `/audio_pacing`，并且不低于 GizClaw v0.18.10：更早的 CLI 在 realtime 首响应探针里要等语音和尾静音同步发完才开始计时，且没有首个 BOS 前的音频暂存（GizClaw/gizclaw#1283），会报出与服务端无关的首字超时和音频边界违规。多角色语音要求服务端支持 `voice_adapter.speaker_voices`，文字不被 TTS 启动拖住要求服务端不低于 v0.18.10。

RealTime 的 `realtime_roundtrip` 负责验证完整往返：events/text 非空、text/audio EOS、audio_bytes >= 1，并保留统一的 audio_integrity 与 underruns/minimum_buffer 检查，不设置首字、首音或 EOS 耗时上限。该步骤的 first_text_ms 从开始发送输入语音计时，包含约 4s 输入语音及尾静音，正常可达 6.5–7.3s，不能套用 6s 首字门槛。随后的 `realtime_roundtrip_first_response`（原测试的 `realtime_first_response`）独立负责延迟验收，所有实现均保留首字 2s、首音 3s 的 timeout 和 maximum 断言。

不同实现通过文件级并发运行；需要的 speech 输入在各文件内独立生成。quality 保留 peer_stream 并行组和每个 suite 内的原始步骤顺序，将短 suite 向最后一轮对齐，使角色、路由、转场在同轮完成后立即进入 finally。较晚启动的 client 在首次注册前 reconnect，避免文件启动时建好的连接已经过期。finally 的原有历史输出、stop、Workspace/Peer 删除完整保留，失败时仍执行。

不再对每个响应轮次发送全量 keepalive。独立 Workspace 准备阶段仍会让其它已注册 client 等待过久的位置保留 `*_setup_keepalive_*`（`server.run.status`）；Journey soak 在三个 90s recall barrier 之间保留一个 Tester 的 `*_recall_keepalive`。当前 smoke 1、quality 268、soak 4，共 273 个；每个都通过删除反证检查，删掉任一个会造成静态空闲预算超限。原有 3,735 个 keepalive 步骤全部移除，跨实现等待也随文件拆分消除。

`test-unit-resources` 检查文件名/文档名、每档实现清单、raid.json 单实现登记、Voice/角色闭环和真实 routing-cases 脚本。按 variant 比较 `<raid>.flowcraft*.giztest.yaml` 与 `<raid>.eino*.giztest.yaml` 的完整 steps/finally（展开并行父步骤的断言），Journey 的三个 Eino 变体分别与 Flowcraft 比较。仅规范化 client/标识符、workflow_name 和 Workspace parameters；输入、expect、capture、timeout、collection、relay 计划保持一致。仅真实 TTS 能力差异沿用音频断言例外。

空闲规则累计某 client 两次操作之间其它步骤的预算，包含 finally；显式 timeout 按原值计算，无显式 timeout 的控制操作按 30s 调度余量计算，output 为 0。并行组中每个参与 client、relay 中双方均视为持续有流量。间隔超过 180s、晚启动未重连、注册前保活、冗余保活都会失败。这是静态调度检查，不是网络时延上限或真实 E2E 验收；没有放宽或改动原有响应门槛。quality 不创建 Tester，不执行长 relay；预算沿用原值（story/adventure 30m，其余 10m）。

Journey quality 另保留七回合 benchmark（四实现同输入同门槛）；soak 的四实现采用原门槛交集，并统一 recall barrier。eino-history 无持久 Memory 的差异可能导致 recall 失败，不作豁免。长剧情实际轮次以 relay 的 max_turns、completed_turns 和 Tester route 为准。

首响应探针主动提前结束后，smoke 显式停止当前 run 并 reload 已选 Workspace，再开始下一探针，避免未读尾音污染下一轮音频完整性证据。`audio_integrity` 的流闭合、不重叠和 violations 门槛保持不变。

quality 不重复 smoke 中逐项相同的 285 个首响应探针。其余原有文本、音频 EOS、首字/首音、第一人称、知识边界、转场、路由和安全断言均保留；不会仅因文本 EOS 提前进入下一轮。学习类 quality 用新建 Workspace 执行安全围栏，chat-assistant 用三轮事实建立/更正的确定性检查，完整长程记忆及裁判均在 soak。

story-aesop / adventure-history 的 quality 在 finally 清理前读取各 client 最新一条 Workspace 历史，并输出类型和正文到运行日志，辅助定位文本围栏失败；报告 JSON 保留相应步骤与延迟。该观测不替代原 peer_stream 断言。

story-aesop soak 每个文件只包含该实现与对应 Tester；长 relay 和裁判完成后立即 finally 清理，因此已移除原有为跨实现等待设置的注册前及清理前 reconnect。relay 和裁判断言不变。

### Original Eino voice behavior

Original story, adventure and learn Eino Workflows use their Workflow-scoped default Voice for the complete primary text output; multi-role Eino variants add character Voice switching. Both engines use ASR for paced RealTime audio input. Journey Eino history, asynchronous-memory and recall variants also retain ASR and the narrator default Voice. RuntimeProfiles bind these aliases to the same role Voice as Flowcraft.

The smoke RealTime probes require complete text/audio output and separate 2-second text / 3-second audio first responses for TTS-capable implementations. Offline checks validate Eino Voice ownership, manifest declarations and resolution in both RuntimeProfiles alongside tier parity and multi-role Voice closure.
