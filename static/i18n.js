const translations = {
    'ru': {
        'nav_chats': 'Сообщения',
        'nav_settings': 'Настройки',
        'nav_logout': 'Выйти',
        'search_placeholder': 'Найти контакт...',
        'search_results': 'Результаты поиска',
        'your_chats': 'Ваши чаты',
        'no_chats': 'У вас пока нет активных чатов',
        'no_chats_desc': 'Используйте поиск сверху, чтобы найти собеседника.',
        'user_not_found': 'Пользователь не найден.',
        'typing': 'печатает',
        'send_placeholder': 'Ваше сообщение или Ctrl+V...',
        'profile_title': 'Профиль пользователя',
        'profile_bio_empty': 'Описание профиля отсутствует',
        'write_message': 'Написать сообщение',
        'back': 'Назад',
        'save_changes': 'Сохранить изменения',
        'username_label': 'Имя пользователя',
        'bio_label': 'О себе (Bio)',
        'theme_label': 'Выберите тему оформления',
        'avatar_label': 'Изменить аватар',
        'video_label': 'Видео в профиле (MP4/WebM)',
        'theme_dark': 'Темная',
        'theme_midnight': 'Midnight',
        'theme_light': 'Светлая',
        'photo': 'Фотография',
        'video': 'Видео',
        'login': 'Вход',
        'register': 'Регистрация',
        'username': 'Имя пользователя',
        'password': 'Пароль',
        'no_account': 'Нет аккаунта?',
        'have_account': 'Уже есть аккаунт?',
        'register_link': 'Зарегистрироваться',
        'login_link': 'Войти',
        'delete_chat': 'Удалить чат',
        'delete_me': 'Удалить у себя',
        'delete_both': 'Удалить у всех'
    },
    'en': {
        'nav_chats': 'Messages',
        'nav_settings': 'Settings',
        'nav_logout': 'Logout',
        'search_placeholder': 'Find contact...',
        'search_results': 'Search Results',
        'your_chats': 'Your Chats',
        'no_chats': 'No active chats yet',
        'no_chats_desc': 'Use the search bar above to find someone.',
        'user_not_found': 'User not found.',
        'typing': 'is typing',
        'send_placeholder': 'Your message or Ctrl+V...',
        'profile_title': 'User Profile',
        'profile_bio_empty': 'No bio available',
        'write_message': 'Send Message',
        'back': 'Back',
        'save_changes': 'Save Changes',
        'username_label': 'Username',
        'bio_label': 'About Me (Bio)',
        'theme_label': 'Select Theme',
        'avatar_label': 'Change Avatar',
        'video_label': 'Profile Video (MP4/WebM)',
        'theme_dark': 'Dark',
        'theme_midnight': 'Midnight',
        'theme_light': 'Light',
        'photo': 'Photo',
        'video': 'Video',
        'login': 'Login',
        'register': 'Register',
        'username': 'Username',
        'password': 'Password',
        'no_account': 'Don\'t have an account?',
        'have_account': 'Already have an account?',
        'register_link': 'Register',
        'login_link': 'Login',
        'delete_chat': 'Delete Chat',
        'delete_me': 'Delete for me',
        'delete_both': 'Delete for everyone'
    },
    'sr': {
        'nav_chats': 'Поруке',
        'nav_settings': 'Подешавања',
        'nav_logout': 'Одјава',
        'search_placeholder': 'Пронађи контакт...',
        'search_results': 'Резултати претраге',
        'your_chats': 'Ваши ћаскања',
        'no_chats': 'Још увек нема активних ћаскања',
        'no_chats_desc': 'Користите претрагу изнад да пронађете некога.',
        'user_not_found': 'Корисник није пронађен.',
        'typing': 'куца',
        'send_placeholder': 'Ваша порука или Ctrl+V...',
        'profile_title': 'Кориснички профил',
        'profile_bio_empty': 'Опис профила није доступан',
        'write_message': 'Пошаљи поруку',
        'back': 'Назад',
        'save_changes': 'Сачувај измене',
        'username_label': 'Корисничко име',
        'bio_label': 'О мени (Bio)',
        'theme_label': 'Изаберите тему',
        'avatar_label': 'Промени аватара',
        'video_label': 'Видео на профилу (MP4/WebM)',
        'theme_dark': 'Тамна',
        'theme_midnight': 'Миднигхт',
        'theme_light': 'Светла',
        'photo': 'Фотографија',
        'video': 'Видео',
        'login': 'Пријава',
        'register': 'Регистрација',
        'username': 'Корисничко име',
        'password': 'Лозинка',
        'no_account': 'Немате налог?',
        'have_account': 'Већ имате налог?',
        'register_link': 'Региструјте се',
        'login_link': 'Пријавите се',
        'delete_chat': 'Избриши ћаскање',
        'delete_me': 'Избриши за мене',
        'delete_both': 'Избриши за све'
    }
};

function applyLanguage(lang) {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = translations[lang][key];
            } else {
                el.innerText = translations[lang][key];
            }
        }
    });
    localStorage.setItem('nebula_lang', lang);
}

document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('nebula_lang') || 'ru';
    const langSelect = document.getElementById('lang-select');
    if (langSelect) {
        langSelect.value = savedLang;
        langSelect.addEventListener('change', (e) => applyLanguage(e.target.value));
    }
    applyLanguage(savedLang);
});
