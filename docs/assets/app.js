(function () {
  const deviceEl = document.getElementById("device");
  const formatEl = document.getElementById("format");
  const statusEl = document.getElementById("status");
  const dlBtn = document.getElementById("dl");

  const RELEASE = "https://github.com/sl8722569-ux/jarvis-assitant/releases/latest/download/";
  const COMP = "downloads/JARVIS-Android-WebCompanion.zip";
  const WEB = "webapp/index.html";
  const WIN_ZIP = RELEASE + "JARVIS-Windows-Phase2.zip";
  const WIN_PORTABLE = RELEASE + "JARVIS-Windows-Portable.exe-pack.zip";

  const APK = RELEASE + "JARVIS-Android.apk";
  const LINKS = {
    windows: { zip: WIN_ZIP, portable: WIN_PORTABLE, apk: null },
    android: { zip: COMP, portable: null, apk: APK },
    ios: { zip: null, portable: null, apk: null },
    linux: { zip: WIN_ZIP, portable: null, apk: null },
    macos: { zip: WIN_ZIP, portable: null, apk: null },
    web: { zip: null, portable: null, apk: null },
  };

  const NOTES = {
    windows: {
      zip: "Windows ZIP — full J.A.R.V.I.S. Unzip and run INSTALL-WINDOWS.bat or Start_JARVIS.bat.",
      portable: "Portable pack with JARVIS.exe. Unzip and run; no installer required.",
    },
    android: {
      zip: "Android web companion ZIP / PWA. Chrome → Add to Home Screen.",
      portable: "Portable pack is Windows-only. Pick ZIP or APK for Android.",
      apk: "Sideload APK: official WebView of the live companion (camera/mic). Not the Windows Python app. Not Play Store.",
    },
    ios: {
      zip: "No native iOS app. Opens the web companion — Safari → Share → Add to Home Screen.",
      portable: "Portable pack is Windows-only. Use the web companion on iPhone/iPad.",
    },
    linux: {
      zip: "Experimental: this is the Windows/Python source ZIP. Use the Linux scripts inside. Not a native installer.",
      portable: "Portable pack is Windows-only. Pick ZIP for experimental Linux scripts.",
    },
    macos: {
      zip: "Experimental: this is the Windows/Python source ZIP. Use the macOS scripts inside. Not a native installer.",
      portable: "Portable pack is Windows-only. Pick ZIP for experimental macOS scripts.",
    },
    web: {
      zip: "No ZIP required. Opens the web companion in your browser.",
      portable: "No ZIP required. Opens the web companion in your browser.",
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
    if (device === "web" || device === "ios") {
      statusEl.textContent = note;
      statusEl.classList.add("ok");
      dlBtn.textContent = "Open web companion";
      return;
    }
    if (url) {
      statusEl.textContent = note + " Ready to download.";
      statusEl.classList.add("ok");
      dlBtn.textContent = "Download " + format;
    } else {
      statusEl.textContent = note || "That combo is not available. Windows: ZIP or portable. Phones: web companion. No APK/XAPK is published.";
      statusEl.classList.add("wait");
      dlBtn.textContent = "Not available";
    }
  }

  function download() {
    const { device, format } = combo();
    if (device === "web" || device === "ios") {
      window.location.href = WEB;
      return;
    }
    const url = LINKS[device] && LINKS[device][format];
    if (!url) {
      statusEl.className = "status wait";
      statusEl.textContent =
        "That package is not published for " +
        device +
        ". Windows: ZIP or portable. Phones: web companion. No APK/XAPK exists.";
      return;
    }
    statusEl.className = "status";
    statusEl.textContent = "Starting download…";
    window.location.href = url;
    setTimeout(function () {
      statusEl.className = "status ok";
      statusEl.textContent = "If the file did not start, open GitHub Releases and pick the Windows ZIP or portable pack.";
    }, 1200);
  }

  deviceEl.addEventListener("change", refresh);
  formatEl.addEventListener("change", refresh);
  dlBtn.addEventListener("click", download);
  refresh();
})();
