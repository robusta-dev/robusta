(function () {
  "use strict";

  const REGIONS = {
    us: { label: "US", infix: "" },
    eu: { label: "EU", infix: ".eu" },
    ap: { label: "AP", infix: ".ap" },
  };
  const STORAGE_KEY = "robusta-docs-region";
  const URL_PATTERN = /\b(platform|api)(?:\.(?:eu|ap))?\.robusta\.dev\b/g;
  const DETECT_PATTERN = /\b(?:platform|api)(?:\.(?:eu|ap))?\.robusta\.dev\b/;
  const BAR_CLASS = "robusta-region-box__bar";
  const BTN_CLASS = "robusta-region-box__region-btn";

  function getRegion() {
    try {
      const r = localStorage.getItem(STORAGE_KEY);
      return REGIONS[r] ? r : "us";
    } catch (e) {
      return "us";
    }
  }

  function saveRegion(r) {
    try {
      localStorage.setItem(STORAGE_KEY, r);
    } catch (e) {}
  }

  function rewrite(text, regionKey) {
    const infix = REGIONS[regionKey].infix;
    return text.replace(URL_PATTERN, function (_, sub) {
      return sub + infix + ".robusta.dev";
    });
  }

  // Each box on the page has its own collection of URL targets so its
  // contents update in place when the region changes.
  const boxes = [];

  function collectTargets(root) {
    const targets = [];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || !DETECT_PATTERN.test(node.nodeValue)) {
          return NodeFilter.FILTER_REJECT;
        }
        const parent = node.parentNode;
        if (parent && (parent.tagName === "SCRIPT" || parent.tagName === "STYLE")) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    let node;
    while ((node = walker.nextNode())) {
      targets.push({ kind: "text", node: node, original: node.nodeValue });
    }
    const ATTR_NAMES = ["href", "src", "data-clipboard-text", "value", "title"];
    const selector = ATTR_NAMES.map(function (a) { return "[" + a + "]"; }).join(",");
    root.querySelectorAll(selector).forEach(function (el) {
      ATTR_NAMES.forEach(function (attr) {
        const v = el.getAttribute(attr);
        if (v && DETECT_PATTERN.test(v)) {
          targets.push({ kind: "attr", node: el, attr: attr, original: v });
        }
      });
    });
    return targets;
  }

  function applyToBox(box, regionKey) {
    for (let i = 0; i < box.targets.length; i++) {
      const t = box.targets[i];
      const next = rewrite(t.original, regionKey);
      if (t.kind === "text") {
        if (t.node.nodeValue !== next) t.node.nodeValue = next;
      } else {
        if (t.node.getAttribute(t.attr) !== next) t.node.setAttribute(t.attr, next);
      }
    }
    updateBoxButtons(box, regionKey);
  }

  function updateBoxButtons(box, regionKey) {
    box.buttons.forEach(function (btn) {
      const isActive = btn.getAttribute("data-region") === regionKey;
      btn.classList.toggle("is-active", isActive);
      btn.setAttribute("aria-checked", String(isActive));
    });
  }

  function syncAll(regionKey) {
    saveRegion(regionKey);
    boxes.forEach(function (box) {
      applyToBox(box, regionKey);
    });
  }

  function buildBar(currentRegion) {
    const bar = document.createElement("div");
    bar.className = BAR_CLASS;

    const label = document.createElement("span");
    label.className = "robusta-region-box__bar-label";
    label.textContent = "Region";
    bar.appendChild(label);

    const group = document.createElement("div");
    group.className = "robusta-region-box__region-options";
    group.setAttribute("role", "radiogroup");
    group.setAttribute("aria-label", "Select your Robusta region");

    const buttons = [];
    Object.keys(REGIONS).forEach(function (key) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("role", "radio");
      btn.setAttribute("data-region", key);
      btn.className = BTN_CLASS;
      btn.textContent = REGIONS[key].label;
      const active = key === currentRegion;
      btn.setAttribute("aria-checked", String(active));
      if (active) btn.classList.add("is-active");
      btn.addEventListener("click", function () {
        syncAll(key);
      });
      group.appendChild(btn);
      buttons.push(btn);
    });

    bar.appendChild(group);
    return { bar: bar, buttons: buttons };
  }

  function initBox(el, currentRegion) {
    const existingBar = el.querySelector(":scope > ." + BAR_CLASS);
    if (existingBar) existingBar.remove();

    const built = buildBar(currentRegion);
    el.insertBefore(built.bar, el.firstChild);

    const targetRoot = el.querySelector(".robusta-region-box__body") || el;
    const targets = collectTargets(targetRoot);

    const box = {
      el: el,
      bar: built.bar,
      buttons: built.buttons,
      targets: targets,
    };
    boxes.push(box);
    applyToBox(box, currentRegion);
  }

  function init() {
    boxes.length = 0;
    const content =
      document.querySelector(".md-content__inner") ||
      document.querySelector("article") ||
      document.querySelector("main") ||
      document.body;
    if (!content) return;

    const region = getRegion();
    const elements = content.querySelectorAll(".robusta-region-box");
    elements.forEach(function (el) {
      initBox(el, region);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Material/Sphinx-Immaterial instant navigation swaps the content area
  // without firing DOMContentLoaded. The theme exposes an RxJS `document$`
  // observable that emits on every swap; re-run init() on each emission.
  if (typeof window !== "undefined" && window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  }
})();
