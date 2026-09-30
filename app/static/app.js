document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((flash) => {
    const close = flash.querySelector(".flash-close");
    const dismiss = () => {
      flash.classList.add("leaving");
      window.setTimeout(() => flash.remove(), 260);
    };
    close?.addEventListener("click", dismiss);
    window.setTimeout(dismiss, 5200);
  });

  const passwordToggle = document.querySelector("[data-password-toggle]");
  const passwordInput = document.querySelector("#password");
  passwordToggle?.addEventListener("click", () => {
    const reveal = passwordInput.type === "password";
    passwordInput.type = reveal ? "text" : "password";
    passwordToggle.textContent = reveal ? "Ocultar" : "Ver";
    passwordToggle.setAttribute("aria-label", reveal ? "Ocultar contraseña" : "Mostrar contraseña");
  });

  const titleInput = document.querySelector("#title");
  const charCount = document.querySelector("[data-char-count]");
  const updateCount = () => {
    if (titleInput && charCount) charCount.textContent = titleInput.value.length;
  };
  titleInput?.addEventListener("input", updateCount);
  updateCount();

  const cards = [...document.querySelectorAll(".task-card")];
  cards.forEach((card, index) => card.style.setProperty("--delay", `${Math.min(index, 8) * 55}ms`));

  const search = document.querySelector("[data-task-search]");
  const filters = [...document.querySelectorAll("[data-filter]")];
  const noResults = document.querySelector("[data-no-results]");
  let activeFilter = "all";

  const applyFilters = () => {
    const term = search?.value.trim().toLowerCase() || "";
    let visible = 0;
    cards.forEach((card) => {
      const matchesState = activeFilter === "all" || card.dataset.status === activeFilter;
      const matchesText = (card.dataset.search || "").includes(term);
      const show = matchesState && matchesText;
      card.hidden = !show;
      if (show) visible += 1;
    });
    if (noResults) noResults.hidden = visible !== 0;
  };

  search?.addEventListener("input", applyFilters);
  filters.forEach((button) => {
    button.addEventListener("click", () => {
      filters.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      activeFilter = button.dataset.filter;
      applyFilters();
    });
  });
});
