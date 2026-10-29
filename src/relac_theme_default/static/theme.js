(() => {
    const root = document.documentElement;
    const toggle = document.querySelector(".theme-toggle");

    if (!toggle) {
        return;
    }

    const icon = toggle.querySelector(".theme-toggle-icon");

    const renderTheme = (theme) => {
        const isDark = theme === "dark";
        const nextTheme = isDark ? "light" : "dark";

        root.classList.toggle("dark", isDark);
        root.classList.toggle("light", !isDark);
        icon.textContent = isDark ? "\u263c" : "\u263e";
        toggle.setAttribute("aria-label", `Switch to ${nextTheme} theme`);
        toggle.setAttribute("title", `Switch to ${nextTheme} theme`);
    };

    renderTheme(root.classList.contains("light") ? "light" : "dark");

    toggle.addEventListener("click", () => {
        const theme = root.classList.contains("dark") ? "light" : "dark";
        renderTheme(theme);

        try {
            localStorage.setItem("relac-theme", theme);
        } catch {
        }
    });
})();
