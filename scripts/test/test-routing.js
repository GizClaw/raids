// Execute the shipped controller in the real Starlark interpreter.
const fs = require('fs');
const assert = require('assert/strict');
const cp = require('child_process');
const suites = JSON.parse(fs.readFileSync(0, 'utf8'));
assert(suites.length > 0, 'no native routing suites');
for (const {raid, data, sources} of suites) {
  assert(sources.eino, `${raid}: no native controller source`);
  const ids = new Set();
  const cases = data.cases.map(c => {
    assert.equal(typeof c.id, 'string');
    assert(!ids.has(c.id), `${raid}: duplicate case ID`);
    ids.add(c.id);
    assert.equal(typeof c.input, 'string');
    if (c.expect.speaker !== undefined) assert.equal(typeof c.expect.speaker, 'string');
    return {ID: `${raid}/${c.id}`, Input: {text: c.input, history: c.history || [], memory: c.memory || '', ...(c.eino_input || {})}, Speaker: c.expect.speaker, Expect: c.expect.eino || {}};
  });
  cp.execFileSync('sh', ['scripts/test/test-starlark-routing.sh'], {
    input: JSON.stringify({Source: sources.eino, Cases: cases}), stdio: ['pipe', 'inherit', 'inherit']});
  console.log(`validated ${raid} native routing: ${cases.length} cases`);
}
