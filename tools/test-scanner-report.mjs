import {strict as assert} from "node:assert";
import {reportForMod} from "../docs/js/scan-report.mjs";

const pending=reportForMod({triage_status:"queued",scan_status:"pending",status:"pending"});
assert.equal(pending.length,6);
assert.equal(pending.find(x=>x.name==="ClamAV").status,"pending");
assert.equal(pending.find(x=>x.name==="VirusTotal").status,"unknown");

const checked=reportForMod({
  triage_status:"checked",triage_files:7,scan_status:"clean",status:"approved"
});
assert.equal(checked.find(x=>x.name==="CRC и распаковка").status,"checked");
assert.match(checked.find(x=>x.name==="Размер и содержимое").detail,/7/);
assert.match(checked.find(x=>x.name==="ClamAV").detail,/не гарантия/);
assert.equal(checked.find(x=>x.name==="Ручная модерация").status,"checked");

const blocked=reportForMod({
  triage_status:"review",scan_status:"blocked",status:"pending",
  triage_note:"Неоднозначная сигнатура файла"
});
assert.equal(blocked.find(x=>x.name==="ClamAV").status,"blocked");
assert.equal(blocked.find(x=>x.name==="VirusTotal").status,"unknown");
assert.equal(blocked.find(x=>x.name==="Комментарий проверки").status,"info");
console.log("WT Scanner Reports 2.0: non-invented evidence regression passed");
