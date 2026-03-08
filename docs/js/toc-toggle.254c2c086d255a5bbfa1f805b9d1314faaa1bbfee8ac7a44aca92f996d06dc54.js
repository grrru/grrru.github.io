(() => {
  // <stdin>
  document.addEventListener("DOMContentLoaded", function() {
    const tocToggleButton = document.getElementById("toc-toggle-button");
    const tocContainer = document.getElementById("toc-container");
    if (tocToggleButton && tocContainer) {
      tocContainer.style.display = "none";
      tocToggleButton.setAttribute("aria-expanded", "false");
      tocToggleButton.addEventListener("click", function() {
        const isExpanded = tocToggleButton.getAttribute("aria-expanded") === "true";
        tocToggleButton.setAttribute("aria-expanded", String(!isExpanded));
        if (isExpanded) {
          tocContainer.style.display = "none";
          tocContainer.classList.remove("is-active");
        } else {
          tocContainer.style.display = "block";
          tocContainer.classList.add("is-active");
        }
      });
    }
  });
})();
