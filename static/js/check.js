document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("stars");
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  let stars = [];

  for (let i = 0; i < 250; i++) {
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.5,
      d: Math.random() * 0.5,
    });
  }

  function drawStars() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "white";
    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2, false);
      ctx.fill();
    }
    updateStars();
    requestAnimationFrame(drawStars);
  }

  function updateStars() {
    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      s.y += s.d;
      if (s.y > canvas.height) {
        s.y = 0;
        s.x = Math.random() * canvas.width;
      }
    }
  }

  drawStars();
});


function openPopup(id) {
  document.getElementById(id).style.display = 'flex';
}

function closePopup(id) {
  document.getElementById(id).style.display = 'none';
}

// Закрытие по клику вне попапа
document.querySelectorAll('.popup-overlay').forEach(overlay => {
  overlay.addEventListener('click', function(e) {
    if (e.target === this) this.style.display = 'none';
  });
});


const translations = {
  ru: {
   header_about: "О софте",
    header_risks: "Виды риска",
    header_signals: "Сигналы",
    header_instruction: "Инструкция",
    header_profile: "Профиль",
    header_register: "Зарегистрироваться",
    register_title: "Зарегистрируйтесь на PocketOption",
    register_subtitle: "чтобы мы могли связать ваш аккаунт с системой",
    check_title: "Проверка трейдер ID",
    placeholder_trader_id: "Введите ваш Trader ID",
    btn_continue: "Продолжить",
    btn_register_pocket: "Зарегистрироваться на PocketOption",
    why_register: "Для чего нужно зарегистрироваться",
    where_trader_id: "Где найти Trader ID",
    popup_why_title: "Почему нужно зарегистрироваться",
    popup_why_text: "Регистрация на PocketOption позволяет системе связать сигналы с вашим трейдерским аккаунтом, отслеживать вашу активность и начислять бонусы за активную торговлю.",
    popup_where_title: "Где найти ваш Trader ID",
    popup_where_text: "Зайдите в личный кабинет PocketOption, откройте раздел «Профиль». Там вы увидите ваш уникальный Trader ID — он состоит из цифр и букв."
  },
  en: {

   header_about: "About",
    header_risks: "Risk Types",
    header_signals: "Signals",
    header_instruction: "Instruction",
    header_profile: "Profile",
    header_register: "Register",
    register_title: "Register on PocketOption",
    register_subtitle: "so we can link your account with the system",
    check_title: "Trader ID Verification",
    placeholder_trader_id: "Enter your Trader ID",
    btn_continue: "Continue",
    btn_register_pocket: "Register on PocketOption",
    why_register: "Why should I register?",
    where_trader_id: "Where to find Trader ID?",
    popup_why_title: "Why register?",
    popup_why_text: "Registration on PocketOption links signals with your account, tracks your activity, and allows for bonuses for active trading.",
    popup_where_title: "Where to find Trader ID",
    popup_where_text: "Go to your PocketOption account profile. There you will find your unique Trader ID consisting of letters and numbers."
  },
  ua: {
  header_about: "Про софт",
    header_risks: "Види ризику",
    header_signals: "Сигнали",
    header_instruction: "Інструкція",
    header_profile: "Профіль",
    header_register: "Зареєструватися",
    register_title: "Зареєструйтеся на PocketOption",
    register_subtitle: "щоб ми могли пов’язати ваш акаунт із системою",
    check_title: "Перевірка трейдер ID",
    placeholder_trader_id: "Введіть ваш Trader ID",
    btn_continue: "Продовжити",
    btn_register_pocket: "Зареєструватися на PocketOption",
    why_register: "Навіщо реєструватися",
    where_trader_id: "Де знайти Trader ID",
    popup_why_title: "Навіщо реєструватися",
    popup_why_text: "Реєстрація на PocketOption дозволяє системі пов’язати сигнали з вашим акаунтом, відстежувати активність і нараховувати бонуси за торгівлю.",
    popup_where_title: "Де знайти Trader ID",
    popup_where_text: "Увійдіть до кабінету PocketOption, відкрийте розділ «Профіль». Там ви побачите свій унікальний Trader ID."
  }
};

function applyTranslations(lang) {
  const t = translations[lang];
  if (!t) return;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.textContent = t[key];
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (t[key]) el.placeholder = t[key];
  });
}

function setLanguage(lang) {
  localStorage.setItem('language', lang);
  applyTranslations(lang);
  document.querySelectorAll('.lang-icon').forEach(icon => {
    icon.classList.toggle('active', icon.dataset.lang === lang);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const lang = localStorage.getItem('language') || 'ru';
  applyTranslations(lang);
  setLanguage(lang);

  document.querySelectorAll('.lang-icon').forEach(icon => {
    icon.addEventListener('click', () => {
      setLanguage(icon.dataset.lang);
    });
  });
});
