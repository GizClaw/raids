// Execute actual controller sources. Fixtures express equivalent state/history for each engine.
const fs = require('fs');
const assert = require('assert/strict');
const vm = require('vm');
const cp = require('child_process');
const suites = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const {raid, data, sources} of suites) {
  const cfg = data.flowcraft;
  const results = new Map();
  const starCases = [];
  for (const c of data.cases) {
    try {
      assert.equal(typeof c.id, 'string');
      assert(!results.has(c.id), 'duplicate case ID');
      assert.equal(typeof c.input, 'string');
      assert.equal(typeof c.expect.speaker, 'string');
      let state = c.state || {};
      if (c.state_from) {
        assert(results.has(c.state_from), 'state_from must reference an earlier case');
        state = results.get(c.state_from)[cfg.state_var || 'story_state'];
      }
      const vars = structuredClone({input: c.input, [cfg.state_var || 'story_state']: state,
        [cfg.memory_var || 'scenario_memory']: c.memory || '', ...(c.vars || {})});
      const context = {board: {getVar: k => vars[k], setVar: (k, v) => {vars[k] = v;}}};
      vm.runInNewContext(sources.flowcraft, context, {timeout: 1000, filename: `${raid}/${cfg.node || 'control-story'}`});
      // Normalize VM values before strict comparisons across realms.
      const result = JSON.parse(JSON.stringify(vars));
      assert.equal(result[cfg.speaker_var || 'selected_speaker'], c.expect.speaker);
      for (const [path, checks] of Object.entries(c.expect.flowcraft || {})) {
        const actual = path.split('.').reduce((v, k) => v?.[k], result);
        for (const [op, expected] of Object.entries(checks)) {
          if (op === 'equals') assert.deepEqual(actual, expected, path);
          else if (op === 'includes') assert(actual.includes(expected), path);
          else if (op === 'not_includes') assert(!actual.includes(expected), path);
          else assert.fail(`unknown assertion ${op}`);
        }
      }
      results.set(c.id, result);
      starCases.push({ID: `${raid}/${c.id}`, Input: {text: c.input, history: c.history || [], memory: c.memory || '', ...(c.eino_input || {})}, Speaker: c.expect.speaker});
    } catch (error) { throw new Error(`${raid}/${c.id}: ${error.message}`, {cause: error}); }
  }
  cp.execFileSync('sh', ['scripts/test/test-starlark-routing.sh'], {
    input: JSON.stringify({Source: sources.eino, Cases: starCases}), stdio: ['pipe', 'inherit', 'inherit']});
  console.log(`validated ${raid} routing: ${data.cases.length} shared Flowcraft/Eino cases`);
}
