document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("darkModeToggle");
  const body = document.body;
  const sidebar = document.querySelector(".sidebar");
  const content = document.querySelector(".content-area");
  const footer = document.querySelector("footer");

  // Função para aplicar dark mode
  function enableDarkMode() {
    body.classList.add("dark-mode");

    if (sidebar) {
      sidebar.classList.add("bg-dark", "text-white");
      sidebar.classList.remove("bg-teal-700");
    }

    if (content) {
      content.classList.add("bg-dark", "text-white");
      content.classList.remove("bg-light", "text-dark");
    }

    if (footer) {
      footer.classList.add("bg-dark", "text-white");
      footer.classList.remove("bg-light", "text-dark");
    }

    if (toggle) toggle.textContent = "☀️ Modo Claro";
    localStorage.setItem("darkMode", "true");
  }

  // Função para remover dark mode
  function disableDarkMode() {
    body.classList.remove("dark-mode");

    if (sidebar) {
      sidebar.classList.remove("bg-dark", "text-white");
      sidebar.classList.add("bg-teal-700");
    }

    if (content) {
      content.classList.remove("bg-dark", "text-white");
      content.classList.add("bg-light", "text-dark");
    }

    if (footer) {
      footer.classList.remove("bg-dark", "text-white");
      footer.classList.add("bg-light", "text-dark");
    }

    if (toggle) toggle.textContent = "🌙 Modo Escuro";
    localStorage.setItem("darkMode", "false");
  }

  // Aplica dark mode se estiver salvo no localStorage
  if (localStorage.getItem("darkMode") === "true") {
    enableDarkMode();
  }

  // Evento do botão
  if (toggle) {
    toggle.addEventListener("click", function () {
      if (body.classList.contains("dark-mode")) {
        disableDarkMode();
      } else {
        enableDarkMode();
      }
    });
  }
});
