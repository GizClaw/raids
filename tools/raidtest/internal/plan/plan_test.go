package plan

import (
	"strings"
	"testing"
	"time"
)

func TestValidateRejectsDuplicateCaseAndUnknownDriver(t *testing.T) {
	p := Plan{Version: "v1", Name: "sample", Driver: "flowcraft", Cases: []Case{{ID: "one", Turns: []Turn{{ID: "turn", User: "hello"}}}, {ID: "one", Turns: []Turn{{ID: "turn", User: "again"}}}}}
	if err := p.Validate(); err == nil {
		t.Fatal("expected duplicate error")
	}
	p.Driver = "unknown"
	if err := p.Validate(); err == nil {
		t.Fatal("expected driver error")
	}
}

func TestLoadBenchmarkPlans(t *testing.T) {
	for path, driver := range map[string]string{
		"../../plans/benchmarks/eino-journey-6s.yaml":                     "eino",
		"../../plans/benchmarks/flowcraft-journey-6s.yaml":                "flowcraft",
		"../../plans/benchmarks/story-aesop-comparison.yaml":              "scripted-comparison",
		"../../plans/benchmarks/story-alice-comparison.yaml":              "scripted-comparison",
		"../../plans/benchmarks/adventure-space-rescue-comparison.yaml":   "scripted-comparison",
		"../../plans/benchmarks/adventure-monster-maze-comparison.yaml":   "scripted-comparison",
		"../../plans/benchmarks/adventure-castle-mystery-comparison.yaml": "scripted-comparison",
	} {
		loaded, err := Load(path)
		if err != nil {
			t.Fatalf("%s: %v", path, err)
		}
		if loaded.Driver != driver {
			t.Fatalf("%s driver=%q want %q", path, loaded.Driver, driver)
		}
		for _, testCase := range loaded.Cases {
			for _, turn := range testCase.Turns {
				if turn.FirstResponse != 6*time.Second {
					t.Fatalf("%s turn %s first response=%s want 6s", path, turn.ID, turn.FirstResponse)
				}
			}
		}
	}
}

func TestValidateRejectsIncompletePersistenceBarrier(t *testing.T) {
	base := Turn{ID: "turn", User: "hello", ReloadBefore: true, PersistedBeforeReload: []string{"39码"}, PersistenceTimeout: time.Second}
	for name, mutate := range map[string]func(*Turn){
		"missing reload":  func(turn *Turn) { turn.ReloadBefore = false },
		"missing timeout": func(turn *Turn) { turn.PersistenceTimeout = 0 },
		"missing facts":   func(turn *Turn) { turn.PersistedBeforeReload = nil },
		"empty fact":      func(turn *Turn) { turn.PersistedBeforeReload = []string{" "} },
		"duplicate fact":  func(turn *Turn) { turn.PersistedBeforeReload = []string{"39码", " 39码 "} },
	} {
		t.Run(name, func(t *testing.T) {
			turn := base
			mutate(&turn)
			p := Plan{Version: "v1", Name: "sample", Driver: "flowcraft", Cases: []Case{{ID: "case", Turns: []Turn{turn}}}}
			if err := p.Validate(); err == nil {
				t.Fatal("expected persistence barrier validation error")
			}
		})
	}
}

func TestCommittedDefaultPlansAreValid(t *testing.T) {
	files := []string{"pet-care.yaml", "assistant-general.yaml", "assistant-doubao.yaml", "murder-mystery.yaml", "journey.yaml", "translations.yaml"}
	for _, file := range files {
		t.Run(file, func(t *testing.T) {
			p, err := Load("../../plans/default/" + file)
			if err != nil {
				t.Fatal(err)
			}
			if len(p.Cases) == 0 {
				t.Fatal("plan has no cases")
			}
		})
	}
}

