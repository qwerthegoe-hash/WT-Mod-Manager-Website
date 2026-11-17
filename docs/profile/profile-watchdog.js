"use strict";
// Module imports can fail before profile.js gets to run (offline/CDN failure).
      // Keep a visible diagnostic instead of an endless loading screen.
      window.addEventListener("DOMContentLoaded", () => {
        window.setTimeout(() => {
          const heading = document.getElementById("userProfileTitle");
          if (heading && heading.textContent.trim() === "Загрузка...") {
            heading.textContent = "Профиль временно недоступен";
            const notice = document.getElementById("profileNotice");
            if (notice) {
              notice.textContent = "Не удалось запустить профиль. Проверь соединение, открой консоль браузера (F12) и обнови страницу.";
              notice.classList.add("error");
            }
          }
        }, 15000);
      });
