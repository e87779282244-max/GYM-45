// Копирует приложение (index.html, media, manifest) в native/www — это то, что попадёт внутрь iPhone-приложения.
import {cpSync, rmSync, mkdirSync} from "node:fs";
rmSync("www", {recursive: true, force: true});
mkdirSync("www");
for (const f of ["index.html", "manifest.json", "media"]) cpSync("../" + f, "www/" + f, {recursive: true});
console.log("www готов");
