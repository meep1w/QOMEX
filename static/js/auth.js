document.addEventListener("DOMContentLoaded", () => {
  // --- DOM ---
  const container = document.querySelector(".container");
  const form = document.getElementById("auth-form");
  const errorBox = document.getElementById("error-message");
  const actionInput = document.getElementById("action-input");
  const formTitle = document.getElementById("form-title");
  const submitBtn = document.getElementById("submit-btn");
  const switchLink = document.getElementById("switch-link");
  const passwordInput = document.getElementById("password");
  const passwordStrength = document.getElementById("password-strength");
  const headerTitle = document.getElementById("header-title");
  const headerSubtitle = document.getElementById("header-subtitle");

  // Reset password popup
  const forgotPasswordLink = document.getElementById("forgot-password-link");
  const passwordResetPopup = document.getElementById("passwordResetPopup");
  const closeResetPopupBtn = document.getElementById("closeResetPopup");
  const passwordResetForm = document.getElementById("password-reset-form");
  const resetMessage = document.getElementById("reset-message");

  // Language
  const langIcons = document.querySelectorAll(".lang-icon");

  // --- i18n ---
  const translations = {
    ru: {
      header_about: "О софте",
      header_risks: "Виды риска",
      header_signals: "Сигналы",
      header_instruction: "Инструкция",
      header_profile: "Профиль",
      header_register: "Зарегистрироваться",

      auth_register_title: "Зарегистрируйте аккаунт на QOMEX",
      auth_register_subtitle: "Чтобы начать пользоваться лучшим инструментом для трейдинга",
      auth_login_title: "Войдите в свой аккаунт",
      auth_login_subtitle: "С возвращением!",

      auth_register: "Регистрация",
      auth_login: "Логин",
      auth_email: "Email",
      auth_password: "Пароль",
      auth_password_strength: "Сложность пароля:",
      auth_remember: "Запомнить меня",
      auth_forgot_password: "Забыли пароль?",
      auth_create_account: "Создать аккаунт",
      auth_switch_login: "Есть аккаунт? Войдите",
      auth_switch_register: "Нет аккаунта? Зарегистрируйтесь",

      auth_reset_title: "Сбросить пароль",
      auth_reset_instruction: "Введите ваш email для получения ссылки на сброс пароля.",
      auth_reset_send: "Отправить ссылку",

      auth_login_placeholder: "Введите логин",
      auth_email_placeholder: "Введите email",
      auth_password_placeholder: "Введите пароль",

      auth_reset_success: "Если email существует, ссылка для сброса отправлена.",
      auth_reset_error: "Ошибка при отправке.",
      auth_server_error: "Ошибка сервера. Попробуйте позже.",

      password_strength: {
        veryWeak: "Очень слабый",
        weak: "Слабый",
        medium: "Средний",
        good: "Хороший",
        excellent: "Отличный"
      }
    },
    en: {
      header_about: "About",
      header_risks: "Risks",
      header_signals: "Signals",
      header_instruction: "Instruction",
      header_profile: "Profile",
      header_register: "Register",

      auth_register_title: "Register an account on QOMEX",
      auth_register_subtitle: "To start using the best trading tool",
      auth_login_title: "Log into your account",
      auth_login_subtitle: "Welcome back!",

      auth_register: "Register",
      auth_login: "Login",
      auth_email: "Email",
      auth_password: "Password",
      auth_password_strength: "Password strength:",
      auth_remember: "Remember me",
      auth_forgot_password: "Forgot password?",
      auth_create_account: "Create account",
      auth_switch_login: "Have an account? Log in",
      auth_switch_register: "No account? Register",

      auth_reset_title: "Reset password",
      auth_reset_instruction: "Enter your email to receive a reset link.",
      auth_reset_send: "Send link",

      auth_login_placeholder: "Enter login",
      auth_email_placeholder: "Enter email",
      auth_password_placeholder: "Enter password",

      auth_reset_success: "If the email exists, a reset link has been sent.",
      auth_reset_error: "Error sending link.",
      auth_server_error: "Server error. Try again later.",

      password_strength: {
        veryWeak: "Very weak",
        weak: "Weak",
        medium: "Medium",
        good: "Good",
        excellent: "Excellent"
      }
    },
    ua: {
      header_about: "Про софт",
      header_risks: "Види ризику",
      header_signals: "Сигнали",
      header_instruction: "Інструкція",
      header_profile: "Профіль",
      header_register: "Реєстрація",

      auth_register_title: "Зареєструйте акаунт на QOMEX",
      auth_register_subtitle: "Щоб почати користуватися найкращим інструментом для трейдингу",
      auth_login_title: "Увійдіть у свій акаунт",
      auth_login_subtitle: "З поверненням!",

      auth_register: "Реєстрація",
      auth_login: "Логін",
      auth_email: "Email",
      auth_password: "Пароль",
      auth_password_strength: "Складність пароля:",
      auth_remember: "Запам'ятати мене",
      auth_forgot_password: "Забули пароль?",
      auth_create_account: "Створити акаунт",
      auth_switch_login: "Є акаунт? Увійти",
      auth_switch_register: "Немає акаунту? Зареєструйтесь",

      auth_reset_title: "Скинути пароль",
      auth_reset_instruction: "Введіть email для отримання посилання.",
      auth_reset_send: "Надіслати посилання",

      auth_login_placeholder: "Введіть логін",
      auth_email_placeholder: "Введіть email",
      auth_password_placeholder: "Введіть пароль",

      auth_reset_success: "Якщо email існує, посилання надіслано.",
      auth_reset_error: "Помилка під час надсилання.",
      auth_server_error: "Помилка сервера. Спробуйте пізніше.",

      password_strength: {
        veryWeak: "Дуже слабкий",
        weak: "Слабкий",
        medium: "Середній",
        good: "Хороший",
        excellent: "Відмінний"
      }
    }
  };

  let currentLang = localStorage.getItem("lang") || "ru";
  if (!translations[currentLang]) currentLang = "ru";
  const t = translations[currentLang];

  // Активная иконка языка + переключение
  if (langIcons && langIcons.length) {
    langIcons.forEach(icon => {
      icon.classList.toggle("active", icon.dataset.lang === currentLang);
      icon.addEventListener("click", () => {
        const selected = icon.dataset.lang;
        if (selected && translations[selected]) {
          localStorage.setItem("lang", selected);
          location.reload();
        }
      });
    });
  }

  // Применение переводов
  function translatePage() {
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (t[key]) el.textContent = t[key];
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (t[key]) el.setAttribute("placeholder", t[key]);
    });

    if (formTitle && actionInput) {
      formTitle.textContent = actionInput.value === "register" ? t.auth_register : t.auth_login;
    }
    if (submitBtn && actionInput) {
      submitBtn.textContent = actionInput.value === "register" ? t.auth_create_account : t.auth_login;
    }
    if (switchLink && actionInput) {
      switchLink.textContent = actionInput.value === "register" ? t.auth_switch_login : t.auth_switch_register;
    }
    if (headerTitle && actionInput) {
      headerTitle.textContent = actionInput.value === "register" ? t.auth_register_title : t.auth_login_title;
    }
    if (headerSubtitle && actionInput) {
      headerSubtitle.textContent = actionInput.value === "register" ? t.auth_register_subtitle : t.auth_login_subtitle;
    }
    if (passwordStrength) {
      passwordStrength.textContent = `${t.auth_password_strength} ${t.password_strength.veryWeak}`;
      passwordStrength.style.color = "#888";
    }
  }

  translatePage();

  // Индикатор сложности пароля
  if (passwordInput && passwordStrength) {
    passwordInput.addEventListener("input", () => {
      const val = passwordInput.value || "";
      let score = 0;
      if (val.length >= 8) score++;
      if (val.length >= 12) score++;
      if (/\d/.test(val)) score++;
      if (/[a-z]/.test(val)) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;

      const levels = t.password_strength;
      let label = levels.veryWeak, color = "#888";

      if (score <= 2) { label = levels.veryWeak; color = "red"; }
      else if (score === 3) { label = levels.weak; color = "orange"; }
      else if (score === 4) { label = levels.medium; color = "goldenrod"; }
      else if (score === 5) { label = levels.good; color = "green"; }
      else if (score >= 6) { label = levels.excellent; color = "darkgreen"; }

      passwordStrength.textContent = `${t.auth_password_strength} ${label}`;
      passwordStrength.style.color = color;
    });
  }

  // Переключение: регистрация <-> вход
  if (switchLink && actionInput && form) {
    switchLink.addEventListener("click", (e) => {
      e.preventDefault();
      actionInput.value = actionInput.value === "register" ? "login" : "register";
      form.reset();
      if (errorBox) errorBox.style.display = "none";
      if (passwordStrength) {
        passwordStrength.textContent = `${t.auth_password_strength} ${t.password_strength.veryWeak}`;
        passwordStrength.style.color = "#888";
      }
      translatePage();
    });
  }

  // Сабмит формы /auth
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (errorBox) {
        errorBox.style.display = "none";
        errorBox.textContent = "";
      }

      const formData = new FormData(form);
      const remember = document.getElementById("remember")?.checked;
      if (typeof remember === "boolean") {
        formData.set("remember", remember ? "true" : "false");
      }

      try {
        const res = await fetch("/auth", { method: "POST", body: formData });
        const data = await res.json().catch(() => ({}));

        // успех только если success===true
        const ok = data.success === true || data.ok === true;

        if (ok) {
          window.location.href = "/";
        } else {
          if (errorBox) {
            errorBox.style.display = "block";
            errorBox.textContent = data.message || data.detail || t.auth_server_error;
          }
        }
      } catch {
        if (errorBox) {
          errorBox.style.display = "block";
          errorBox.textContent = t.auth_server_error;
        }
      }
    });
  }

  // --- Forgot Password popup ---
  if (forgotPasswordLink && passwordResetPopup && closeResetPopupBtn) {
    forgotPasswordLink.addEventListener("click", (e) => {
      e.preventDefault();
      if (resetMessage) resetMessage.textContent = "";
      passwordResetPopup.style.display = "flex";
    });

    closeResetPopupBtn.addEventListener("click", () => {
      passwordResetPopup.style.display = "none";
    });

    // закрытие по клику на фон
    passwordResetPopup.addEventListener("click", (e) => {
      if (e.target === passwordResetPopup) {
        passwordResetPopup.style.display = "none";
      }
    });
  }

  if (passwordResetForm) {
    passwordResetForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (resetMessage) resetMessage.textContent = "";
      const emailEl = document.getElementById("reset-email");
      const email = (emailEl?.value || "").trim();

      try {
        const res = await fetch("/password-reset-request", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });

        const data = await res.json().catch(() => ({}));
        const ok = data.ok === true || data.success === true;

        if (resetMessage) {
          resetMessage.style.color = ok ? "green" : "red";
          resetMessage.textContent = ok
            ? (t.auth_reset_success || "Если email существует, ссылка для сброса отправлена.")
            : (data.message || data.detail || t.auth_reset_error);
        }

        if (ok) {
          setTimeout(() => { passwordResetPopup.style.display = "none"; }, 2000);
        }
      } catch {
        if (resetMessage) {
          resetMessage.style.color = "red";
          resetMessage.textContent = t.auth_server_error;
        }
      }
    });
  }

  // --- Stars background ---
  const canvas = document.getElementById("stars");
  if (canvas && canvas.getContext) {
    const ctx = canvas.getContext("2d");
    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    const stars = [];
    const COUNT = 250;
    for (let i = 0; i < COUNT; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.5,
        d: Math.random() * 0.5 + 0.1
      });
    }

    function drawStars() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "white";
      for (let s of stars) {
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
      }
      updateStars();
      requestAnimationFrame(drawStars);
    }

    function updateStars() {
      for (let s of stars) {
        s.y += s.d;
        if (s.y > canvas.height) {
          s.y = 0;
          s.x = Math.random() * canvas.width;
        }
      }
    }

    drawStars();
  }
});
