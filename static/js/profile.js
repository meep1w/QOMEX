
document.addEventListener("DOMContentLoaded", () => {
    // === Переключение вкладок ===
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.tab;
            tabButtons.forEach((b) => b.classList.remove("active"));
            tabContents.forEach((c) => c.classList.remove("active"));
            btn.classList.add("active");
            const tab = document.getElementById(target);
            if (tab) tab.classList.add("active");
        });
    });

    // === Анимация звёзд ===
    const canvas = document.getElementById("stars");
    if (canvas) {
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

    // === Перевод ===
    const icons = document.querySelectorAll(".lang-icon");

    const translations = {
        ru: {
            header_profile: "Профиль",
            header_about: "О софте",
            header_risks: "Виды риска",
            header_signals: "Сигналы",
            header_instruction: "Инструкция",
            welcome: "Добро пожаловать,",
            logout: "Выход",
            dashboard: "Дашборд",
            reset: "Сброс пароля",
            referral: "Реф. система",
            your_login: "Ваш логин",
            your_email: "Ваша почта",
            your_trader_id: "Ваш трейдер ID",
            personal_phone: "Личный номер телефона (необязательно)",
            work_phone: "Рабочий номер телефона (необязательно)",
            country_city: "Страна, город (необязательно)",
            save_btn: "Сохранить изменения",
            reset_text: "Чтобы изменить пароль, отправьте запрос на ваш email.Вы получите ссылку для сброса пароля.",
            send_link: "Отправить ссылку",
            referral_soon: "Скоро"
        },
        en: {
            header_profile: "Profile",
            header_about: "About",
            header_risks: "Risk Types",
            header_signals: "Signals",
            header_instruction: "Instruction",
            welcome: "Welcome,",
            logout: "Log out",
            dashboard: "Dashboard",
            reset: "Reset Password",
            referral: "Ref. System",
            your_login: "Your login",
            your_email: "Your email",
            your_trader_id: "Your trader ID",
            personal_phone: "Personal phone (optional)",
            work_phone: "Work phone (optional)",
            country_city: "Country, City (optional)",
            save_btn: "Save data",
            reset_text: "To change your password, send a request to your email.You will receive a reset link.",
            send_link: "Send link",
            referral_soon: "Coming soon"
        },
        ua: {
            header_profile: "Профіль",
            header_about: "Про софт",
            header_risks: "Типи ризиків",
            header_signals: "Сигнали",
            header_instruction: "Інструкція",
            welcome: "Ласкаво просимо,",
            logout: "Вийти",
            dashboard: "Дашборд",
            reset: "Скинути пароль",
            referral: "Реф. система",
            your_login: "Ваш логін",
            your_email: "Ваша пошта",
            your_trader_id: "Ваш трейдер ID",
            personal_phone: "Особистий номер (необов'язково)",
            work_phone: "Робочий номер (необов'язково)",
            country_city: "Країна, місто (необов'язково)",
            save_btn: "Зберегти дані",
            reset_text: "Щоб змінити пароль, надішліть запит на вашу пошту.Ви отримаєте посилання для скидання.",
            send_link: "Надіслати посилання",
            referral_soon: "Скоро"
        }
    };

    function setLanguage(lang) {
        icons.forEach((icon) => {
            icon.classList.toggle("active", icon.dataset.lang === lang);
        });
        localStorage.setItem("language", lang);
        applyTranslations(lang);
    }

    const savedLang = localStorage.getItem("language") || "ru";
    setLanguage(savedLang);

    icons.forEach((icon) => {
        icon.addEventListener("click", () => {
            setLanguage(icon.dataset.lang);
            location.reload();
        });
    });

    function applyTranslations(lang) {
        const elements = document.querySelectorAll("[data-i18n]");
        elements.forEach((el) => {
            const key = el.getAttribute("data-i18n");
            if (translations[lang] && translations[lang][key]) {
                el.innerText = translations[lang][key];
            }
        });
    }

    applyTranslations(savedLang);

    // === Сохранение данных профиля ===
// === Сохранение данных профиля ===
    const form = document.getElementById("profile-form");
    if (form) {
        const personal = document.getElementById("phone-personal");
        const work     = document.getElementById("phone-work");
        const location = document.getElementById("location");
        const saveBtn  = form.querySelector("button.save-btn");

        personal.value = localStorage.getItem("phone_personal") || "";
        work.value     = localStorage.getItem("phone_work") || "";
        location.value = localStorage.getItem("location") || "";

        const setBtn = (mode, text) => {
            saveBtn.classList.remove("is-loading","is-success","is-error");
            if (mode) saveBtn.classList.add(mode);
            if (text) saveBtn.textContent = text;
        };
        const revertBtn = () => {
            const lang = localStorage.getItem("language") || "ru";
            const dict = {ru:"Сохранить изменения", en:"Save data", ua:"Зберегти дані"};
            setBtn(null, dict[lang] || "Сохранить изменения");
        };

        form.addEventListener("submit", (e) => {
            e.preventDefault();
            setBtn("is-loading","Сохраняем…");

            // Сохраняем локально
            localStorage.setItem("phone_personal", personal.value.trim());
            localStorage.setItem("phone_work",     work.value.trim());
            localStorage.setItem("location",       location.value.trim());

            setTimeout(() => {
                setBtn("is-success","Изменения сохранены");
                setTimeout(revertBtn, 1800);
            }, 400);
        });
    }


    // === Бургер-меню ===
    const burger = document.getElementById("burger-button");
    const overlay = document.querySelector(".mobile-overlay");
    const mobileMenu = document.querySelector(".mobile-menu");

    if (burger && overlay && mobileMenu) {
        burger.addEventListener("click", () => {
            overlay.classList.toggle("active");
        });

        const links = mobileMenu.querySelectorAll("a");
        links.forEach(link => {
            link.addEventListener("click", () => {
                overlay.classList.remove("active");
            });
        });

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                overlay.classList.remove("active");
            }
        });
    }
});

let lastScrollTop = 0;
const header = document.querySelector("header");

window.addEventListener("scroll", () => {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;

    if (scrollTop > lastScrollTop && scrollTop > 50) {
        // Скролл вниз — скрыть хедер
        header.classList.add("header--hidden");
    } else {
        // Скролл вверх — показать хедер
        header.classList.remove("header--hidden");
    }

    lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
});

