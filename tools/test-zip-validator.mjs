// Offline ZIP validation regression tests. No network or dependencies.
import assert from "node:assert/strict";
import { validateModZip } from "../docs/js/mod-zip-validator.mjs";

function zipFixture(name, opts = {}) {
  const nameBytes = Buffer.from(name, "utf8");
  const payload = Buffer.from("safe mod content");
  const compressed = payload.length;
  const uncompressed = opts.uncompressed ?? compressed;
  const local = Buffer.alloc(30 + nameBytes.length + payload.length);
  local.writeUInt32LE(0x04034b50, 0);
  local.writeUInt16LE(20, 4);
  local.writeUInt32LE(compressed, 18);
  local.writeUInt32LE(uncompressed, 22);
  local.writeUInt16LE(nameBytes.length, 26);
  nameBytes.copy(local, 30);
  payload.copy(local, 30 + nameBytes.length);

  const directory = Buffer.alloc(46 + nameBytes.length);
  directory.writeUInt32LE(0x02014b50, 0);
  directory.writeUInt16LE(opts.symlink ? (3 << 8) | 20 : 20, 4);
  directory.writeUInt16LE(20, 6);
  directory.writeUInt16LE(opts.encrypted ? 1 : 0, 8);
  directory.writeUInt32LE(compressed, 20);
  directory.writeUInt32LE(uncompressed, 24);
  directory.writeUInt16LE(nameBytes.length, 28);
  if (opts.symlink) directory.writeUInt32LE((0xa1ff << 16) >>> 0, 38);
  nameBytes.copy(directory, 46);

  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(1, 8);
  end.writeUInt16LE(1, 10);
  end.writeUInt32LE(directory.length, 12);
  end.writeUInt32LE(local.length, 16);
  return new Blob([local, directory, end], { type: "application/zip" });
}
let cases = 0;
async function accepted(name) {
  const result = await validateModZip(zipFixture(name));
  assert.equal(result.files, 1);
  cases++;
}
async function rejected(name, opts) {
  await assert.rejects(() => validateModZip(zipFixture(name, opts)), Error);
  cases++;
}
await accepted("mod/texture.png");
await accepted("custom/camouflage/item.bin");
await rejected("../escape.txt");
await rejected("/absolute/path.txt");
await rejected("C:\\outside.txt");
await rejected("nested\\..\\private.bin");
await rejected("sym", { symlink: true });
await rejected("encrypted.txt", { encrypted: true });
await rejected("inflate.bin", { uncompressed: 50_000_000 });
await assert.rejects(() => validateModZip(new Blob([Buffer.from("not zip")]))); cases++;
console.log("PASS: ZIP regression tests (" + cases + " cases)");
