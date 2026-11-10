(() => {
    const card = document.querySelector(".literary-analysis-card");
    const toggle = document.querySelector(".literary-analysis-width-toggle");

    if (!card || !toggle) {
        return;
    }

    const preferenceKey = "relac-literary-analysis-full-width";

    const renderWidth = (fullWidth) => {
        card.classList.toggle("full-width-prose", fullWidth);
        toggle.setAttribute("aria-pressed", String(fullWidth));
        toggle.title = fullWidth ? "Switch to reading-width text" : "Switch to full-width text";
    };

    let fullWidth = false;
    try {
        fullWidth = localStorage.getItem(preferenceKey) === "true";
    } catch {
    }

    renderWidth(fullWidth);

    toggle.addEventListener("click", () => {
        fullWidth = !fullWidth;
        renderWidth(fullWidth);

        try {
            localStorage.setItem(preferenceKey, String(fullWidth));
        } catch {
        }
    });
})();
