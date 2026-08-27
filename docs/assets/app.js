(function () {
  const deviceEl = document.getElementById("device");
  const formatEl = document.getElementById("format");
  const statusEl = document.getElementById("status");
  const dlBtn = document.getElementById("dl");

  // Public GitHub release / docs paths (no personal files)
  const RELEASE = "https://github.com/sl8722569-ux/jarvis-assitant/releases/latest/download/";
  const LOCAL = "downloads/";
  const LINKS = {
    windows: {
      zip: RELEASE + "JARVIS-Windows-Phase2.zip",
      apk: null,
      xapk: null,
    },
    android: {
      zip: LOCAL + "JARVIS-Android-WebCompanion.zip",
      apk: null,
      xapk: null,
    },
    ios: { zip: null, apk: null, xapk: null },
    linux: {
      zip: RELEASE + "JARVIS-Windows-Phase2.zip",
      apk: null,
      xapk: null,
    },
    web: { zip: null, apk: null, xapk: null },
  };

  const NOTES = {
    windows: {
      zip: "Windows ZIP — full J.A.R.V.I.S. Unzip and run INSTALL-WINDOWS.bat (installer + shortcuts) or Start_JARVIS.bat. Also see Releases for the portable JARVIS.exe pack.",
      apk: "APK is an Android package. It is not used on Windows. Switch device to Android, or pick ZIP.",
      xapk: "XAPK is an Android package. Use ZIP for Windows.",
    },
    android: {
      zip: "ZIP of the project source. You can run the web companion now. Native APK/XAPK is offered when a build exists.",
      apk: "No native APK is published. Use Web companion: Chrome → Add to Home Screen.",
      xapk: "No native XAPK is published. Use Web companion: Chrome → Add to Home Screen.",
    },
    ios: {
      zip: "iOS does not install this ZIP as an app. Use the web companion in Safari → Share → Add to Home Screen.",
      apk: "APK is Android-only. For iPhone/iPad use the web companion.",
      xapk: "XAPK is Android-only. For iPhone/iPad use the web companion.",
    },
    linux: {
      zip: "Same project ZIP. On Linux: Python 3.11+, pip install -r requirements.txt, python jarvis.py (TTS uses local engines).",
      apk: "APK is Android-only. Pick ZIP for Linux.",
      xapk: "XAPK is Android-only. Pick ZIP for Linux.",
    },
    web: {
      zip: "No ZIP required. Open the web companion in your browser.",
      apk: "Not a web format. Open the web companion instead.",
      xapk: "Not a web format. Open the web companion instead.",
    },
  };

  function combo() {
    return { device: deviceEl.value, format: formatEl.value };
  }

  function refresh() {
    const { device, format } = combo();
    const note = (NOTES[device] && NOTES[device][format]) || "";
    const url = LINKS[device] && LINKS[device][format];
    statusEl.className = "status";
    if (device === "web") {
      statusEl.textContent = "Web companion works in the browser on phones, tablets, and PCs. No APK/ZIP needed.";
      statusEl.classList.add("ok");
      dlBtn.textContent = "Open web companion";
      return;
    }
    if (url) {
      statusEl.textContent = note + " Ready to download.";
      statusEl.classList.add("ok");
      dlBtn.textContent = "Download " + format.toUpperCase();
    } else {
      statusEl.textContent = note + " This format is not available for that device yet (coming soon).";
      statusEl.classList.add("wait");
      dlBtn.textContent = "Not available yet";
    }
  }

  function download() {
    const { device, format } = combo();
    if (device === "web") {
      window.location.href = "webapp/index.html";
      return;
    }
    const url = LINKS[device] && LINKS[device][format];
    if (!url) {
      statusEl.className = "status wait";
      statusEl.textContent =
        "No " +
        format.toUpperCase() +
        " for " +
        device +
        " yet. For phones, use Open web companion. Windows/Linux: choose ZIP.";
      return;
    }
    // Probe file; if GitHub 404, show honest message
    statusEl.className = "status";
    statusEl.textContent = "Starting download…";
    window.location.href = url;
    setTimeout(function () {
      statusEl.className = "status ok";
      statusEl.textContent =
        "If the file did not start, the package may still be publishing. Use GitHub Releases or pick ZIP for Windows.";
    }, 1200);
  }

  deviceEl.addEventListener("change", refresh);
  formatEl.addEventListener("change", refresh);
  dlBtn.addEventListener("click", download);
  refresh();
})();
