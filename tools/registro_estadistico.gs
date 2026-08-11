// Pegue este archivo en script.google.com, vinculado a una hoja de calculo.
// Despliegue como aplicacion web y copie su URL en Ajustes > Registro.
const HOJA_REGISTROS = "Registros";

function doPost(e) {
  const libro = SpreadsheetApp.getActiveSpreadsheet();
  const hoja = libro.getSheetByName(HOJA_REGISTROS) || libro.insertSheet(HOJA_REGISTROS);
  if (hoja.getLastRow() === 0) {
    hoja.appendRow(["Fecha UTC", "Nombre", "Pais", "Version", "Plataforma"]);
  }
  const datos = JSON.parse((e.postData && e.postData.contents) || "{}");
  hoja.appendRow([
    datos.fecha_utc || new Date().toISOString(),
    datos.nombre || "",
    datos.pais || "",
    datos.version || "",
    datos.plataforma || "",
  ]);
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  const libro = SpreadsheetApp.getActiveSpreadsheet();
  const hoja = libro.getSheetByName(HOJA_REGISTROS);
  const paises = {};
  let total = 0;
  if (hoja && hoja.getLastRow() > 1) {
    const filas = hoja.getRange(2, 1, hoja.getLastRow() - 1, 5).getValues();
    filas.forEach((fila) => {
      const pais = String(fila[2] || "").trim();
      if (!pais) return;
      total += 1;
      paises[pais] = (paises[pais] || 0) + 1;
    });
  }
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, total: total, paises: paises }))
    .setMimeType(ContentService.MimeType.JSON);
}
