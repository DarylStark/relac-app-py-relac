(() => {
    const toggle = document.querySelector(".literary-analysis-menu-toggle");

    if (!toggle) {
        return;
    }

    const layout = toggle.closest(".literary-analysis-layout");
    const menuCard = toggle.closest(".literary-analysis-menu-card");
    const currentTitle = menuCard?.querySelector(".literary-analysis-menu-current");
    const icon = toggle.querySelector(".literary-analysis-menu-toggle-icon");
    const label = toggle.querySelector(".literary-analysis-menu-toggle-label");

    if (!layout || !menuCard || !currentTitle || !icon || !label) {
        return;
    }

    const mobileLayout = window.matchMedia("(max-width: 760px)");

    const renderMenu = (collapsed) => {
        layout.classList.toggle("menu-collapsed", collapsed);
        const action = collapsed ? "Expand" : "Collapse";
        const accessibleLabel = `${action} work pages menu`;

        toggle.setAttribute("aria-expanded", String(!collapsed));
        toggle.setAttribute("aria-label", accessibleLabel);
        toggle.title = accessibleLabel;
        label.textContent = accessibleLabel;
        icon.textContent = collapsed ? "+" : "-";
    };

    renderMenu(mobileLayout.matches);

    const expandFromTitle = () => {
        if (layout.classList.contains("menu-collapsed")) {
            renderMenu(false);
            toggle.focus();
        }
    };

    toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        renderMenu(!layout.classList.contains("menu-collapsed"));
    });

    currentTitle.addEventListener("click", expandFromTitle);

    currentTitle.addEventListener("keydown", (event) => {
        if (
            layout.classList.contains("menu-collapsed")
            && (event.key === "Enter" || event.key === " ")
        ) {
            event.preventDefault();
            expandFromTitle();
        }
    });

    menuCard.addEventListener("click", () => {
        if (
            layout.classList.contains("menu-collapsed")
            && currentTitle.getClientRects().length > 0
        ) {
            expandFromTitle();
        }
    });
})();