func TestDefaultMurderMysteryPlanKeepsLongFormRecoveryCoverage(t *testing.T) {
	p, err := Load("../../plans/default/murder-mystery.yaml")
	if err != nil {
		t.Fatal(err)
	}
	if len(p.Cases) != 1 {
		t.Fatalf("cases=%d", len(p.Cases))
	}
	if !p.Paired || p.NeedsAgent() || p.NeedsJudge() || p.Persona != "" {
		t.Fatal("paired Murder plan must leave dialogue and semantic judging to its Tester Workflow")
	}
	turns := p.Cases[0].Turns
	if len(turns) < 20 || len(turns) > 30 {
		t.Fatalf("long-form plan has %d turns", len(turns))
	}
	indexes := map[string]int{}
	for index, turn := range turns {
		indexes[turn.ID] = index
	}
	for _, id := range []string{"inspect-balcony", "interview-chef", "inspect-study", "inspect-thread", "analyze-contradictions"} {
		turn := turns[indexes[id]]
		if turn.MinRunes < 30 || turn.MaxRunes < 300 {
			t.Fatalf("turn %q must exercise a complete spoken scene, got %d-%d runes", id, turn.MinRunes, turn.MaxRunes)
		}
	}
	opening := turns[indexes["opening"]]
	if opening.MinRunes != 40 || opening.MaxRunes != 100 || !containsAll(opening.Required, "22:00", "沈鹤年", "二楼书房", "雨夜", "自由调查") {
		t.Fatalf("opening must enforce the concise whitelist without padding, got %#v", opening)
	}
	if turns[indexes["inspect-thread"]].MaxRunes != 480 {
		t.Fatal("multi-part lock and fiber inspection must have enough room for every requested result")
	}
	if turns[indexes["inspect-rear-corridor"]].MinRunes != 25 || turns[indexes["inspect-will"]].MinRunes != 25 || turns[indexes["accuse-wrong-suspect"]].MinRunes != 30 || turns[indexes["mistaken-outage-theory"]].MinRunes != 20 || turns[indexes["delayed-correction-recall"]].MinRunes != 20 || turns[indexes["irrelevant-garden-route"]].MinRunes != 10 || turns[indexes["revisit-phonograph"]].MinRunes != 40 {
		t.Fatal("complete concise answers must not be rejected merely for avoiding padding")
	}
	if turns[indexes["inspect-balcony"]].MinRunes != 40 || turns[indexes["correct-shoe-size"]].MinRunes != 4 {
		t.Fatal("explicitly complete balcony and correction replies must use evidence-backed minimums")
	}
	if turns[indexes["analyze-contradictions"]].MinRunes != 80 || turns[indexes["conclude"]].MinRunes != 50 || turns[indexes["conclude"]].MaxRunes != 130 {
		t.Fatal("the explicit three-sentence conclusion request must keep its user-specified budget")
	}
	for _, id := range []string{
		"inspect-balcony", "inspect-kitchen", "inspect-study", "inspect-phonograph",
		"interview-chef", "interview-housekeeper", "interview-heir", "inspect-heir-room",
		"irrelevant-garden-route", "mistaken-outage-theory", "correct-shoe-size",
		"delayed-correction-recall", "analyze-contradictions", "conclude",
	} {
		if _, ok := indexes[id]; !ok {
			t.Fatalf("missing coverage turn %q", id)
		}
	}
	correction := indexes["correct-shoe-size"]
	recall := indexes["delayed-correction-recall"]
	if len(turns[indexes["establish-shoe-size"]].Forbidden) != 2 || turns[indexes["establish-shoe-size"]].Forbidden[0] != "后廊" || turns[indexes["establish-shoe-size"]].Forbidden[1] != "更正" {
		t.Fatal("shoe-size establishment must not reveal the later source")
	}
	if !containsAll(turns[indexes["inspect-study"]].Forbidden, "你要看看", "要不要检查", "是否要检查", "建议检查") {
		t.Fatal("study inspection must not steer the player to a fixed next clue")
	}
	if len(turns[correction].Forbidden) != 2 || turns[correction].Forbidden[1] != "后廊" {
		t.Fatal("shoe-size correction must not reveal the later source")
	}
	if !containsAll(turns[indexes["opening"]].Forbidden, "留声机", "唱片", "遗嘱", "木蜡", "鞋印", "钥匙", "细线") {
		t.Fatal("opening must not leak investigation evidence")
	}
	if !containsAll(turns[indexes["opening"]].Forbidden, "管家巡查", "撞开", "推开", "书房门", "壁灯", "烟草", "纸张", "开了门") {
		t.Fatal("opening must not invent who discovered the body or how the study was opened")
	}
	if !containsAll(turns[indexes["inspect-heir-room"]].Forbidden, "本案纤维", "同批的细钓鱼线", "现场钓鱼线") {
		t.Fatal("heir-room turn must forbid premature line matching")
	}
	if !containsAll(turns[indexes["interview-heir"]].Forbidden, "公开的固定关系矛盾", "没说过和沈鹤年", "没有公开矛盾", "没有矛盾") {
		t.Fatal("heir interview must not invent relationship commentary")
	}
	if !containsAll(turns[indexes["interview-lawyer"]].Required, "不清楚") {
		t.Fatal("lawyer interview must preserve uncertainty about the final-night conversation")
	}
	if !containsAll(turns[indexes["inspect-rear-corridor"]].Required, "门锁", "39") {
		t.Fatal("rear-corridor inspection must report the lock and corrected shoe size")
	}
	if !containsAll(turns[indexes["inspect-rear-corridor"]].Forbidden, "其他区域不连接", "其他区域不连通", "同源湿鞋印") {
		t.Fatal("rear-corridor inspection must not invent connectivity or same-source attribution")
	}
	if !containsAll(turns[indexes["opening"]].Forbidden, "下起雨夜") {
		t.Fatal("opening must forbid the observed malformed rain-night phrase")
	}
	if !containsAll(turns[indexes["inspect-balcony"]].Forbidden, "阳台地面没有发现异常", "地面没有异常", "地面没有发现痕迹", "地面没有痕迹") {
		t.Fatal("balcony inspection must not invent negative ground findings")
	}
	if !containsAll(turns[indexes["inspect-thread"]].Forbidden, "细线匹配", "钓鱼线匹配", "特征匹配", "细线同源", "钓鱼线同源") {
		t.Fatal("thread inspection must preserve feature-consistency evidence strength")
	}
	if !containsAll(turns[indexes["inspect-window"]].Forbidden, "没有其他异常", "其他异常", "没有遗漏", "没有额外发现") {
		t.Fatal("window inspection must not invent generic negative findings")
	}
	if !containsAll(turns[indexes["inspect-window"]].Forbidden, "没有其他痕迹", "没有额外收获", "异常痕迹") {
		t.Fatal("window inspection must reject observed variants of invented generic negative findings")
	}
	if !containsAll(turns[indexes["inspect-study"]].Forbidden, "没有其他异常", "其他异常", "没有发现死者额外", "没有发现相关活动物品") || !containsAll(turns[indexes["inspect-will"]].Forbidden, "没有其他异常", "其他异常") {
		t.Fatal("study and will inspection must not invent generic negative findings")
	}
	if !containsAll(turns[indexes["inspect-fireplace"]].Forbidden, "主钥匙备用钥匙") {
		t.Fatal("fireplace inspection must forbid malformed key attribution")
	}
	if !containsAll(turns[indexes["interview-housekeeper"]].Forbidden, "来电后没多久", "喊着众人", "一起开了门") {
		t.Fatal("housekeeper interview must reject invented discovery and door-opening testimony")
	}
	if !containsAll(turns[indexes["irrelevant-garden-route"]].Forbidden, "我查看", "我检查", "我调查", "落叶", "泥土", "攀爬", "翻越") {
		t.Fatal("game master must not take the player's investigation action in first person")
	}
	if !containsAll(turns[indexes["accuse-wrong-suspect"]].Forbidden, "其他物证和证词", "其他证据和证词", "其他物证都", "其他证词都", "其他能印证或反驳") {
		t.Fatal("chef challenge must not generalize unrelated evidence")
	}
	for _, id := range []string{"delayed-correction-recall", "summarize-confirmed-clues", "analyze-contradictions", "conclude"} {
		if !containsAll(turns[indexes[id]].Forbidden, "同源后廊鞋印", "后廊同源鞋印", "同源湿鞋印") {
			t.Fatalf("%s must not merge the external same-source report with the rear-corridor print", id)
		}
	}
	if !containsAll(turns[indexes["inspect-will"]].Forbidden, "一半", "百分", "没有发现签名异常", "没有发现笔迹异常", "纸张没有异常", "落款没有异常", "指纹没有异常") {
		t.Fatal("will inspection must forbid invented quantities and negative forensic findings")
	}
	if !containsAll(turns[indexes["mistaken-outage-theory"]].Forbidden, "后廊", "湿鞋印", "书房锁具", "细线纤维", "拉扯磨痕", "操作密室", "所有证词都显示", "无人在书房附近", "死亡正好发生在", "死亡发生在21:10", "死于21:10") {
		t.Fatal("outage theory must not leak unvisited evidence or invent a universal witness conclusion or death time")
	}
	if !containsAll(turns[indexes["inspect-phonograph"]].Forbidden, "起到误导死亡时间的作用", "确认用于误导死亡时间", "就是用来误导死亡时间") {
		t.Fatal("phonograph inspection must keep the time-misdirection theory unconfirmed")
	}
	if !containsAll(turns[indexes["accuse-wrong-suspect"]].Forbidden, "证据显示厨师全程", "物证显示厨师全程") {
		t.Fatal("wrong-suspect analysis must not convert testimony into physical evidence")
	}
	if !containsAll(turns[indexes["challenge-chef"]].Forbidden, "没有其他已发现的线索能印证或反驳", "没有其他线索能印证或反驳") {
		t.Fatal("chef challenge must reject unsupported universal claims about every other clue")
	}
	if !containsAll(turns[indexes["summarize-confirmed-clues"]].Forbidden, "相同木蜡", "木蜡匹配", "同源木蜡", "细线匹配", "钓鱼线匹配", "特征匹配", "细线同源", "钓鱼线同源", "雨靴与鞋印同源", "鞋印与雨靴同源", "与沈知秋的雨靴匹配") {
		t.Fatal("summary must preserve material and shoe-size evidence strength")
	}
	if !containsAll(turns[indexes["summarize-confirmed-clues"]].Forbidden, "所有物证和厨师", "所有物证都和厨师", "全部物证和厨师", "其他物证和厨师") {
		t.Fatal("summary must not generalize kitchen consistency to all evidence")
	}
	if !containsAll(turns[indexes["conclude"]].Forbidden, "细线匹配", "钓鱼线匹配", "特征匹配", "细线同源", "钓鱼线同源", "雨靴与鞋印同源", "鞋印与雨靴同源", "与沈知秋的雨靴匹配") {
		t.Fatal("conclusion must preserve shoe-size evidence strength")
	}
	if !containsAll(turns[indexes["analyze-contradictions"]].Forbidden, "雨靴与鞋印同源", "鞋印与雨靴同源", "确认鞋印属于沈知秋", "鞋印确定属于沈知秋", "鞋印是沈知秋的", "不在他回房的路上", "不在他回房的常规路线上") {
		t.Fatal("contradiction analysis must not attribute a size-only shoeprint")
	}
	if !containsAll(turns[indexes["delayed-correction-recall"]].Forbidden, "不在他回房的路上", "不在他回房的常规路线上") {
		t.Fatal("recall must not invent the heir-room route")
	}
	if !containsAll(turns[indexes["conclude"]].Forbidden, "木蜡指向沈知秋", "木蜡证明沈知秋", "房间木蜡、钓鱼线和现场痕迹") {
		t.Fatal("concise conclusion must reject over-compressed affirmative wood-wax evidence")
	}
	thread := turns[indexes["inspect-thread"]]
	if !containsAll(thread.Required, "书房", "锁具", "细线") {
		t.Fatal("lock-fiber evidence must remain deterministically gated")
	}
	if recall-correction < 6 {
		t.Fatalf("only %d intervening turns before delayed recall", recall-correction-1)
	}
	if !turns[recall].ReloadBefore {
		t.Fatal("delayed correction recall must reload the Workspace")
	}
	if !containsAll(turns[recall].PersistedBeforeReload, "39码") || turns[recall].PersistenceTimeout == 0 {
		t.Fatal("delayed correction recall must wait until the correction is durably recallable")
	}
	if len(turns[recall].Required) != 1 || turns[recall].Required[0] != "39" {
		t.Fatalf("delayed correction recall gates=%#v", turns[recall].Required)
	}
	if indexes["conclude"] != len(turns)-1 {
		t.Fatal("plan must end in the deterministic conclusion checkpoint")
	}
}

