// Explain *recorded* scanner state without fabricating an antivirus verdict.
export function reportForMod(row) {
  const state = String(row?.triage_status || "queued");
  const verified = state === "checked" || state === "review";
  const stage = state === "blocked" ? "blocked" :
    verified ? "checked" : "pending";
  const note = String(row?.triage_note || "").slice(0,180);
  const av = String(row?.scan_status || "pending");
  const scan = [
    {name: "Структура ZIP",status:stage,
      detail:verified?"Заголовки и допустимые пути проверены.":
      state==="blocked"?"Архив отклонён.": "Проверка ещё не завершена."},
    {name: "CRC и распаковка",status:stage,
      detail:verified?"Проверка CRC и ограничений завершена.":
      "Нет подтверждённого успешного результата."},
    {name: "Размер и содержимое",status:stage,
      detail:verified?"Файлов проверено: "+(Number.isInteger(row?.triage_files)?row.triage_files:"неизвестно"):
      "Результат не установлен."},
    {name: "ClamAV",status:av==="blocked"?"blocked":av==="clean"?"checked":"pending",
      detail:av==="blocked"?"Обнаружение требует расследования.":
      av==="clean"?"Сканер сообщил об отсутствии обнаружений; это не гарантия.":
      "Сканирование может быть не настроено или не завершено."},
    {name: "VirusTotal",status:"unknown",
      detail:"Для этого ZIP не подтверждён автоматический отчёт VirusTotal."},
    {name: "Ручная модерация",
      status:row?.status==="approved"?"checked":
        row?.status==="rejected"?"blocked":"pending",
      detail:row?.status==="approved"?"Одобрено человеком.":
        row?.status==="rejected"?"Отклонено.":"Ожидает решения модератора."}
  ];
  if(note)scan.push({name:"Комментарий проверки",status:"info",detail:note});
  return scan;
}
