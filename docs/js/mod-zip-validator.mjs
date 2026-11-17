// WT Mod Manager - bounded client-side ZIP preflight for uploads.
// This is defense-in-depth and UX validation, never a replacement for server validation.
const MAX_FILES = 4096;
const MAX_DIRECTORY_BYTES = 2 * 1024 * 1024;
const MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024;
const MAX_COMPRESSION_RATIO = 200;

function read16(view, offset) { return view.getUint16(offset, true); }
function read32(view, offset) { return view.getUint32(offset, true); }
function unsafeEntryName(name) {
  const normalized = name.replaceAll("\\", "/");
  if (!normalized || normalized.startsWith("/") || /^[a-z]:/i.test(normalized) ||
      /[\u0000-\u001F]/.test(normalized) || normalized.includes(":")) return true;
  const segments = normalized.split("/");
  return segments.includes("..") || normalized.length > 1024;
}

export async function validateModZip(file) {
  if (!file || typeof file.slice !== "function" || file.size < 22) {
    throw new Error("Некорректный ZIP-архив.");
  }
  // Read only the tail and central directory, not full archive contents.
  const tailLength = Math.min(file.size, 65557);
  const tailStart = file.size - tailLength;
  const tail = new DataView(await file.slice(tailStart).arrayBuffer());
  let eocd = -1;
  for (let i = tail.byteLength - 22; i >= 0; i--) {
    if (read32(tail, i) === 0x06054b50 && i + 22 + read16(tail, i + 20) === tail.byteLength) {
      eocd = i;
      break;
    }
  }
  if (eocd < 0) throw new Error("ZIP не содержит корректную центральную директорию.");
  if (read16(tail, eocd + 4) !== 0 || read16(tail, eocd + 6) !== 0) {
    throw new Error("Многотомные ZIP-архивы не поддерживаются.");
  }
  const count = read16(tail, eocd + 10);
  const diskCount = read16(tail, eocd + 8);
  const directorySize = read32(tail, eocd + 12);
  const directoryOffset = read32(tail, eocd + 16);
  if (count !== diskCount || count === 0 || count === 0xffff ||
      directorySize === 0xffffffff || directoryOffset === 0xffffffff) {
    throw new Error("ZIP64, пустые и многотомные ZIP-архивы требуют отдельной проверки.");
  }
  if (count > MAX_FILES || directorySize > MAX_DIRECTORY_BYTES ||
      directoryOffset + directorySize > tailStart + eocd) {
    throw new Error("Слишком много файлов или некорректная структура ZIP.");
  }
  const central = new DataView(await file.slice(directoryOffset, directoryOffset + directorySize).arrayBuffer());
  const utf8 = new TextDecoder("utf-8");
  let offset = 0, expanded = 0;
  const names = new Set();
  for (let i = 0; i < count; i++) {
    if (offset + 46 > central.byteLength || read32(central, offset) !== 0x02014b50) {
      throw new Error("ZIP содержит повреждённую запись каталога.");
    }
    const flags = read16(central, offset + 8);
    const method = read16(central, offset + 10);
    const compressed = read32(central, offset + 20);
    const uncompressed = read32(central, offset + 24);
    const nameLength = read16(central, offset + 28);
    const extraLength = read16(central, offset + 30);
    const commentLength = read16(central, offset + 32);
    const externalAttributes = read32(central, offset + 38);
    const creator = read16(central, offset + 4) >> 8;
    const size = 46 + nameLength + extraLength + commentLength;
    if (offset + size > central.byteLength || nameLength === 0) {
      throw new Error("Некорректная запись в ZIP.");
    }
    const nameBytes = new Uint8Array(central.buffer, central.byteOffset + offset + 46, nameLength);
    const filename = utf8.decode(nameBytes);
    if (unsafeEntryName(filename)) throw new Error("Архив содержит небезопасный путь файла.");
    if (names.has(filename.toLowerCase())) throw new Error("ZIP содержит повторяющиеся имена файлов.");
    names.add(filename.toLowerCase());
    const unixMode = (externalAttributes >>> 16) & 0xffff;
    if (creator === 3 && (unixMode & 0xf000) === 0xa000) {
      throw new Error("Символические ссылки внутри ZIP не поддерживаются.");
    }
    if ((flags & 1) !== 0) throw new Error("ZIP с паролем нельзя проверить перед публикацией.");
    if (method !== 0 && method !== 8) throw new Error("Неподдерживаемый метод сжатия ZIP.");
    if (uncompressed > 0 && (compressed === 0 || uncompressed / compressed > MAX_COMPRESSION_RATIO)) {
      throw new Error("Подозрительно высокая степень сжатия ZIP.");
    }
    expanded += uncompressed;
    if (expanded > MAX_UNCOMPRESSED_BYTES) {
      throw new Error("После распаковки архив превышает безопасный размер.");
    }
    offset += size;
  }
  if (offset !== central.byteLength) throw new Error("ZIP содержит лишние данные в каталоге.");
  return { files: count, uncompressedBytes: expanded };
}
