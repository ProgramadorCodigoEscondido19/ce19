// Pegue este archivo en script.google.com y desplieguelo como aplicacion web.
// El proyecto crea y conserva su propia hoja de calculo automaticamente.
const HOJA_REGISTROS = "Registros";
const PROPIEDAD_HOJA = "ce19_hoja_registros";

function obtenerHoja_() {
  const propiedades = PropertiesService.getScriptProperties();
  let libro = null;
  const id = propiedades.getProperty(PROPIEDAD_HOJA);

  if (id) {
    try {
      libro = SpreadsheetApp.openById(id);
    } catch (error) {
      libro = null;
    }
  }

  if (!libro) {
    libro = SpreadsheetApp.create("CODIGO ESCONDIDO 19 - Registros");
    propiedades.setProperty(PROPIEDAD_HOJA, libro.getId());
  }

  let hoja = libro.getSheetByName(HOJA_REGISTROS);
  if (!hoja) {
    hoja = libro.insertSheet(HOJA_REGISTROS);
    hoja.appendRow(["Fecha UTC", "Nombre", "Pais", "Version", "Plataforma"]);
    hoja.setFrozenRows(1);
  }
  return hoja;
}

function salida_(datos) {
  return ContentService
    .createTextOutput(JSON.stringify(datos))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const datos = JSON.parse((e.postData && e.postData.contents) || "{}");
    const hoja = obtenerHoja_();
    hoja.appendRow([
      datos.fecha_utc || new Date().toISOString(),
      String(datos.nombre || "").trim(),
      String(datos.pais || "").trim(),
      String(datos.version || ""),
      String(datos.plataforma || ""),
    ]);
    return salida_({ ok: true });
  } catch (error) {
    return salida_({ ok: false, error: String(error) });
  }
}

function doGet() {
  try {
    const hoja = obtenerHoja_();
    const paises = {};
    const filas = hoja.getLastRow() > 1
      ? hoja.getRange(2, 1, hoja.getLastRow() - 1, 5).getValues()
      : [];

    filas.forEach((fila) => {
      const pais = String(fila[2] || "").trim();
      if (pais) {
        paises[pais] = (paises[pais] || 0) + 1;
      }
    });
    return salida_({ ok: true, total: filas.length, paises: paises });
  } catch (error) {
    return salida_({ ok: false, total: 0, paises: {}, error: String(error) });
  }
}
