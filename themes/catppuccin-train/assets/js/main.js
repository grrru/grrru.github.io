const THEME_KEY = "theme-preference";

function readPreferredTheme() {
  const saved = window.localStorage.getItem(THEME_KEY);
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const toggle = document.querySelector("[data-theme-toggle]");
  if (!toggle) {
    return;
  }
  toggle.dataset.themeState = theme;
  toggle.setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} theme`);
  toggle.textContent = theme === "dark" ? "Dark" : "Light";
}

function setupThemeToggle() {
  applyTheme(readPreferredTheme());
  const toggle = document.querySelector("[data-theme-toggle]");
  if (!toggle) {
    return;
  }
  toggle.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    window.localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  });
}

function updateOverflowState(block) {
  const pre = block.querySelector("pre");
  const expandButton = block.querySelector("[data-code-expand]");
  if (!pre || !expandButton) {
    return;
  }

  const hasOverflow = pre.scrollWidth > pre.clientWidth + 4;
  expandButton.hidden = !hasOverflow;

  if (!hasOverflow) {
    block.classList.remove("wrapped");
    expandButton.textContent = "Wrap";
  }
}

function setupCodeBlocks() {
  const blocks = document.querySelectorAll("[data-codeblock]");
  if (!blocks.length) {
    return;
  }

  for (const block of blocks) {
    const copyButton = block.querySelector("[data-code-copy]");
    const expandButton = block.querySelector("[data-code-expand]");
    const code = block.querySelector("code");

    if (copyButton && code) {
      copyButton.addEventListener("click", async () => {
        const previous = copyButton.textContent;
        try {
          await navigator.clipboard.writeText(code.innerText);
          copyButton.textContent = "Copied";
        } catch {
          copyButton.textContent = "Failed";
        }
        window.setTimeout(() => {
          copyButton.textContent = previous;
        }, 1400);
      });
    }

    if (expandButton) {
      expandButton.addEventListener("click", () => {
        const wrapped = block.classList.toggle("wrapped");
        expandButton.textContent = wrapped ? "Nowrap" : "Wrap";
      });
    }

    updateOverflowState(block);
  }

  const resizeObserver = new ResizeObserver(() => {
    for (const block of blocks) {
      updateOverflowState(block);
    }
  });
  resizeObserver.observe(document.body);
}

document.addEventListener("DOMContentLoaded", () => {
  setupThemeToggle();
  setupCodeBlocks();
});
