import { inspectZip, ScanReject } from "./zip.ts";
import { assertEquals, assertRejects } from "jsr:@std/assert@1.0.15";

// Stored, tiny ZIP test fixture constructed without third-party archivers.
function sampleZip(filename:string, dataBytes:Uint8Array, badCrc=false, method=0, packed=dataBytes) {
  const text=new TextEncoder().encode(filename);
  const crcTable=new Uint32Array(256);
  for(let i=0;i<256;i++){
    let value=i;
    for(let j=0;j<8;j++)value=value&1 ? 0xEDB88320^(value>>>1):value>>>1;
    crcTable[i]=value>>>0;
  }
  let crc=0xFFFFFFFF;
  for(const b of dataBytes)crc=crcTable[(crc^b)&255]^(crc>>>8);
  crc=(crc^0xFFFFFFFF)>>>0;
  if(badCrc)crc^=1;
  const output:number[]=[];
  const word=(n:number)=>{output.push(n&255,(n>>>8)&255)};
  const dword=(n:number)=>{word(n&65535);word(n>>>16)};
  const local=output.length;
  dword(0x04034b50);word(20);word(0);word(method);word(0);word(0);
  dword(crc);dword(packed.length);dword(dataBytes.length);
  word(text.length);word(0);
  output.push(...text,...packed);
  const centralOffset=output.length;
  dword(0x02014b50);word(20);word(20);word(0);word(method);
  word(0);word(0);dword(crc);
  dword(packed.length);dword(dataBytes.length);
  word(text.length);word(0);word(0);word(0);word(0);
  dword(0);dword(local);
  output.push(...text);
  const centralLength=output.length-centralOffset;
  dword(0x06054b50);word(0);word(0);word(1);word(1);
  dword(centralLength);dword(centralOffset);word(0);
  return new Uint8Array(output);
}
Deno.test("accept valid text mod and compute SHA-256", async()=>{
  const zip=sampleZip("sounds/example.txt",new TextEncoder().encode("safe data"));
  const report=await inspectZip(zip);
  assertEquals(report.files,1);
  assertEquals(report.sha256.length,64);
  assertEquals(report.verdict,"checked");
  assertEquals(report.reviewReasons.length,0);
});
Deno.test("reject parent-directory traversal", async()=>{
  const zip=sampleZip("../outside.txt",new TextEncoder().encode("unsafe"));
  await assertRejects(()=>inspectZip(zip),ScanReject);
});
Deno.test("reject executable mod content type", async()=>{
  const zip=sampleZip("config/autorun.bat",new TextEncoder().encode("not allowed"));
  await assertRejects(()=>inspectZip(zip),ScanReject);
});
Deno.test("short MZ header is not enough to declare executable", async()=>{
  const zip=sampleZip("textures/fake.png",new Uint8Array([77,90,0,0,0]));
  const report=await inspectZip(zip);
  assertEquals(report.verdict,"review");
});
Deno.test("real Windows PE header concealed in PNG gets rejected", async()=>{
  const payload=new Uint8Array(160);
  payload[0]=77;payload[1]=90; // DOS MZ signature
  payload[0x3c]=0x80;         // e_lfanew -> full PE header
  payload[0x80]=80; payload[0x81]=69;
  payload[0x82]=0; payload[0x83]=0;
  const zip=sampleZip("textures/fake.png",payload);
  await assertRejects(()=>inspectZip(zip),ScanReject);
});
Deno.test("reject corrupted CRC", async()=>{
  const zip=sampleZip("textures/bitmap.png",new Uint8Array([137,80,78,71]),true);
  await assertRejects(()=>inspectZip(zip),ScanReject);
});
Deno.test("reject invalid central directory", async()=>{
  const zip=sampleZip("readme.txt",new TextEncoder().encode("ok"));
  zip[zip.length-22]=0;
  await assertRejects(()=>inspectZip(zip),ScanReject);
});

Deno.test("accept raw deflate-compressed ZIP member and verify CRC", async()=>{
  const payload=new TextEncoder().encode("hello world");
  // Deterministic DEFLATE-raw stream created with zlib (no ZIP wrapper).
  const deflated=Uint8Array.from("cb48cdc9c95728cf2fca490100".match(/../g)!,x=>parseInt(x,16));
  const report=await inspectZip(sampleZip("readme.txt",payload,false,8,deflated));
  assertEquals(report.files,1);
});
Deno.test("reject suspicious compression expansion before decompression", async()=>{
  const payload=new Uint8Array(10000);
  await assertRejects(
    ()=>inspectZip(sampleZip("readme.txt",payload,false,8,new Uint8Array([1]))),
    ScanReject
  );
});

Deno.test("allow typical harmless INI config", async()=>{
  const zip=sampleZip("settings/game.ini",new TextEncoder().encode("[game]\\nquality=high\\n"));
  const report=await inspectZip(zip);
  assertEquals(report.verdict,"checked");
});
Deno.test("unfamiliar but non-executable file is review, not virus", async()=>{
  const zip=sampleZip("materials/model.mtl",new TextEncoder().encode("newmtl mat"));
  const report=await inspectZip(zip);
  assertEquals(report.verdict,"review");
  assertEquals(report.reviewReasons.length,1);
});
Deno.test("ambiguous MZ text header does not trigger automatic rejection", async()=>{
  const zip=sampleZip("readme.txt",new TextEncoder().encode("MZ texture design note"));
  const report=await inspectZip(zip);
  assertEquals(report.verdict,"review");
});
Deno.test("shebang-prefixed text requires manual review, not automatic rejection", async()=>{
  const zip=sampleZip("readme.txt",new TextEncoder().encode("#! documentation example"));
  const report=await inspectZip(zip);
  assertEquals(report.verdict,"review");
});
Deno.test("executable file extension remains prohibited", async()=>{
  const zip=sampleZip("install/setup.exe",new Uint8Array([77,90,0,0]));
  await assertRejects(()=>inspectZip(zip),ScanReject);
});
Deno.test("unknown extension with broken CRC cannot pass via review", async()=>{
  const zip=sampleZip("model.custom",new Uint8Array([1,2,3]),true);
  await assertRejects(()=>inspectZip(zip),ScanReject);
});