func TestDefaultJourneyPlanKeepsDistinctLongFormChoiceCoverage(t *testing.T) {
	p, err := Load("../../plans/default/journey.yaml")
	if err != nil {
		t.Fatal(err)
	}
	if len(p.Cases) != 1 {
		t.Fatalf("cases=%d", len(p.Cases))
	}
	turns := p.Cases[0].Turns
	if len(turns) != 20 {
		t.Fatalf("journey turns=%d", len(turns))
	}
	indexes := map[string]int{}
	for index, turn := range turns {
		indexes[turn.ID] = index
		if turn.MinRunes == 0 || turn.MaxRunes == 0 || turn.FirstResponse == 0 || turn.TotalResponse == 0 {
			t.Fatalf("turn %q lost the Journey response budget", turn.ID)
		}
	}
	for _, id := range []string{"origin", "river", "village", "temple", "mountain", "shelter", "cave", "waterfall", "diversion", "rescue", "night-camp"} {
		turn := turns[indexes[id]]
		if turn.MinRunes < 60 || turn.MaxRunes < 220 {
			t.Fatalf("turn %q must exercise a complete story beat, got %d-%d runes", id, turn.MinRunes, turn.MaxRunes)
		}
	}
	if turns[indexes["village"]].MinRunes != 100 || turns[indexes["village"]].MaxRunes != 320 {
		t.Fatal("multi-action village scene must have a larger narration budget")
	}
	for _, id := range []string{"choose-bridge", "correct-guide", "wrong-theory", "reload-recall", "diversion", "return-choice", "recap", "return"} {
		if _, ok := indexes[id]; !ok {
			t.Fatalf("missing Journey-specific coverage turn %q", id)
		}
	}
	if indexes["reload-recall"]-indexes["correct-guide"] < 5 || !turns[indexes["reload-recall"]].ReloadBefore {
		t.Fatal("Journey must exercise delayed corrected recall after reload")
	}
	if !containsAll(turns[indexes["reload-recall"]].Required, "明月", "青铜铃", "商队") || !containsAll(turns[indexes["reload-recall"]].Forbidden, "清禾") {
		t.Fatal("Journey reload must retain the corrected guide, carried item, and objective")
	}
	if !containsAll(turns[indexes["reload-recall"]].PersistedBeforeReload, "明月", "青铜铃", "商队") || turns[indexes["reload-recall"]].PersistenceTimeout == 0 {
		t.Fatal("Journey reload must wait for all durable recall facts")
	}
	if turns[indexes["scout"]].MaxRunes != 30 || !strings.Contains(turns[indexes["scout"]].User, "24字内") || !containsAll(turns[indexes["scout"]].Required, "青铜铃") {
		t.Fatal("Journey scout must retain its three-part meaning within a shorter latency budget")
	}
	if !containsAll(turns[indexes["choose-bridge"]].Judge, "choice-consequence") || !containsAll(turns[indexes["wrong-theory"]].Judge, "uncertainty-handling", "non-railroading") {
		t.Fatal("Journey must judge choice consequences and wrong-theory handling")
	}
	if !containsAll(turns[indexes["wrong-theory"]].Forbidden, "你打开货箱", "你继续前进", "你走进山洞", "商队就是迷路") {
		t.Fatal("Journey wrong-theory response must not take an unchosen player action")
	}
	if !containsAll(turns[indexes["wrong-theory"]].Judge, "no-scene-advancement") {
		t.Fatal("Journey wrong-theory response must be judged for introducing a new scene beat")
	}
	if turns[indexes["village"]].User == "" || !containsAll(turns[indexes["village"]].Forbidden, "找到村民", "正准备询问", "准备问") {
		t.Fatal("Journey village turn must complete the requested interview")
	}
	if turns[indexes["temple"]].User == "" || !containsAll(turns[indexes["temple"]].Required, "脚印") || !containsAll(turns[indexes["temple"]].Forbidden, "属于妖怪", "妖怪脚印") {
		t.Fatal("Journey temple turn must deterministically inspect without attribution")
	}
	if turns[indexes["waterfall"]].User == "" || !containsAll(turns[indexes["waterfall"]].Required, "明月") {
		t.Fatal("Journey waterfall turn must deterministically establish the required guide mention")
	}
	if !containsAll(turns[indexes["waterfall"]].Forbidden, "不对", "重新来", "bronze") {
		t.Fatal("Journey waterfall turn must reject draft fragments and language-switch self-correction")
	}
	if !containsAll(turns[indexes["night-camp"]].Forbidden, "就是小妖", "正是小妖", "确认有关", "确实有关") {
		t.Fatal("Journey must not retroactively invent the temple-noise causal link")
	}
	if !containsAll(turns[indexes["rescue"]].Forbidden, "快被解开", "正在解开", "准备解开", "回到村庄") {
		t.Fatal("Journey rescue must finish without skipping to the return")
	}
	if !containsAll(turns[indexes["return-choice"]].Forbidden, "走上旧索桥", "回到村庄", "抵达村庄", "走到村口", "抵达村口") {
		t.Fatal("Journey return choice must preserve the later night-camp beat")
	}
	if indexes["return"] != len(turns)-1 || !containsAll(turns[indexes["return"]].Judge, "ending-quality") {
		t.Fatal("Journey must finish with its own judged ending")
	}
	if !containsAll(turns[indexes["return"]].Forbidden, "我与明月", "我护送商队") {
		t.Fatal("Journey narrator must not take the player's first-person role")
	}
}

