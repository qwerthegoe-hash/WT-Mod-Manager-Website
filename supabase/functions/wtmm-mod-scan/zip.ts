/**
 * Server-side ZIP structure inspection. Never executes or extracts uploaded mods
 * to the filesystem. The scanned ZIP stays in private Supabase Storage.
 *
 * This catches unsafe entry paths, file types, symbolic links, encrypted ZIPs,
 * oversized/overlapping members, decompression bombs, malformed streams,
 * and CRC mismatches. It is NOT an antivirus scanner.
 */
export class ScanReject extends Error {
  constructor(message: string) { super(message); this.name = "ScanReject"; }
}
export const MAX_ZIP_BYTES = 20 * 1024 * 1024;
const MAX_EXPANDED = 80 * 1024 * 1024;
const MAX_MEMBERS = 250;
const MAX_SINGLE_FILE = 30 * 1024 * 1024;
const MAX_RATIO = 200;
const MAGIC_CEN = 0x02014b50;
const MAGIC_LOC = 0x04034b50;
const MAGIC_EOCD = 0x06054b50;
const ALLOWED = new Set([
  ".png",".jpg",".jpeg",".webp",".dds",".tga",".bmp",
  ".wav",".ogg",".mp3",".flac",
  ".blk",".cfg",".json",".xml",".txt"
]);

type Entry = {
  name: string; isDir: boolean; method: number;
  crc: number; packed: number; unpacked: number; start: number; end: number;
};

