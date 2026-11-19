import { inspectZip, ScanReject } from "./zip.ts";
import { assertEquals, assertRejects } from "jsr:@std/assert@1.0.15";

// Stored, tiny ZIP test fixture constructed without third-party archivers.
function sampleZip(filename:string, dataBytes:Uint8Array, badCrc=false) {
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
  dword(0x04034b50);word(20);word(0);word(0);word(0);word(0);
  dword(crc);dword(dataBytes.length);dword(dataBytes.length);
  word(text.length);word(0);
  output.push(...text,...dataBytes);
  const centralOffset=output.length;
  dword(0x02014b50);word(20);word(20);word(0);word(0);
  word(0);word(0);dword(crc);
  dword(dataBytes.length);dword(dataBytes.length);
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
});
Deno.test("reject parent-directory traversal", async()=>{
  const zip=sampleZip("../outside.txt",new TextEncoder().encode("unsafe"));
  await assertRejects(()=>inspectZip(zip),ScanReject);
});
Deno.test("reject executable mod content type", async()=>{
  const zip=sampleZip("config/autorun.bat",new TextEncoder().encode("not allowed"));
  await assertRejects(()=>inspectZip(zip),ScanReject);
});
Deno.test("reject disguised Windows executable magic", async()=>{
  const zip=sampleZip("textures/fake.png",new Uint8Array([77,90,0,0,0]));
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