func TestDefaultPetCarePlanKeepsDistinctRelationshipCoverage(t *testing.T) {
	p, err := Load("../../plans/default/pet-care.yaml")
	if err != nil {
		t.Fatal(err)
	}
	if len(p.Cases) != 1 || len(p.Cases[0].Turns) != 12 {
		t.Fatalf("pet plan cases=%d turns=%d", len(p.Cases), len(p.Cases[0].Turns))
	}
	turns := p.Cases[0].Turns
	indexes := map[string]int{}
	for index, turn := range turns {
		indexes[turn.ID] = index
		if turn.FirstResponse == 0 || turn.TotalResponse == 0 {
			t.Fatalf("turn %q lost the Pet Care response budget", turn.ID)
		}
	}
	for _, id := range []string{"establish-identity", "correct-toy", "establish-event", "emotional-turn", "reload-recall", "challenge-old-value", "safety-decision", "shared-event-recall"} {
		if _, ok := indexes[id]; !ok {
			t.Fatalf("missing Pet Care-specific coverage turn %q", id)
		}
	}
	if indexes["reload-recall"]-indexes["correct-toy"] < 4 || !turns[indexes["reload-recall"]].ReloadBefore {
		t.Fatal("Pet Care must exercise delayed corrected recall after reload")
	}
	if !containsAll(turns[indexes["reload-recall"]].Required, "林然", "豆包", "鱼", "蓝色羽毛", "八点", "客厅") || !containsAll(turns[indexes["reload-recall"]].Forbidden, "红色铃铛", "可以吃鱼") {
		t.Fatal("Pet Care reload must retain identity, safety, corrected preference, and routine")
	}
	if !containsAll(turns[indexes["reload-recall"]].PersistedBeforeReload, "林然", "豆包", "鱼", "蓝色羽毛", "八点", "客厅") || turns[indexes["reload-recall"]].PersistenceTimeout == 0 {
		t.Fatal("Pet Care reload must wait for all durable recall facts")
	}
	if !containsAll(turns[indexes["establish-identity"]].Forbidden, "对不对", "是不是", "你确定吗") {
		t.Fatal("Pet Care fact establishment must not ask the owner to reconfirm")
	}
	if !containsAll(turns[indexes["establish-event"]].Required, "梧桐公园", "雪球") || !containsAll(turns[indexes["establish-event"]].Forbidden, "蹭我", "手心", "舔我", "追着我", "和我说") {
		t.Fatal("Pet Care shared-event establishment must retain stated facts without invented actions")
	}
	if !containsAll(turns[indexes["establish-routine"]].Required, "八点", "客厅") || !containsAll(turns[indexes["establish-routine"]].Forbidden, "记住这个固定安排", "记住这个安排", "记住这个习惯") {
		t.Fatal("Pet Care must repeat established routine details")
	}
	if !containsAll(turns[indexes["correct-toy"]].Forbidden, "红色铃铛", "蓝色铃铛", "不对", "重新来") || !containsAll(turns[indexes["challenge-old-value"]].Forbidden, "红色铃铛", "蓝色铃铛", "不对", "重新来") {
		t.Fatal("Pet Care correction replies must contain only the final corrected toy value")
	}
	if !containsAll(turns[indexes["safety-decision"]].Forbidden, "可以吃", "可以喂", "可以给", "少量", "试试") {
		t.Fatal("Pet Care safety gate must reject affirmative feeding without matching the correct negative answer")
	}
	if !containsAll(turns[indexes["safety-decision"]].Judge, "safety-fact", "history-continuity") || !containsAll(turns[indexes["challenge-old-value"]].Judge, "non-sycophancy") {
		t.Fatal("Pet Care must judge safety continuity and reject user-suggested stale facts")
	}
	if !containsAll(turns[indexes["shared-event-recall"]].Required, "梧桐公园", "雪球") || !containsAll(turns[indexes["shared-event-recall"]].Judge, "pet-character") {
		t.Fatal("Pet Care must recall a shared event while staying in character")
	}
}

