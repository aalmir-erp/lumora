let raw = "";
process.stdin.on("data", c => raw += c);
process.stdin.on("end", () => {
  const samples = JSON.parse(raw);
  const out = samples.map(text => {
    let pickerKind = null;
    const cleanText = text.replace(/\[\[\s*picker\s*:\s*(date|time)\s*\]\]/gi, (_, kind) => {
      pickerKind = kind.toLowerCase(); return "";
    });
    return { picker: pickerKind, clean: cleanText.trim() };
  });
  process.stdout.write(JSON.stringify(out));
});
