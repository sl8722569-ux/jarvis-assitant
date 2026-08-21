(function () {
  const log = document.getElementById("log");
  const q = document.getElementById("q");
  const status = document.getElementById("status");
  const installBtn = document.getElementById("install");
  let active = false;

  function line(who, text, cls) {
    const p = document.createElement("p");
    p.innerHTML = "<strong class=\"" + cls + "\">" + who + "</strong><br>" + text;
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
  }

  function reply(text) {
    const t = (text || "").trim();
    const low = t.toLowerCase();
    if (!t) return "I did not catch that.";
    if (low.indexOf("jarvis activate") >= 0 || low === "activate") {
      active = true;
      status.textContent = "ONLINE · INSAN CREATIONS";
      return "Yes sir, I am online. How may I assist you? Full desktop voice/files still live in the Windows app. This is the J.A.R.V.I.S app on every device.";
    }
    if (low.indexOf("standby") >= 0 || low === "goodbye") {
      active = false;
      status.textContent = "STANDBY · INSAN CREATIONS";
      return "Standing by.";
    }
    if (low.indexOf("open chatgpt") >= 0) { window.open("https://chatgpt.com/", "_blank"); return "Opening ChatGPT."; }
    if (low.indexOf("open youtube") >= 0) { window.open("https://www.youtube.com", "_blank"); return "Opening YouTube."; }
    if (low.indexOf("time") >= 0) return "Local time: " + new Date().toLocaleString();
    if (low.indexOf("help") >= 0 || low.indexOf("what can") >= 0) {
      return "Say Jarvis Activate, open ChatGPT, open YouTube, time, or ask a question. Windows JARVIS.exe has mic, files, and system tools.";
    }
    return "I heard: “" + t + "”. This device app can chat and open sites. For microphone, files, and PC control, install the Windows package from INSAN CREATIONS.";
  }

  line("JARVIS", "Device app ready. Say Jarvis Activate, or tap Install app to pin me to your home screen / desktop.", "j");

  document.getElementById("bar").onsubmit = function (e) {
    e.preventDefault();
    const t = q.value.trim();
    if (!t) return;
    line("You", t, "u");
    q.value = "";
    line("JARVIS", reply(t), "j");
  };

  document.querySelectorAll(".modes button").forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll(".modes button").forEach((x) => x.classList.remove("on"));
      b.classList.add("on");
      document.body.className = b.dataset.mode === "sidebar" ? "sidebar" : "";
    };
  });

  let deferred;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferred = e;
    installBtn.hidden = false;
  });
  installBtn.onclick = () => { if (deferred) deferred.prompt(); };

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
})();
