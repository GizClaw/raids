# Giztest 测试

测试布局为 `tests/giztest/{smoke,quality,soak}/<raid>.giztest.yaml`，同一文件覆盖该 raid 的所有实现，共 163 个三档文件。另保留 `h106/` 的 2 个外部设备测试，合计 165 个 `.giztest.yaml`；`reports/` 仅存运行产物，不计入用例。

| 档位 | 文件数 | 定义 |
| --- | ---: | --- |
| smoke | 55 | 速度、延迟、响应度：开场、角色探针、RealTime，完整音频与独立首响应 |
| quality | 55 | 质量控制与安全围栏：剧情、转场、更正、语言、角色边界与 Tester 裁判 |
| soak | 53 | Tester 与被测 workflow 长回合对跑，检查记忆、重载及长程一致性 |

55 个 raid 均有 smoke/quality；`ast-translate` 和 `doubao-realtime` 是音频专用目标，没有 Tester 长回合协议，故无 soak，其余 53 个均有三档。Murder Mystery 只有 Flowcraft；Journey 在同一文件覆盖 Flowcraft 与三个 Eino 变体；AST 单文件覆盖八个翻译方向，不把不同方向当作等价实现。

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

默认 `TIER=all RAID=all PARALLEL=1 APPLY=0`。`TIER` 只接受 `smoke|quality|soak|all`，`RAID` 接受 raid 名或 `all`；选中 raid 时逐档选择 `<raid>.giztest.yaml`。`all` 跳过不适用档，显式选择不存在的档会失败。H106 不进入 `make test-e2e`，按其设备环境单独执行 `gizclaw test run tests/giztest/h106`。`REPORT` 可指定 JSON 路径，默认写入 `reports/`。

`APPLY=1` 的原行为保持：使用 `GIZCLAW_CONTEXT` 应用全部 workflows、testing RuntimeProfile 与 testing token，再执行选中的测试。它需要 Admin 权限，普通运行只需 Peer 接入点与 token。

完整响应保留 6s 首字、90s 完整响应等原门槛；smoke 检查 text/audio EOS、非空音频、音频流闭合且无重叠、最大包间隔 150ms 与零 underrun。独立 `completion: first_response` 探针要求首字 2s、首音 3s，主动结束流，因此不要求该探针 EOS。两分钟是速度目标，后期角色前置和完整语音可能超过；文件总 timeout 是运行预算，不能作为放宽单步门槛的依据。运行 CLI 必须支持 `/audio_integrity` 与 `/audio_pacing`。

smoke 的响应步骤按实现并行，共用一次合成的输入音频；quality/soak 按实现顺序执行，Tester 协议和 relay 计划不变。任一步失败会停止后续步骤，未运行不能算通过，finally 仍执行并单独报告清理失败。短连接中断和未创建 Workspace 的清理错误需要单列记录。

`test-unit-resources` 检查三档实际文件、raid.json 登记、Voice/角色闭环、真实 routing-cases 脚本与 schema，并比较同文件各实现的完整 steps/finally 序列。仅规范化 client/标识符、workflow_name 和 Workspace parameters；共同输入、expect、capture、timeout、collection、relay 计划必须一致。路由注释不算运行断言，内部 state/history/memory 的路由检查继续使用 `routing-cases.json`。

Journey quality 另保留七回合 benchmark（四实现同输入同门槛）；soak 的四实现采用原门槛交集，并统一 recall barrier。eino-history 无持久 Memory 的差异可能导致 recall 失败，不作豁免。长剧情实际轮次以 relay 的 max_turns、completed_turns 和 Tester route 为准。
