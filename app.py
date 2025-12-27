from flask import Flask, request, render_template_string, jsonify
from datetime import datetime

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>alextest</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; }
    button { padding: 10px 14px; font-size: 16px; cursor: pointer; }
    .box { padding: 12px; border: 1px solid #ddd; border-radius: 10px; margin-top: 16px; }
    code { background:#f6f6f6; padding:2px 6px; border-radius:6px; }
  </style>
</head>
<body>
  <h1>alextest</h1>

  <p>
    Cette page peut récupérer ta localisation <b>uniquement si tu acceptes</b>.
    Clique sur le bouton ci-dessous pour partager ta position.
  </p>

  <button id="btn">Partager ma localisation</button>

  <div class="box" id="out" style="display:none;"></div>

<script>
const out = document.getElementById("out");
const btn = document.getElementById("btn");

function show(msg) {
  out.style.display = "block";
  out.innerHTML = msg;
}

btn.onclick = () => {
  if (!navigator.geolocation) {
    show("Ton navigateur ne supporte pas la géolocalisation.");
    return;
  }

  navigator.geolocation.getCurrentPosition(async (pos) => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const acc = pos.coords.accuracy;

    // Reverse geocoding via Nominatim (OpenStreetMap)
    const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`;
    let city = "Inconnue";
    let display = "";

    try {
      const r = await fetch(url, { headers: { "Accept": "application/json" } });
      const j = await r.json();
      display = j.display_name || "";
      const a = j.address || {};
      city = a.city || a.town || a.village || a.municipality || a.county || "Inconnue";
    } catch(e) {}

    show(
      `<b>Position reçue</b><br>` +
      `Ville (approx.) : <b>${city}</b><br>` +
      `Adresse (approx.) : ${display ? display : "<i>non dispo</i>"}<br>` +
      `Lat/Lon : <code>${lat.toFixed(6)}, ${lon.toFixed(6)}</code><br>` +
      `Précision : ~<code>${Math.round(acc)} m</code>`
    );

    // Envoi au serveur (consentement implicite car clic + autorisation navigateur)
    await fetch("/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat, lon, acc, city, display })
    });

  }, (err) => {
    show("Refus ou erreur : " + err.message);
  }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
};
</script>
</body>
</html>
"""

@app.get("/")
def home():
    return "OK — va sur /alextest"

@app.get("/alextest")
def alextest():
    return "<h1>AlexTest</h1>"

@app.post("/report")
def report():
    data = request.get_json(force=True) or {}
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)  # utile derrière un proxy Render
    ts = datetime.utcnow().isoformat()

    # Log console (Render affichera ça dans les logs)
    print(f"{ts} | IP={ip} | city={data.get('city')} | lat={data.get('lat')} | lon={data.get('lon')} | acc={data.get('acc')}")

    return jsonify({"ok": True})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
