# app.py
# A simple, consent-based location sharing website.
# No classes, no "oop" ideas — just functions and plain variables.
#
# How it works:
#  1. You run this file. It starts a small website on your computer.
#  2. You send people the link (or the QR code made by generate_qr.py).
#  3. They open it, see a CLEAR message, and must tap "Share my location".
#     Their phone shows them the normal permission popup too.
#  4. If they agree, their location is sent here and saved.
#  5. You open /owner on your own phone/computer to see the latest spot.
#
# Install first:
#   pip install flask --break-system-packages
# Run it:
#   python app.py
# Then open the link it prints (works best if your phone and computer
# are on the same wifi, or if you host this on a real server).

from flask import Flask, request, jsonify
import os


app = Flask(__name__)

# A simple variable (a dictionary) that holds the latest shared location.
# No database needed for this simple version — it just lives in memory
# while the program is running.
latest_location = {
    "lat": None,
    "lng": None,
    "updated_at": None,
    "sharing": False
}


# ---------- Page the PERSON YOU SEND THE LINK TO sees ----------
@app.route("/")
def share_page():
    return """
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Location request</title>
      <style>
        body { font-family: sans-serif; padding: 24px; max-width: 420px; margin: auto; }
        button { padding: 14px; font-size: 16px; width: 100%; margin-top: 16px;
                 border: none; border-radius: 10px; }
        #share { background: #2563eb; color: white; }
        #stop { background: #dc2626; color: white; display: none; }
        #banner { display: none; background: #fee2e2; color: #dc2626;
                  padding: 10px; border-radius: 8px; font-weight: bold;
                  text-align: center; margin-bottom: 10px; }
        #status { color: #666; font-size: 14px; }
      </style>
    </head>
    <body>
      <div id="banner">Your live location is being shared</div>
      <h2>Location request</h2>
      <p>Someone has asked you to share your <b>live location</b> with them.
         Nothing is sent until you tap the button below, and your phone will
         also ask you to confirm. You can stop at any time.</p>

      <button id="share" onclick="startSharing()">Share my location</button>
      <button id="stop" onclick="stopSharing()">Stop sharing</button>
      <p id="status"></p>

      <script>
        var watchId = null;

        function startSharing() {
          // Ask the browser (and so, the phone) for permission.
          // This is the actual "notification" / popup the person sees.
          watchId = navigator.geolocation.watchPosition(sendLocation, showError,
            { enableHighAccuracy: true });

          document.getElementById("share").style.display = "none";
          document.getElementById("stop").style.display = "block";
          document.getElementById("banner").style.display = "block";
        }

        function sendLocation(position) {
          var lat = position.coords.latitude;
          var lng = position.coords.longitude;

          fetch("/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lat: lat, lng: lng })
          });

          document.getElementById("status").innerText =
            "Last sent at " + new Date().toLocaleTimeString();
        }

        function stopSharing() {
          if (watchId !== null) {
            navigator.geolocation.clearWatch(watchId);
          }
          fetch("/stop", { method: "POST" });
          document.getElementById("banner").style.display = "none";
          document.getElementById("stop").style.display = "none";
          document.getElementById("status").innerText = "Stopped sharing.";
        }

        function showError(err) {
          document.getElementById("status").innerText =
            "Could not get location: " + err.message;
        }
      </script>
    </body>
    </html>
    """


# ---------- The phone sends its location here ----------
@app.route("/update", methods=["POST"])
def update_location():
    data = request.get_json()

    latest_location["lat"] = data.get("lat")
    latest_location["lng"] = data.get("lng")
    latest_location["sharing"] = True

    import datetime
    latest_location["updated_at"] = datetime.datetime.now().strftime("%H:%M:%S")

    return jsonify({"ok": True})


# ---------- Called when the person taps "Stop sharing" ----------
@app.route("/stop", methods=["POST"])
def stop_sharing():
    latest_location["sharing"] = False
    return jsonify({"ok": True})


# ---------- Page only YOU should open, to see the location ----------
@app.route("/owner")
def owner_page():
    if latest_location["lat"] is None:
        return "<h2>No one has shared their location yet.</h2>"

    maps_link = "https://www.google.com/maps?q=" + str(latest_location["lat"]) + "," + str(latest_location["lng"])
    status_text = "sharing now" if latest_location["sharing"] else "stopped"

    return f"""
    <html><body style="font-family:sans-serif; padding:20px;">
      <h2>Latest location ({status_text})</h2>
      <p>Updated at: {latest_location["updated_at"]}</p>
      <p>Latitude: {latest_location["lat"]}</p>
      <p>Longitude: {latest_location["lng"]}</p>
      <a href="{maps_link}" target="_blank">Open in Google Maps</a>
      <p><a href="/owner">Refresh</a></p>
    </body></html>
    """


# ---------- Start the website ----------
if __name__ == "__main__":
    print("Share this link with the other person: http://<your-ip>:5000/")
    print("Open this link yourself to see their location: http://<your-ip>:5000/owner")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    

# generate_qr.py
# Simple script: turns a link into a QR code image.
# Install first:  pip install qrcode[pil] --break-system-packages

import qrcode

def make_qr_code(link_text, output_file):
    # This one function does everything: build the QR code and save it
    qr_image = qrcode.make(link_text)
    qr_image.save(output_file)
    print("Saved QR code to:", output_file)
    print("It points to:", link_text)

# ---- Change this line to your real link once your server is running ----
share_link = "http://your-server-address:5000/"

make_qr_code(share_link, "share_qr.png")