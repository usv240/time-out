const themeOrder = ["light", "dark", "system"];
const nav = document.querySelector(".nav");
const navLinks = nav?.querySelector(".nav-links");

if (nav && navLinks) {
  if (!navLinks.id) navLinks.id = "page-nav-links";
  let actions = nav.querySelector(".nav-actions");
  if (!actions) {
    actions = document.createElement("div");
    actions.className = "nav-actions";
    nav.append(actions);
  }

  if (!actions.querySelector(".button")) {
    const tryLink = document.createElement("a");
    tryLink.className = "button button-small";
    tryLink.href = "/try";
    tryLink.textContent = "Try";
    actions.append(tryLink);
  }

  const themeButton = document.createElement("button");
  themeButton.className = "icon-button";
  themeButton.type = "button";
  themeButton.innerHTML = '<span aria-hidden="true">◐</span>';
  actions.append(themeButton);

  function currentTheme() { return localStorage.getItem("before-theme") || "light"; }
  function renderTheme(theme) {
    themeButton.setAttribute("aria-label", `Theme: ${theme}. Activate for next theme.`);
    themeButton.title = `Theme: ${theme}`;
    themeButton.querySelector("span").textContent = theme === "light" ? "☀" : theme === "dark" ? "☾" : "◐";
  }
  function setTheme(theme) {
    if (theme === "system") {
      document.documentElement.removeAttribute("data-theme");
      // Stored, not removed: an absent key now means light, not "follow the OS".
      localStorage.setItem("before-theme", "system");
    } else {
      document.documentElement.dataset.theme = theme;
      localStorage.setItem("before-theme", theme);
    }
    renderTheme(theme);
  }
  themeButton.addEventListener("click", () => setTheme(themeOrder[(themeOrder.indexOf(currentTheme()) + 1) % themeOrder.length]));
  renderTheme(currentTheme());

  const menuButton = document.createElement("button");
  menuButton.className = "icon-button menu-button";
  menuButton.type = "button";
  menuButton.setAttribute("aria-expanded", "false");
  menuButton.setAttribute("aria-controls", navLinks.id);
  menuButton.setAttribute("aria-label", "Open menu");
  menuButton.innerHTML = '<span aria-hidden="true">☰</span>';
  actions.append(menuButton);
  menuButton.addEventListener("click", () => {
    const open = menuButton.getAttribute("aria-expanded") !== "true";
    menuButton.setAttribute("aria-expanded", String(open));
    menuButton.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    navLinks.classList.toggle("is-open", open);
  });
  for (const link of navLinks.querySelectorAll("a")) {
    link.addEventListener("click", () => {
      menuButton.setAttribute("aria-expanded", "false");
      navLinks.classList.remove("is-open");
    });
  }
}