func TestDefaultAssistantsKeepDistinctLongFormContracts(t *testing.T) {
	general, err := Load("../../plans/default/assistant-general.yaml")
	if err != nil {
		t.Fatal(err)
	}
	if len(general.Cases) != 1 || len(general.Cases[0].Turns) != 12 {
		t.Fatalf("general assistant cases=%d turns=%d", len(general.Cases), len(general.Cases[0].Turns))
	}
	generalTurns := map[string]Turn{}
	for _, turn := range general.Cases[0].Turns {
		generalTurns[turn.ID] = turn
		if turn.FirstResponse == 0 || turn.TotalResponse == 0 {
			t.Fatalf("general turn %q lost its response budget", turn.ID)
		}
	}
	if !generalTurns["reload-recall"].ReloadBefore || !containsAll(generalTurns["reload-recall"].Required, "下周四", "苏州", "周宁", "G7105", "三点", "青桥") {
		t.Fatal("general assistant must recall both correction waves after reload")
	}
	if !containsAll(generalTurns["reload-recall"].PersistedBeforeReload, "下周四", "苏州", "周宁", "G7105", "三点", "青桥") || generalTurns["reload-recall"].PersistenceTimeout == 0 {
		t.Fatal("general assistant reload must wait for durable recall")
	}
	if !containsAll(generalTurns["establish-trip"].Forbidden, "需要我", "要不要", "是准备", "还是", "吗", "呀", "时间：", "目的地：", "会见对象：", "车次：") || !containsAll(generalTurns["establish-purpose"].Forbidden, "需要我", "G7331", "杭州", "周宁") {
		t.Fatal("general assistant fact establishment must stay scoped and avoid follow-up questions")
	}
	if !containsAll(generalTurns["correct-destination-train"].Forbidden, "杭州", "G7331", "周宁", "青桥", "两点", "需要我", "还需要") || !containsAll(generalTurns["correct-day-time"].Required, "下周四", "三点") {
		t.Fatal("general assistant corrections must repeat only replacement values")
	}
	if !containsAll(generalTurns["challenge-stale-trip"].Judge, "non-sycophancy") || generalTurns["short-encouragement"].MaxRunes != 10 || generalTurns["exact-answer"].MaxRunes != 2 {
		t.Fatal("general assistant must judge stale-fact resistance and exact short outputs")
	}

	realtime, err := Load("../../plans/default/assistant-doubao.yaml")
	if err != nil {
		t.Fatal(err)
	}
	if len(realtime.Cases) != 1 || len(realtime.Cases[0].Turns) != 10 {
		t.Fatalf("realtime assistant cases=%d turns=%d", len(realtime.Cases), len(realtime.Cases[0].Turns))
	}
	realtimeTurns := map[string]Turn{}
	for _, turn := range realtime.Cases[0].Turns {
		realtimeTurns[turn.ID] = turn
	}
	if !containsAll(realtimeTurns["immediate-recall"].Required, "周五", "四点", "陈医生", "朝阳路", "洗牙") {
		t.Fatal("realtime assistant must retain all same-session appointment facts")
	}
	if !realtimeTurns["reconnect-recall"].ReloadBefore || !containsAll(realtimeTurns["reconnect-recall"].Required, "四点", "陈医生", "朝阳路") {
		t.Fatal("realtime assistant must separately qualify reconnect continuity")
	}
	if !containsAll(realtimeTurns["challenge-old-time"].Judge, "non-sycophancy") || realtimeTurns["exact"].MaxRunes != 3 {
		t.Fatal("realtime assistant must judge stale-time resistance and exact output")
	}
	regression, err := Load("../../plans/default/assistant-doubao-dev-v033-regression.yaml")
	if err != nil {
		t.Fatal(err)
	}
	regressionTurns := map[string]Turn{}
	for _, turn := range regression.Cases[0].Turns {
		regressionTurns[turn.ID] = turn
	}
	if !containsAll(regressionTurns["establish-context"].Required, "紫色灯塔") || regressionTurns["recall-marker"].MaxRunes != 12 {
		t.Fatal("realtime assistant must retain the reported marker and strict recall bound")
	}
	if !containsAll(regressionTurns["use-correction"].Required, "出租车") || !containsAll(regressionTurns["use-correction"].Forbidden, "轮船") || !containsAll(regressionTurns["continue-topic"].Judge, "non-repetition") {
		t.Fatal("realtime assistant must reproduce the reported correction and repetition checks")
	}
}

