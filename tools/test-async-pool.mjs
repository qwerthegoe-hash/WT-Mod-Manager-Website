import assert from "node:assert/strict";
import { mapWithConcurrency } from "../docs/js/async-pool.mjs";

let busy = 0;
let maxBusy = 0;
const input = Array.from({ length: 36 }, (_, i) => i);
const result = await mapWithConcurrency(input, 5, async (value) => {
  busy++;
  maxBusy = Math.max(maxBusy, busy);
  await Promise.resolve();
  busy--;
  return value * 2;
});
assert.deepEqual(result, input.map(x => x * 2));
assert.ok(maxBusy <= 5 && maxBusy > 1);
assert.deepEqual(await mapWithConcurrency([], 3, async x => x), []);
await assert.rejects(() => mapWithConcurrency([1], 0, async x => x), RangeError);
console.log("PASS: bounded concurrent rendering keeps correct order");