function guard(condition: unknown, why: string): asserts condition {
  if (!condition) throw new ScanReject(why);
}
const table = new Uint32Array(256);
for (let n=0; n<256; n++) {
  let c=n;
  for (let k=0; k<8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
  table[n] = c >>> 0;
}
function updateCrc(crc: number, chunk: Uint8Array): number {
  let c=crc;
  for (let i=0; i<chunk.length; i++) c=table[(c ^ chunk[i]) & 255] ^ (c >>> 8);
  return c>>>0;
}
function disallowedMagic(chunk: Uint8Array): boolean {
  return (chunk.length>=2 && chunk[0]===77 && chunk[1]===90) || // Windows PE
    (chunk.length>=4 && chunk[0]===127 && chunk[1]===69 &&
      chunk[2]===76 && chunk[3]===70) || // ELF
    (chunk.length>=2 && chunk[0]===35 && chunk[1]===33) || // scripts
    (chunk.length>=4 && chunk[0]===80 && chunk[1]===75 &&
      chunk[2]===3 && chunk[3]===4); // nested archives
}
function checkName(raw: string, isDir: boolean) {
  const name=raw.normalize("NFC");
  guard(name.length>0 && name.length<=240 &&
    !name.startsWith("/") && !name.includes("\\") && !name.includes(":") &&
    !/[\u0000-\u001f\u007f]/u.test(name), "Недопустимый путь в ZIP");
  const parts=name.split("/");
  guard(parts.every((part,i) => (isDir && i===parts.length-1 && part==="") ||
    (part!=="" && part!=="." && part!=="..")), "Опасный относительный путь");
  if (!isDir) {
    const ext = name.slice(name.lastIndexOf(".")).toLowerCase();
    guard(ALLOWED.has(ext), "Недопустимый тип файла внутри ZIP");
  }
  return name;
}
function parseEntries(bytes: Uint8Array): Entry[] {
  guard(bytes.length>=22 && bytes.length<=MAX_ZIP_BYTES,"Некорректный размер ZIP");
  const data=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  const u16=(n:number)=>data.getUint16(n,true);
  const u32=(n:number)=>data.getUint32(n,true);
  const begin=Math.max(0,bytes.length-22-65535);
  let eocd=-1;
  for (let i=bytes.length-22;i>=begin;i--) {
    if (u32(i)===MAGIC_EOCD && i+22+u16(i+20)===bytes.length) {
      eocd=i; break;
    }
  }
  guard(eocd>=0,"Не найдена центральная директория ZIP");
  guard(u16(eocd+4)===0 && u16(eocd+6)===0,"Многотомные архивы запрещены");
  const count=u16(eocd+10);
  guard(count===u16(eocd+8) && count>0 && count<=MAX_MEMBERS,
    "Недопустимое число файлов ZIP");
  const size=u32(eocd+12), offset=u32(eocd+16);
  guard(size!==0xFFFFFFFF && offset!==0xFFFFFFFF &&
    offset+size===eocd,"Некорректная центральная директория");
  const entries:Entry[]=[];
  const seen=new Set<string>();
  const spans:Array<[number,number]>=[];
  const utf8=new TextDecoder("utf-8",{fatal:true});
  let at=offset,total=0,files=0;
  for (let idx=0;idx<count;idx++) {
    guard(at+46<=eocd && u32(at)===MAGIC_CEN,"Повреждённая запись ZIP");
    const flags=u16(at+8), method=u16(at+10);
    const crc=u32(at+16), packed=u32(at+20), unpacked=u32(at+24);
    const filenameLen=u16(at+28), extraLen=u16(at+30), commentLen=u16(at+32);
    const localOffset=u32(at+42);
    const attr=u32(at+38);
    const end=at+46+filenameLen+extraLen+commentLen;
    guard(filenameLen>0 && end<=eocd,"Повреждённое имя ZIP");
    guard((flags&1)===0 && (flags&0x40)===0,
      "Зашифрованные элементы не поддерживаются");
    guard(method===0 || method===8,"Неподдерживаемый тип сжатия");
    guard(packed!==0xFFFFFFFF && unpacked!==0xFFFFFFFF &&
      localOffset!==0xFFFFFFFF,"ZIP64 не поддерживается");
    guard(((attr>>>16)&0xF000)!==0xA000,"Символические ссылки запрещены");
    let name="";
    try { name=utf8.decode(bytes.subarray(at+46,at+46+filenameLen)); }
    catch { throw new ScanReject("Некорректное UTF-8 имя ZIP"); }
    const isDir=name.endsWith("/");
    checkName(name,isDir);
    const folded=name.normalize("NFC").toLowerCase();
    guard(!seen.has(folded),"Повторяющиеся имена в ZIP");
    seen.add(folded);
    guard(unpacked<=MAX_SINGLE_FILE && (packed!==0 || unpacked===0) &&
      (unpacked===0 || unpacked/packed<=MAX_RATIO),
      "Превышен лимит размера или распаковки");
    total+=unpacked;
    guard(total<=MAX_EXPANDED,"Слишком большой распакованный архив");
    if (isDir) guard(unpacked===0 && packed<=8,"Некорректная директория");
    else files++;
    guard(localOffset+30<=offset && u32(localOffset)===MAGIC_LOC,
      "Повреждённый локальный заголовок");
    guard(u16(localOffset+8)===method,"Разные методы сжатия в ZIP");
    const localNameLen=u16(localOffset+26), localExtra=u16(localOffset+28);
    const memberStart=localOffset+30+localNameLen+localExtra;
    const memberEnd=memberStart+packed;
    guard(memberStart<=memberEnd && memberEnd<=offset,
      "Файл выходит за границы ZIP");
    let localName="";
    try {
      localName=utf8.decode(bytes.subarray(localOffset+30,localOffset+30+localNameLen));
    } catch { throw new ScanReject("Некорректное имя в локальном заголовке"); }
    guard(localName===name,"Имя в заголовках ZIP не совпадает");
    spans.push([localOffset,memberEnd]);
    entries.push({name,isDir,method,crc,packed,unpacked,start:memberStart,end:memberEnd});
    at=end;
  }
  guard(at===eocd && files>0,"Центральная директория ZIP не совпадает");
  spans.sort((a,b)=>a[0]-b[0]);
  for(let i=1;i<spans.length;i++)
    guard(spans[i][0]>=spans[i-1][1],"Пересекающиеся файлы ZIP");
  return entries;
}
async function checkOne(bytes: Uint8Array, entry: Entry): Promise<void> {
  if (entry.isDir) return;
  let seen=0, crc=0xFFFFFFFF, prefix=new Uint8Array();
  const consume=(chunk:Uint8Array)=>{
    seen+=chunk.length;
    guard(seen<=entry.unpacked && seen<=MAX_SINGLE_FILE,
      "Файл больше заявленного размера");
    crc=updateCrc(crc,chunk);
    if (prefix.length<8) {
      const joined=new Uint8Array(Math.min(8,prefix.length+chunk.length));
      joined.set(prefix);
      joined.set(chunk.subarray(0,joined.length-prefix.length),prefix.length);
      prefix=joined;
    }
    guard(!disallowedMagic(prefix),"Обнаружено исполняемое содержимое");
  };
  if (entry.method===0) {
    const raw=bytes.subarray(entry.start,entry.end);
    guard(raw.length===entry.unpacked,"Неправильная длина файла");
    consume(raw);
  } else {
    try {
      const compressed=bytes.subarray(entry.start,entry.end);
      const stream=new Blob([new Uint8Array(compressed)]).stream()
        .pipeThrough(new DecompressionStream("deflate-raw"));
      const reader=stream.getReader();
      try {
        for(;;) {
          const {done,value}=await reader.read();
          if(done) break;
          consume(value);
        }
      } finally {reader.releaseLock();}
    } catch(e) {
      if (e instanceof ScanReject) throw e;
      throw new ScanReject("Ошибка распаковки ZIP");
    }
  }
  guard(seen===entry.unpacked,"Длина файла не совпадает с ZIP");
  guard(((crc^0xFFFFFFFF)>>>0)===entry.crc,"Ошибка CRC файла");
}
export async function inspectZip(bytes:Uint8Array) {
  const entries=parseEntries(bytes);
  for(const entry of entries) await checkOne(bytes,entry);
  const hash=await crypto.subtle.digest("SHA-256",new Uint8Array(bytes).buffer);
  const sha256=Array.from(new Uint8Array(hash),n=>n.toString(16).padStart(2,"0")).join("");
  return {sha256,files:entries.filter(x=>!x.isDir).length};
}