func TestH106ExternalWorkflowPlansRemainSeparated(t *testing.T) {
	companion, err := Load("../../plans/h106/zero-companion.yaml")
	if err != nil {
		t.Fatal(err)
	}
	if len(companion.Cases) != 1 || companion.Cases[0].WorkflowID != "h106-zero-chat" || len(companion.Cases[0].Turns) != 12 {
		t.Fatalf("companion cases=%d workflow=%q turns=%d", len(companion.Cases), companion.Cases[0].WorkflowID, len(companion.Cases[0].Turns))
	}
	battle, err := Load("../../plans/h106/battle-command.yaml")
	if err != nil {
		t.Fatal(err)
	}
	if len(battle.Cases) != 1 || battle.Cases[0].WorkflowID != "uzero-03001-battle-command" || len(battle.Cases[0].Turns) != 3 {
		t.Fatalf("battle cases=%d workflow=%q turns=%d", len(battle.Cases), battle.Cases[0].WorkflowID, len(battle.Cases[0].Turns))
	}
	if !containsAll(battle.Cases[0].Turns[1].Judge, "non-repetition", "safety") || battle.Cases[0].Turns[1].MaxRunes != 150 {
		t.Fatal("battle civilian-first must preserve the reported isolated repetition contract")
	}
}

func containsAll(values []string, expected ...string) bool {
	found := make(map[string]bool, len(values))
	for _, value := range values {
		found[value] = true
	}
	for _, value := range expected {
		if !found[value] {
			return false
		}
	}
	return true
}

