document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((flash) => {
    const dismiss = () => {
      flash.classList.add("leaving");
      window.setTimeout(() => flash.remove(), 260);
    };
    flash.querySelector(".flash-close")?.addEventListener("click", dismiss);
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

  const rows = [...document.querySelectorAll("[data-product-row]")];
  const search = document.querySelector("[data-product-search]");
  const filters = [...document.querySelectorAll("[data-filter]")];
  const noResults = document.querySelector("[data-no-results]");
  let activeFilter = "all";

  const applyFilters = () => {
    const term = search?.value.trim().toLowerCase() || "";
    let visible = 0;
    rows.forEach((row) => {
      const stateMatches = activeFilter === "all" || row.dataset.status === activeFilter;
      const textMatches = (row.dataset.search || "").includes(term);
      row.hidden = !(stateMatches && textMatches);
      if (!row.hidden) visible += 1;
    });
    if (noResults) noResults.hidden = visible !== 0;
  };

  search?.addEventListener("input", applyFilters);
  filters.forEach((button) => button.addEventListener("click", () => {
    filters.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    activeFilter = button.dataset.filter;
    applyFilters();
  }));

  const catalogSearch = document.querySelector("[data-catalog-search]");
  const catalogItems = [...document.querySelectorAll("[data-catalog-item]")];
  const catalogEmpty = document.querySelector("[data-catalog-empty]");
  catalogSearch?.addEventListener("input", () => {
    const term = catalogSearch.value.trim().toLowerCase();
    let visible = 0;
    catalogItems.forEach((item) => {
      item.hidden = !(item.dataset.search || "").includes(term);
      if (!item.hidden) visible += 1;
    });
    if (catalogEmpty) catalogEmpty.hidden = visible !== 0;
  });
});
