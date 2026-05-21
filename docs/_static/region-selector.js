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

  const targets = [];

  function collectTextNodes(root) {
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
  }

  function collectAttributes(root) {
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
  }

  function applyRegion(regionKey) {
    for (let i = 0; i < targets.length; i++) {
      const t = targets[i];
      const next = rewrite(t.original, regionKey);
      if (t.kind === "text") {
        if (t.node.nodeValue !== next) t.node.nodeValue = next;
      } else {
        if (t.node.getAttribute(t.attr) !== next) t.node.setAttribute(t.attr, next);
      }
    }
  }

  function buildToggle(current) {
    const wrap = document.createElement("div");
    wrap.className = "robusta-region-selector";
    wrap.setAttribute("role", "region");
    wrap.setAttribute("aria-label", "Robusta region selector");

    const label = document.createElement("span");
    label.className = "robusta-region-selector__label";
    label.textContent = "Select your region:";
    wrap.appendChild(label);

    const group = document.createElement("div");
    group.className = "robusta-region-selector__options";
    group.setAttribute("role", "radiogroup");

    Object.keys(REGIONS).forEach(function (key) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("role", "radio");
      btn.setAttribute("data-region", key);
      btn.className = "robusta-region-selector__btn";
      btn.textContent = REGIONS[key].label;
      const active = key === current;
      btn.setAttribute("aria-checked", String(active));
      if (active) btn.classList.add("is-active");
      btn.addEventListener("click", function () {
        const r = btn.getAttribute("data-region");
        saveRegion(r);
        applyRegion(r);
        group.querySelectorAll("button[data-region]").forEach(function (b) {
          const isActive = b.getAttribute("data-region") === r;
          b.classList.toggle("is-active", isActive);
          b.setAttribute("aria-checked", String(isActive));
        });
      });
      group.appendChild(btn);
    });

    wrap.appendChild(group);

    const note = document.createElement("span");
    note.className = "robusta-region-selector__note";
    note.textContent = "URLs on this page will update to match.";
    wrap.appendChild(note);

    return wrap;
  }

  function init() {
    const content =
      document.querySelector(".md-content__inner") ||
      document.querySelector("article.md-content__inner") ||
      document.querySelector("article") ||
      document.querySelector("main");
    if (!content) return;

    collectTextNodes(content);
    collectAttributes(content);
    if (targets.length === 0) return;

    const region = getRegion();
    const toggle = buildToggle(region);

    const firstHeading = content.querySelector("h1");
    if (firstHeading && firstHeading.parentNode) {
      firstHeading.parentNode.insertBefore(toggle, firstHeading.nextSibling);
    } else {
      content.insertBefore(toggle, content.firstChild);
    }

    if (region !== "us") applyRegion(region);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
