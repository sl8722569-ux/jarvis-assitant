(function () {
  const log = document.getElementById("log");
  const q = document.getElementById("q");
  const status = document.getElementById("status");
  const installBtn = document.getElementById("install");
  const langSel = document.getElementById("lang");
  let lastUser = "";
  let lastReply = "";
  let pending = null;
  let stopped = false;
  const SITES = {
    youtube: "https://www.youtube.com",
    gmail: "https://mail.google.com",
    github: "https://github.com",
    chatgpt: "https://chatgpt.com/",
    grok: "https://grok.x.ai/",
    google: "https://www.google.com"
  };

  function line(who, text, cls) {
    const p = document.createElement("p");
    p.innerHTML = "<strong class=\"" + cls + "\">" + who + "</strong><br>" + escapeHtml(text);
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  }

  function detectLang(t) {
    if (/[\u0A00-\u0A7F]/.test(t)) return "pa";
    if (/[\u0900-\u097F]/.test(t)) return "hi";
    return "en";
  }

  async function reply(text) {
    const t = (text || "").trim();
    const low = t.toLowerCase();
    if (!t) return "I did not catch that.";
    if (pending) {
      if (/\b(yes|ok|haan|हां|ਹਾਂ|website|web)\b/i.test(low)) {
        const url = pending;
        pending = null;
        window.open(url, "_blank");
        return "Opening the official website.";
      }
      pending = null;
      return "Cancelled.";
    }
    if (/activate|online/.test(low)) {
      status.textContent = "ONLINE · type or speak";
      return "Yes sir. This is the web companion. I can chat and offer official websites. Installed Windows apps are opened by JARVIS.exe on the PC.";
    }
    if (/standby|goodbye/.test(low)) {
      status.textContent = "STANDBY · type or speak";
      return "Standing by.";
    }
    const openM = low.match(/\b(?:open|launch|kholo|खोलो|ਖੋਲ੍ਹੋ)\s+(.+)/) || low.match(/(.+)\s+(?:kholo|खोलो|ਖੋਲ੍ਹੋ)/);
    if (openM) {
      const name = (openM[1] || "").trim().replace(/[.!]+$/, "");
      const key = Object.keys(SITES).find(function (k) { return name.indexOf(k) >= 0; });
      if (key) {
        pending = SITES[key];
        return "This web app cannot launch a Windows program. Sir, should I open the official " + key + " website?";
      }
      return "I cannot launch installed desktop apps from the browser. Use JARVIS.exe on Windows for that.";
    }
    if (window.INSAN_BRIDGE) {
      try {
        const found = await window.INSAN_BRIDGE.find();
        if (found && found.health.ai) {
          const pref = langSel.value === "auto" ? detectLang(t) : langSel.value;
          const sys = "You are J.A.R.V.I.S from INSAN CREATIONS. Reply in " +
            ({ en: "English", hi: "Hindi", pa: "Punjabi" }[pref] || "English") +
            ". This is the web companion: no Windows app launching. Be concise.";
          return await window.INSAN_BRIDGE.chat("jarvis", t, sys);
        }
      } catch (e) {
        return "SpaceXAI error: " + e.message + " Start INSAN Bridge on the PC, or use JARVIS.exe.";
      }
    }
    if (/help|what can/.test(low)) {
      return "Type normally. Mic uses the browser if available. For Chrome/Gmail/VS Code as installed apps, run the Windows JARVIS.exe.";
    }
    return "I heard: “" + t + "”. On-device phrases only until INSAN Bridge has XAI_API_KEY. Windows app control is JARVIS.exe.";
  }

  line("JARVIS", "Type a command or question. You do not need a microphone. Voice is optional (browser speech).", "j");

  async function send() {
    const t = q.value.trim();
    if (!t) return;
    lastUser = t;
    line("You", t, "u");
    q.value = "";
    stopped = false;
    status.textContent = "THINKING…";
    const a = await reply(t);
    if (stopped) return;
    lastReply = a;
    line("JARVIS", a, "j");
    status.textContent = "ONLINE · type or speak";
  }

  document.getElementById("bar").onsubmit = function (e) {
    e.preventDefault();
    send();
  };
  q.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
  document.getElementById("stop").onclick = function () {
    stopped = true;
    status.textContent = "STOPPED";
  };
  document.getElementById("copy").onclick = function () {
    if (lastReply) navigator.clipboard.writeText(lastReply).catch(function () {});
  };
  document.getElementById("clear").onclick = function () {
    log.innerHTML = "";
    lastReply = "";
    line("JARVIS", "Cleared.", "j");
  };
  document.getElementById("regen").onclick = function () {
    if (!lastUser) return;
    q.value = lastUser;
    send();
  };
  document.getElementById("mic").onclick = function () {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      line("JARVIS", "This browser has no speech recognition. Type instead — typing is a core feature.", "j");
      return;
    }
    const rec = new SR();
    rec.lang = ({ auto: "en-IN", en: "en-IN", hi: "hi-IN", pa: "pa-IN" })[langSel.value] || "en-IN";
    rec.onresult = function (ev) {
      q.value = ev.results[0][0].transcript;
      send();
    };
    rec.onerror = function () {
      line("JARVIS", "Mic failed. Type your command.", "j");
    };
    rec.start();
    status.textContent = "LISTENING…";
  };

  let deferred;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferred = e;
    installBtn.hidden = false;
  });
  installBtn.onclick = function () { if (deferred) deferred.prompt(); };
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(function () {});

  (async function () {
    if (!window.INSAN_BRIDGE) return;
    const found = await window.INSAN_BRIDGE.find();
    document.getElementById("ai-st").textContent = found && found.health.ai
      ? "SpaceXAI connected via INSAN Bridge."
      : "Bridge offline — local replies. Windows app launching is JARVIS.exe.";
  })();
})();
