(() => {
    const readToggle = document.querySelector(".literary-analysis-read-toggle");
    const readPageLinks = document.querySelectorAll(
        ".literary-analysis-menu [data-read-page-key]",
    );
    const readGroups = document.querySelectorAll(
        ".literary-analysis-menu [data-read-group-label]",
    );

    if (!readToggle && readPageLinks.length === 0 && readGroups.length === 0) {
        return;
    }

    const storageKey = (pageKey) => `relac-read-page:${pageKey}`;
    const feedback = document.querySelector(".literary-analysis-read-feedback");
    const svgNamespace = "http://www.w3.org/2000/svg";

    const isRead = (pageKey) => {
        try {
            return localStorage.getItem(storageKey(pageKey)) === "true";
        } catch {
            if (feedback) {
                feedback.textContent = "Reading status is unavailable in this browser.";
            }
            return false;
        }
    };

    const createReadIcon = (read) => {
        const svg = document.createElementNS(svgNamespace, "svg");
        svg.classList.add("literary-analysis-read-icon");
        svg.setAttribute("viewBox", "0 0 16 16");
        svg.setAttribute("aria-hidden", "true");

        const circle = document.createElementNS(svgNamespace, "circle");
        circle.setAttribute("cx", "8");
        circle.setAttribute("cy", "8");
        circle.setAttribute("r", "6");
        svg.append(circle);

        if (read) {
            const check = document.createElementNS(svgNamespace, "path");
            check.setAttribute("d", "m4.5 8.25 2.25 2.25 4.75-5");
            svg.append(check);
        }

        return svg;
    };

    const renderReadStatus = () => {
        for (const link of readPageLinks) {
            const read = isRead(link.dataset.readPageKey);
            const statusContainer = link.querySelector(
                ".literary-analysis-menu-meta",
            ) ?? link;
            let status = statusContainer.querySelector(
                ".literary-analysis-read-status",
            );

            if (!status) {
                status = document.createElement("span");
                status.className = "literary-analysis-read-status";
                status.setAttribute("role", "img");
                statusContainer.append(status);
            }

            status.dataset.read = String(read);
            status.setAttribute("aria-label", read ? "Read" : "Not read");
            status.title = read ? "Read" : "Not read";
            status.replaceChildren(createReadIcon(read));
        }

        for (const group of readGroups) {
            const details = group.closest("details");
            const groupLinks = details?.querySelectorAll(
                ".literary-analysis-submenu [data-read-page-key]",
            ) ?? [];
            const allRead = groupLinks.length > 0
                && [...groupLinks].every((link) => isRead(link.dataset.readPageKey));
            let status = group.querySelector(
                ".literary-analysis-read-group-status",
            );

            if (!status) {
                status = document.createElement("span");
                status.className = "literary-analysis-read-group-status";
                status.setAttribute("role", "img");
                group.append(status);
            }

            const description = allRead
                ? group.dataset.readGroupCompleteLabel
                : group.dataset.readGroupIncompleteLabel;
            status.dataset.read = String(allRead);
            status.setAttribute("aria-label", description);
            status.title = description;
            status.replaceChildren(createReadIcon(allRead));
        }

        if (readToggle) {
            const read = isRead(readToggle.dataset.readPageKey);
            readToggle.setAttribute("aria-pressed", String(read));
            readToggle.dataset.read = String(read);
            readToggle.querySelector(
                ".literary-analysis-read-toggle-icon",
            )?.replaceChildren(createReadIcon(read));
            const label = readToggle.querySelector(
                ".literary-analysis-read-toggle-label",
            );
            if (label) {
                label.textContent = read ? "Mark as unread" : "Mark as read";
            }
        }
    };

    renderReadStatus();

    readToggle?.addEventListener("click", () => {
        const pageKey = readToggle.dataset.readPageKey;
        const nextReadState = readToggle.getAttribute("aria-pressed") !== "true";

        try {
            if (nextReadState) {
                localStorage.setItem(storageKey(pageKey), "true");
            } else {
                localStorage.removeItem(storageKey(pageKey));
            }
        } catch {
            if (feedback) {
                feedback.textContent = "Could not save reading status in this browser.";
            }
            return;
        }

        if (feedback) {
            feedback.textContent = "";
        }
        renderReadStatus();
    });
})();
