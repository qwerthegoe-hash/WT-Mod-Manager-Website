import assert from "node:assert/strict";
import { modReviewReady } from "../docs/js/mod-review-policy.mjs";

assert.equal(modReviewReady(false, false), false);
assert.equal(modReviewReady(true, false), false);
assert.equal(modReviewReady(false, true), false);
assert.equal(modReviewReady(true, true), true);
assert.equal(modReviewReady(1, true), false);
assert.equal(modReviewReady(true, "yes"), false);
console.log("PASS: archive approval requires successful ZIP preflight and human review");
