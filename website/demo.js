/* A narrated, fictional walkthrough of the actual Flutter screen order. */
(() => {
  const root = document.documentElement;
  const themeButton = document.getElementById("theme-toggle");
  try { root.dataset.theme = localStorage.getItem("mednarrate-theme") || "light"; } catch (_) {}
  function updateThemeButton() {
    themeButton.setAttribute("aria-label", root.dataset.theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    themeButton.textContent = root.dataset.theme === "dark" ? "☀" : "◐";
  }
  updateThemeButton();
  themeButton.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    try { localStorage.setItem("mednarrate-theme", root.dataset.theme); } catch (_) {}
    updateThemeButton();
  });

  const screen = document.getElementById("device-screen");
  const content = document.getElementById("screen-content");
  const pointer = document.getElementById("demo-pointer");
  const journey = document.getElementById("journey");
  const count = document.getElementById("stage-count");
  const caption = document.getElementById("stage-caption");
  const progress = document.getElementById("progress-track");
  const fill = document.getElementById("progress-fill");
  const play = document.getElementById("play-button");
  const previous = document.getElementById("prev-button");
  const next = document.getElementById("next-button");
  const replay = document.getElementById("replay-button");

  function bottomNav() {
    return "<div class='app-bottom-nav'><span class='active'><b>▦</b>Dashboard</span><span><b>▤</b>Journal</span><span><b>⚙</b>Settings</span><span><b>♙</b>Profile</span></div>";
  }
  function topbar(title) {
    return "<div class='app-topbar'><span class='app-back'>‹</span><span>" + title + "</span></div>";
  }
  function uploadForm(state) {
    const selected = state === "ready" || state === "processing";
    const processing = state === "processing";
    const file = selected
      ? "<div class='file-selected'><span class='pdf-icon'>▣</span><span><strong>sample_blood_report.pdf</strong><small>132 KB · PDF</small></span><span class='ready-badge'>" + (processing ? "Report uploaded" : "File Ready") + "</span></div>"
      : "<button class='file-drop' data-next type='button'><span class='drop-icon'>⇧</span><span>Choose a file to analyze</span><small>Supports PDF, JPG, JPEG, PNG (up to 25 MB)</small></button>";
    return [
      "<div class='app-scene upload-scene'>", topbar("Upload Report"), "<div class='scene-scroll'><div class='app-body'>",
      "<div class='upload-hero'><div class='upload-icon'>⇧</div><h2>Upload Medical Report</h2></div>",
      "<div class='app-card upload-form-card'>",
      "<span class='app-mini-label'>Report Title *</span><div class='app-field " + (selected ? "" : "placeholder") + "'><span class='field-icon'>▤</span>" + (selected ? "Sample blood report" : "e.g. Annual Blood Test") + "</div>",
      "<span class='app-mini-label'>Hospital / Clinic (optional)</span><div class='app-field placeholder'><span class='field-icon'>✚</span>e.g. City General Hospital</div>",
      "<div class='upload-type-date'><div><span class='app-mini-label'>Report Type</span><div class='app-field'>Blood Test ▾</div></div><div><span class='app-mini-label'>Report Date</span><div class='app-field'>Auto-detect from document</div></div></div>",
      "</div>", file,
      processing ? "<div class='process-card'><span class='ready-badge'>Report uploaded</span><strong>Extracting text and analyzing report...</strong><div class='process-line'><span></span></div><small>The app checks processing status until the result is ready.</small></div>" : "",
      "<p class='upload-notice'>Your document will be stored and its text processed by MedNarrate and configured AI services to create an explanation. Check important results against the original report.</p>",
      "<button class='app-button' type='button' " + (selected && !processing ? "data-next" : "disabled") + ">" + (processing ? "Processing report…" : "Upload &amp; Analyze") + "</button>",
      "</div></div>",
      state === "picker" ? "<div class='finder-backdrop'><div class='finder-window'><div class='finder-title'>Choose a medical report</div><div class='finder-row'>▣ &nbsp; sample_blood_report.pdf</div><div class='finder-foot'><button type='button'>Cancel</button><button type='button' data-next>Open</button></div></div></div>" : "",
      "</div>"
    ].join("");
  }
  function tabs(active) {
    return "<div class='report-tabs'>" + ["For You", "Clinical View", "Lab Results", "AI Chat"].map((label) => {
      const selected = active === label ? " active" : "";
      const onward = (active === "For You" && label === "Clinical View") ||
        (active === "Clinical View" && label === "Lab Results") ||
        (active === "Lab Results" && label === "AI Chat");
      return "<span class='" + selected + "'" + (onward ? " data-next" : "") + ">" + label + "</span>";
    }).join("") + "</div>";
  }
  function reportHead() {
    return "<div class='app-topbar'><span class='app-back'>‹</span><span>Report Details</span><span class='app-header-actions'>♡⋮</span></div>";
  }
  function overview() {
    return "<div class='app-card overview'><div class='overview-head'><span class='overview-icon'>♙</span><span><strong>Sample blood report</strong><small>24 Jun 2023 · Blood Test</small></span></div><div class='overview-stats'><span><strong>1</strong> Lab Result</span><span><strong>0</strong> Medications</span><span><strong>1</strong> Noteworthy</span></div></div>";
  }
  function reportScreen(active) {
    let body;
    if (active === "For You") {
      body = overview() +
        "<div class='section-row'><h3>Report at a Glance</h3><button type='button'>⚑ Translate</button></div>" +
        "<div class='app-card summary-card'><b>1. What Your Report Says</b><p>Your report contains one extracted laboratory test result.</p><b>2. Key Findings</b><p>Result outside the reported reference range:</p><ul><li>Hemoglobin: 10.2 g/dL — flagged LOW (reported range: 12.0–16.0 g/dL).</li></ul><b>3. What to Discuss</b><p>Ask a clinician how this finding fits with your health history and symptoms.</p><div class='attribution'>Example AI explanation · review the original report</div></div>";
    } else if (active === "Clinical View") {
      body = "<div class='section-row'><h3>Clinical View</h3></div><div class='app-card summary-card'><b>Clinician Summary</b><p>Fictional sample: hemoglobin 10.2 g/dL, below the sample report's stated interval of 12.0–16.0 g/dL.</p><b>Abnormal Findings</b><p>Hemoglobin — LOW</p><b>Clinical note</b><p>Interpretation requires clinical context. This finding alone is not a diagnosis.</p></div>";
    } else if (active === "Lab Results") {
      body = "<div class='section-row'><h3>Lab Results</h3></div><div class='app-card'><div class='lab-row'><div><strong>Hemoglobin</strong><small>Reported range 12.0–16.0 g/dL</small></div><div class='lab-value'>10.2 g/dL<br><span class='low-tag'>LOW</span></div></div></div><p class='app-sub'>Compare values with the original PDF. Reference ranges can vary by laboratory.</p>";
    } else {
      body = "<div class='chat-bubble user'>What does the hemoglobin result mean?</div><div class='chat-bubble ai'>The fictional report shows hemoglobin below its stated range. One result cannot identify a cause or confirm a diagnosis. Please review it with a clinician alongside your symptoms and history.</div><div class='chat-input' data-cursor-target>Ask about your report... <span class='chat-send'>➤</span></div>";
    }
    return "<div class='app-scene report-scene'>" + reportHead() + tabs(active) + "<div class='scene-scroll'><div class='app-body'>" + body + "</div></div></div>";
  }
  function onboardingScene(title, body, icon, page) {
    return "<div class='app-scene'><div class='app-pad' style='text-align:right'><button type='button' class='app-text-button' data-skip>Skip</button></div>" +
      "<div class='onboard-art'>" + icon + "</div>" +
      "<div class='onboard-copy'><h2>" + title + "</h2><p>" + body + "</p></div>" +
      "<div class='onboard-dots'>" + [0, 1, 2, 3].map((dot) => "<i" + (dot === page ? " class='active'" : "") + "></i>").join("") + "</div>" +
      "<div style='padding:0 24px'><button class='app-button' data-next type='button'>" + (page === 3 ? "Get Started" : "Continue") + "</button></div></div>";
  }
  function illustration(page) {
    const start = "<svg class='onboard-svg' viewBox='0 0 280 220' role='img' aria-label='Medical illustration'><circle cx='140' cy='110' r='100' fill='#E8F4F0'/>";
    if (page === 0) {
      return start + "<rect x='90' y='50' width='100' height='130' rx='10' fill='#17211D' opacity='.98'/>" +
        "<path d='M102 75h74 M102 93h74 M102 111h62 M102 129h74 M102 147h74' stroke='#2A9D85' stroke-width='3' stroke-linecap='round'/>" +
        "<path d='M182 44v22 M171 55h22' stroke='#0B7563' stroke-width='6'/>" +
        "<circle cx='190' cy='155' r='18' fill='none' stroke='#00C48C' stroke-width='4'/><path d='m203 168 10 10' stroke='#00C48C' stroke-width='4'/></svg>";
    }
    if (page === 1) {
      return start + "<rect x='90' y='80' width='20' height='60' rx='4' fill='#0B7563'/><rect x='118' y='50' width='20' height='90' rx='4' fill='#00C48C'/><rect x='146' y='95' width='20' height='45' rx='4' fill='#F5A623'/><rect x='174' y='65' width='20' height='75' rx='4' fill='#0B7563'/>" +
        "<rect x='155' y='37' width='80' height='36' rx='12' fill='#17211D'/><circle cx='177' cy='55' r='10' fill='#00C48C'/><circle cx='75' cy='50' r='10' fill='#E53935'/></svg>";
    }
    if (page === 2) {
      return start + "<circle cx='85' cy='130' r='32' fill='#00C48C' opacity='.2'/><circle cx='140' cy='100' r='40' fill='#0B7563' opacity='.2'/><circle cx='195' cy='130' r='32' fill='#F5A623' opacity='.2'/>" +
        "<circle cx='85' cy='121' r='11' fill='#00C48C'/><circle cx='140' cy='89' r='14' fill='#0B7563'/><circle cx='195' cy='121' r='11' fill='#F5A623'/>" +
        "<path d='M70 148q15-12 30 0M120 122q20-17 40 0M180 148q15-12 30 0' fill='none' stroke='#0B7563' stroke-width='8' stroke-linecap='round'/>" +
        "<path d='M140 64c-22-20-30 7 0 25 30-18 22-45 0-25Z' fill='#E53935'/></svg>";
    }
    return start + "<rect x='55' y='25' width='170' height='170' rx='40' fill='#0B7563' opacity='.12'/><path d='M85 145h26l17-52 24 69 17-37h29' fill='none' stroke='#0B7563' stroke-width='10' stroke-linecap='round' stroke-linejoin='round'/></svg>";
  }

  const scenes = [
    { label: "Open the app", note: "Splash", caption: "MedNarrate starts and checks your session.", target: null,
      html: "<div class='app-scene splash-scene'><div class='splash-center'><div class='splash-logo'><svg viewBox='0 0 80 80' aria-hidden='true'><rect x='13' y='24' width='54' height='42' rx='7' fill='#0E1713'/><path d='M30 24v-8h20v8' fill='none' stroke='#0E1713' stroke-width='6' stroke-linejoin='round'/><path d='M40 36v19M31 45.5h18' stroke='#0B7563' stroke-width='6' stroke-linecap='round'/></svg></div><h2>MedNarrate</h2><p>AI Medical Report Assistant</p><div class='spinner'></div></div></div>" },
    { label: "Understand reports", note: "Onboarding 1/4", caption: "The first onboarding page introduces report explanations.", target: ".app-button[data-next]",
      html: onboardingScene("Understand<br>Medical Reports", "Upload any medical report and let AI explain every medical term in simple language.", illustration(0), 0) },
    { label: "AI assistant", note: "Onboarding 2/4", caption: "The second page introduces questions about uploaded reports.", target: ".app-button[data-next]",
      html: onboardingScene("AI Health<br>Assistant", "Ask questions about your uploaded reports and receive clear, easy-to-understand explanations.", illustration(1), 1) },
    { label: "Reminders", note: "Onboarding 3/4", caption: "The third page introduces medicine reminders.", target: ".app-button[data-next]",
      html: onboardingScene("Medicine<br>Reminders", "Never miss your medicines. Receive intelligent reminders based on your prescriptions.", illustration(2), 2) },
    { label: "Track health", note: "Onboarding 4/4", caption: "Get Started opens Sign Up after the fourth onboarding page.", target: ".app-button[data-next]",
      html: onboardingScene("Track Your<br>Health", "Monitor health trends, compare reports and understand your progress over time.", illustration(3), 3) },
    { label: "Create account", note: "Sign Up", caption: "The real Sign Up screen creates an account before opening the dashboard.", target: ".signup-scene .app-button[data-next]",
      html: "<div class='app-scene signup-scene'><div class='app-body'><h2 class='app-heading'>Create Account</h2><p class='app-sub'>Let's personalize your health journey.</p><div class='login-form'><span class='app-mini-label'>Full Name</span><div class='app-field'>♙ &nbsp; Alex Morgan</div><span class='app-mini-label'>Email Address</span><div class='app-field'>✉ &nbsp; alex@example.com</div><span class='app-mini-label'>Password</span><div class='app-field'>♧ &nbsp; ••••••••••••</div><span class='app-mini-label'>Confirm Password</span><div class='app-field'>♧ &nbsp; ••••••••••••</div><p class='signup-notice'>MedNarrate explains reports but does not diagnose conditions or replace a clinician. <span class='app-text-button'>Terms of Service</span> · <span class='app-text-button'>Privacy Policy</span></p><button class='app-button' data-next type='button'>Sign Up</button></div><div class='login-footer'><span class='app-text-button'>Already have an account? Login</span></div></div></div>" },
    { label: "Dashboard", note: "Upload entry", caption: "The dashboard's Upload Report card opens the real upload route.", target: ".upload-tile",
      html: "<div class='app-scene dashboard-scene'><div class='scene-scroll'><div class='app-body'><div class='dash-greeting'>Good morning</div><div class='dash-name'>Alex</div><div class='health-card'><b>Health Score</b><span class='health-score'>—</span><p class='app-sub'>Upload a completed report to see your score.</p></div><div class='dash-stats'><div><strong>0</strong>Reports</div><div><strong>0</strong>Reminders</div><div><strong>0</strong>Favourites</div></div><button type='button' class='upload-tile' data-next><span class='tile-icon'>⇧</span><b>Upload Report</b><small>Tap here to upload a new medical report for analysis</small></button><div class='quick-row'><span>▤<br>All Reports</span><span>✦<br>AI Chat</span><span>▥<br>Insights</span></div><div class='section-row'><h3>Recent Reports</h3></div><p class='app-sub'>Your recent medical reports will appear here once you add them.</p></div></div>" + bottomNav() + "</div>" },
    { label: "Report details", note: "Upload form", caption: "Enter a title, optional clinic, report type and date, then choose a file.", target: ".file-drop",
      html: uploadForm("empty") },
    { label: "Choose a PDF", note: "File picker", caption: "On macOS, the native file chooser opens for PDF, JPG, JPEG and PNG files.", target: ".finder-foot [data-next]",
      html: uploadForm("picker") },
    { label: "Review file", note: "Ready", caption: "Selecting a file fills the title suggestion and enables Upload & Analyze.", target: ".upload-scene .app-button[data-next]",
      html: uploadForm("ready") },
    { label: "Analyze report", note: "Processing", caption: "The app uploads the file, extracts text, starts analysis and checks status.", target: null,
      html: uploadForm("processing") },
    { label: "For You", note: "Patient view", caption: "Success opens Report Details on the For You tab with the patient summary.", target: ".report-tabs [data-next]",
      html: reportScreen("For You") },
    { label: "Clinical View", note: "Output", caption: "Clinical View shows a clinician-oriented summary and extracted findings.", target: ".report-tabs [data-next]",
      html: reportScreen("Clinical View") },
    { label: "Lab Results", note: "Output", caption: "Lab Results keeps the reported value, range and LOW flag together.", target: ".report-tabs [data-next]",
      html: reportScreen("Lab Results") },
    { label: "AI Chat", note: "Follow-up", caption: "AI Chat is a tab within Report Details for questions about this report.", target: "[data-cursor-target]",
      html: reportScreen("AI Chat") }
  ];

  let index = 0;
  let playing = false;
  let advanceTimer = null;
  let pointerTimer = null;
  let tapTimer = null;
  let releaseTimer = null;
  let pressedTarget = null;
  let advancingAutomatically = false;

  scenes.forEach((scene, sceneIndex) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "journey-step";
    button.innerHTML = "<span class='number'>" + String(sceneIndex + 1).padStart(2, "0") + "</span><span class='journey-title'>" + scene.label + "</span><span class='journey-note'>" + scene.note + "</span>";
    button.addEventListener("click", () => { pause(); show(sceneIndex); });
    journey.appendChild(button);
  });

  function clearPointerTimers() {
    clearTimeout(pointerTimer);
    clearTimeout(tapTimer);
    clearTimeout(releaseTimer);
    if (pressedTarget) pressedTarget.classList.remove("demo-pressed");
    pressedTarget = null;
  }
  function movePointer() {
    clearPointerTimers();
    const targetSelector = scenes[index].target;
    const target = targetSelector ? content.querySelector(targetSelector) : null;
    pointer.classList.remove("tap");
    if (!target) {
      pointer.style.opacity = "0";
      return;
    }
    const scroller = target.closest(".scene-scroll");
    if (scroller) {
      const targetBox = target.getBoundingClientRect();
      const scrollBox = scroller.getBoundingClientRect();
      if (targetBox.bottom > scrollBox.bottom - 16) {
        scroller.scrollTop += targetBox.bottom - scrollBox.bottom + 24;
      } else if (targetBox.top < scrollBox.top + 16) {
        scroller.scrollTop -= scrollBox.top - targetBox.top + 24;
      }
    }
    const screenRect = screen.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const x = Math.max(22, Math.min(screenRect.width - 22, targetRect.left - screenRect.left + targetRect.width / 2));
    const y = Math.max(43, Math.min(screenRect.height - 24, targetRect.top - screenRect.top + targetRect.height / 2));
    const startX = Math.max(22, Math.min(screenRect.width - 22, x + (x > screenRect.width / 2 ? -48 : 48)));
    const startY = Math.max(43, Math.min(screenRect.height - 24, y + (y > screenRect.height / 2 ? -42 : 42)));
    pointer.style.transition = "none";
    pointer.style.left = startX + "px";
    pointer.style.top = startY + "px";
    pointer.style.opacity = "0";
    pointerTimer = setTimeout(() => {
      pointer.style.transition = "";
      pointer.style.left = x + "px";
      pointer.style.top = y + "px";
      pointer.style.opacity = "1";
    }, 60);
    tapTimer = setTimeout(() => {
      pointer.classList.remove("tap");
      void pointer.offsetWidth;
      pointer.classList.add("tap");
      target.classList.add("demo-pressed");
      pressedTarget = target;
      releaseTimer = setTimeout(() => {
        target.classList.remove("demo-pressed");
        pressedTarget = null;
      }, 410);
    }, 760);
  }
  function show(newIndex) {
    index = Math.max(0, Math.min(scenes.length - 1, newIndex));
    content.innerHTML = scenes[index].html;
    const tabBar = content.querySelector(".report-tabs");
    const activeTab = content.querySelector(".report-tabs .active");
    if (tabBar && activeTab) {
      tabBar.scrollLeft = Math.max(0, activeTab.offsetLeft - tabBar.offsetLeft - 18);
    }
    count.textContent = String(index + 1).padStart(2, "0") + " / " + scenes.length;
    caption.textContent = scenes[index].caption;
    progress.setAttribute("aria-valuemax", String(scenes.length));
    progress.setAttribute("aria-valuenow", String(index + 1));
    fill.style.width = ((index + 1) / scenes.length * 100) + "%";
    previous.disabled = index === 0;
    next.disabled = index === scenes.length - 1;
    [...journey.children].forEach((button, buttonIndex) => {
      button.classList.toggle("active", buttonIndex === index);
      button.setAttribute("aria-current", buttonIndex === index ? "step" : "false");
    });
    movePointer();
  }
  function pause() {
    playing = false;
    clearTimeout(advanceTimer);
    play.textContent = "▶ Play walkthrough";
  }
  function scheduleAdvance() {
    clearTimeout(advanceTimer);
    if (!playing) return;
    const dwell = index === 0 ? 1100 : index === 10 ? 2300 : index >= 11 ? 2100 : 1450;
    advanceTimer = setTimeout(() => {
      if (index >= scenes.length - 1) { pause(); return; }
      const targetSelector = scenes[index].target;
      const target = targetSelector ? content.querySelector(targetSelector) : null;
      if (target && target.hasAttribute("data-next")) {
        advancingAutomatically = true;
        target.click();
        advancingAutomatically = false;
      } else {
        show(index + 1);
      }
      scheduleAdvance();
    }, dwell);
  }
  play.addEventListener("click", () => {
    if (playing) { pause(); return; }
    if (index === scenes.length - 1) show(0);
    playing = true;
    play.textContent = "Ⅱ Pause walkthrough";
    scheduleAdvance();
  });
  previous.addEventListener("click", () => { pause(); show(index - 1); });
  next.addEventListener("click", () => { pause(); show(index + 1); });
  replay.addEventListener("click", () => { pause(); show(0); playing = true; play.textContent = "Ⅱ Pause walkthrough"; scheduleAdvance(); });
  screen.addEventListener("click", (event) => {
    if (event.target.closest("[data-skip]") && index >= 1 && index <= 4) {
      pause();
      show(5);
      return;
    }
    if (event.target.closest("[data-next]") && index < scenes.length - 1) {
      if (!advancingAutomatically) pause();
      show(index + 1);
    }
  });
  window.addEventListener("resize", () => movePointer());
  show(0);
})();