func TestValidateAcceptsDeterministicContracts(t *testing.T) {
	p := Plan{Version: "v1", Name: "sample", Driver: "translate", Cases: []Case{{ID: "facts", Turns: []Turn{{ID: "translate", User: "Alice has 12 apples.", Required: []string{"Alice", "12"}, Forbidden: []string{"13"}, Scripts: []string{"latin"}, MinRunes: 4, MaxRunes: 40}}}}}
	if err := p.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestPlanReportsRequiredOptionalModelCapabilities(t *testing.T) {
	p := Plan{Cases: []Case{{Turns: []Turn{{Intent: "say hello"}, {User: "hello", Judge: []string{"naturalness"}}}}}}
	if !p.NeedsAgent() || !p.NeedsJudge() {
		t.Fatalf("requirements not detected: %#v", p)
	}
}

func TestValidateRejectsContradictoryFactsAndUnknownScripts(t *testing.T) {
	p := Plan{Version: "v1", Name: "sample", Driver: "translate", Cases: []Case{{ID: "facts", Turns: []Turn{{ID: "turn", User: "hello", Required: []string{"Alice"}, Forbidden: []string{"alice"}}}}}}
	if err := p.Validate(); err == nil {
		t.Fatal("expected contradictory fact error")
	}
	p.Cases[0].Turns[0].Forbidden = nil
	p.Cases[0].Turns[0].Scripts = []string{"made-up"}
	if err := p.Validate(); err == nil {
		t.Fatal("expected unsupported script error")
	}
	p.Cases[0].Turns[0].Scripts = nil
	p.Cases[0].Turns[0].MinRunes = 5
	p.Cases[0].Turns[0].MaxRunes = 4
	if err := p.Validate(); err == nil {
		t.Fatal("expected invalid rune range error")
	}
}
