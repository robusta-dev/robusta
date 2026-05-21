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
  const INLINE_PICKER_CLASS = "robusta-region-inline__picker";
  const INLINE_BTN_CLASS = "robusta-region-inline__btn";

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

  // All URL occurrences across the page content (text nodes + relevant
  // attributes). Boxes are separate — each holds its selector buttons so
  // every box on the page stays visually in sync on region change.
  const targets = [];
  const boxes = [];

  function collectTargets(root) {
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
    for (let j = 0; j < boxes.length; j++) {
      const box = boxes[j];
      if (box.buttons) {
        for (let k = 0; k < box.buttons.length; k++) {
          const btn = box.buttons[k];
          const active = btn.getAttribute("data-region") === regionKey;
          btn.classList.toggle("is-active", active);
          btn.setAttribute("aria-checked", String(active));
        }
      }
      if (box.items) {
        if (box.currentEl) box.currentEl.textContent = REGIONS[regionKey].label;
        for (let m = 0; m < box.items.length; m++) {
          const item = box.items[m];
          const active = item.getAttribute("data-region") === regionKey;
          item.classList.toggle("is-active", active);
          item.setAttribute("aria-selected", String(active));
        }
      }
    }
  }

  function syncAll(regionKey) {
    saveRegion(regionKey);
    applyRegion(regionKey);
  }

  function closeAllInlineMenus(except) {
    document.querySelectorAll("." + INLINE_PICKER_CLASS + ".is-open").forEach(function (p) {
      if (p === except) return;
      p.classList.remove("is-open");
      const trig = p.querySelector(".robusta-region-inline__trigger");
      if (trig) trig.setAttribute("aria-expanded", "false");
    });
  }

  function buildInlinePicker(currentRegion) {
    const picker = document.createElement("span");
    picker.className = INLINE_PICKER_CLASS;

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "robusta-region-inline__trigger";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");

    const currentEl = document.createElement("span");
    currentEl.className = "robusta-region-inline__current";
    currentEl.textContent = REGIONS[currentRegion].label;

    const caret = document.createElement("span");
    caret.className = "robusta-region-inline__caret";
    caret.setAttribute("aria-hidden", "true");
    caret.textContent = "▾";

    trigger.appendChild(currentEl);
    trigger.appendChild(caret);

    const menu = document.createElement("ul");
    menu.className = "robusta-region-inline__menu";
    menu.setAttribute("role", "listbox");

    const items = [];

    function focusItem(idx) {
      if (idx < 0) idx = items.length - 1;
      if (idx >= items.length) idx = 0;
      items.forEach(function (it, i) { it.tabIndex = i === idx ? 0 : -1; });
      items[idx].focus();
    }

    function selectItem(key) {
      syncAll(key);
      picker.classList.remove("is-open");
      trigger.setAttribute("aria-expanded", "false");
      trigger.focus();
    }

    Object.keys(REGIONS).forEach(function (key) {
      const item = document.createElement("li");
      item.setAttribute("role", "option");
      item.setAttribute("data-region", key);
      item.className = "robusta-region-inline__option";
      const isActive = key === currentRegion;
      item.setAttribute("aria-selected", String(isActive));
      item.tabIndex = isActive ? 0 : -1;
      if (isActive) item.classList.add("is-active");
      item.textContent = REGIONS[key].label;
      item.addEventListener("click", function (e) {
        e.preventDefault();
        selectItem(key);
      });
      item.addEventListener("keydown", function (e) {
        const idx = items.indexOf(item);
        switch (e.key) {
          case "Enter":
          case " ":
            e.preventDefault();
            selectItem(key);
            break;
          case "ArrowDown":
            e.preventDefault();
            focusItem(idx + 1);
            break;
          case "ArrowUp":
            e.preventDefault();
            focusItem(idx - 1);
            break;
          case "Home":
            e.preventDefault();
            focusItem(0);
            break;
          case "End":
            e.preventDefault();
            focusItem(items.length - 1);
            break;
          case "Tab":
            picker.classList.remove("is-open");
            trigger.setAttribute("aria-expanded", "false");
            break;
          case "Escape":
            e.preventDefault();
            picker.classList.remove("is-open");
            trigger.setAttribute("aria-expanded", "false");
            trigger.focus();
            break;
        }
      });
      menu.appendChild(item);
      items.push(item);
    });

    function openMenu() {
      closeAllInlineMenus(picker);
      picker.classList.add("is-open");
      trigger.setAttribute("aria-expanded", "true");
      const activeIdx = items.findIndex(function (it) { return it.classList.contains("is-active"); });
      focusItem(activeIdx >= 0 ? activeIdx : 0);
    }

    trigger.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (picker.classList.contains("is-open")) {
        picker.classList.remove("is-open");
        trigger.setAttribute("aria-expanded", "false");
      } else {
        openMenu();
      }
    });

    trigger.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openMenu();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        openMenu();
        focusItem(items.length - 1);
      }
    });

    picker.appendChild(trigger);
    picker.appendChild(menu);

    return { picker: picker, trigger: trigger, currentEl: currentEl, items: items };
  }

  function buildBar(currentRegion) {
    const bar = document.createElement("div");
    bar.className = BAR_CLASS;

    const label = document.createElement("span");
    label.className = "robusta-region-box__bar-label";
    label.textContent = "Select Region";
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

  function init() {
    targets.length = 0;
    boxes.length = 0;

    const content =
      document.querySelector(".md-content__inner") ||
      document.querySelector("article") ||
      document.querySelector("main") ||
      document.body;
    if (!content) return;

    const region = getRegion();

    content.querySelectorAll(".robusta-region-box").forEach(function (el) {
      const existingBar = el.querySelector(":scope > ." + BAR_CLASS);
      if (existingBar) existingBar.remove();
      const built = buildBar(region);
      el.insertBefore(built.bar, el.firstChild);
      boxes.push({ buttons: built.buttons });
    });

    content.querySelectorAll(".robusta-region-inline").forEach(function (el) {
      const existingPicker = el.querySelector(":scope > ." + INLINE_PICKER_CLASS);
      if (existingPicker) existingPicker.remove();
      const built = buildInlinePicker(region);
      el.appendChild(built.picker);
      boxes.push({ currentEl: built.currentEl, items: built.items });
    });

    collectTargets(content);

    if (targets.length === 0 && boxes.length === 0) return;

    applyRegion(region);
  }

  document.addEventListener("click", function (e) {
    const open = document.querySelector("." + INLINE_PICKER_CLASS + ".is-open");
    if (open && !open.contains(e.target)) closeAllInlineMenus(null);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeAllInlineMenus(null);
  });

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
