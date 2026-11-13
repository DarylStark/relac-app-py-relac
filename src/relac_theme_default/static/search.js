(() => {
    const trigger = document.querySelector(".library-search-toggle");
    const dialog = document.querySelector(".library-search-dialog");
    const closeButton = document.querySelector(".library-search-close");
    const searchInput = document.querySelector(".library-search-input");
    const status = document.querySelector(".library-search-status");
    const results = document.querySelector(".library-search-results");

    if (!trigger || !dialog || !closeButton || !searchInput || !status || !results) {
        return;
    }

    let searchIndexPromise;
    let searchItems = [];

    const applePlatform = /Mac|iPhone|iPad/.test(navigator.platform);
    const modifierLabel = applePlatform ? "Cmd" : "Ctrl";
    trigger.title = `Search library (${modifierLabel}+Shift+O or /)`;
    trigger.setAttribute("aria-keyshortcuts", "Control+Shift+O Meta+Shift+O /");

    const normalize = (value) => value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase();

    const loadSearchIndex = () => {
        if (!searchIndexPromise) {
            searchIndexPromise = fetch(new URL("search-index.json", document.baseURI))
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`Search index request failed: ${response.status}`);
                    }
                    return response.json();
                })
                .then((index) => {
                    searchItems = Array.isArray(index.items) ? index.items : [];
                    renderResults();
                })
                .catch(() => {
                    searchIndexPromise = null;
                    status.textContent = "Search is currently unavailable.";
                });
        }

        return searchIndexPromise;
    };

    const createResult = (item) => {
        const listItem = document.createElement("li");
        listItem.className = "library-search-result-item";

        const link = document.createElement("a");
        link.className = "library-search-result";
        link.href = item.href;

        const main = document.createElement("span");
        main.className = "library-search-result-main";

        const title = document.createElement("span");
        title.className = "library-search-result-title";
        title.textContent = item.title;
        main.append(title);

        if (Array.isArray(item.details) && item.details.length > 0) {
            const details = document.createElement("span");
            details.className = "library-search-result-details";
            details.textContent = item.details.slice(0, 3).join(" · ");
            main.append(details);
        }

        const type = document.createElement("span");
        type.className = "library-search-result-type";
        type.textContent = item.type;
        link.append(type, main);
        listItem.append(link);
        return listItem;
    };

    const renderResults = () => {
        results.replaceChildren();
        const query = normalize(searchInput.value.trim());
        if (!query) {
            status.textContent = "";
            return;
        }

        const terms = query.split(/\s+/).filter(Boolean);
        const matches = searchItems
            .filter((item) => {
                const searchableText = normalize(item.searchText ?? "");
                return terms.every((term) => searchableText.includes(term));
            })
            .sort((left, right) => {
                const leftTitle = normalize(left.title ?? "");
                const rightTitle = normalize(right.title ?? "");
                const leftRank = leftTitle.startsWith(query) ? 0 : leftTitle.includes(query) ? 1 : 2;
                const rightRank = rightTitle.startsWith(query) ? 0 : rightTitle.includes(query) ? 1 : 2;
                return leftRank - rightRank || leftTitle.localeCompare(rightTitle);
            });
        const resultLimit = 50;
        matches.slice(0, resultLimit).forEach((item) => {
            results.append(createResult(item));
        });

        if (matches.length === 0) {
            status.textContent = "No results found.";
        } else if (matches.length > resultLimit) {
            status.textContent = `Showing the first ${resultLimit} results.`;
        } else {
            status.textContent = `${matches.length} ${matches.length === 1 ? "result" : "results"}`;
        }
    };

    const openSearch = () => {
        if (!dialog.open) {
            dialog.showModal();
            loadSearchIndex();
        }
        searchInput.focus();
    };

    trigger.addEventListener("click", openSearch);

    document.addEventListener("keydown", (event) => {
        const isChord = (event.ctrlKey || event.metaKey) && event.shiftKey &&
            !event.altKey && event.key.toLocaleLowerCase() === "o";
        const isSlash = event.key === "/" && !event.ctrlKey && !event.metaKey &&
            !event.altKey && !event.shiftKey &&
            !(event.target instanceof Element && event.target.closest(
                "input, textarea, select, [contenteditable='true']"
            ));

        if (!isChord && !isSlash) {
            return;
        }

        event.preventDefault();
        openSearch();
    });

    closeButton.addEventListener("click", () => dialog.close());
    searchInput.addEventListener("input", renderResults);
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) {
            dialog.close();
        }
    });
    dialog.addEventListener("close", () => {
        searchInput.value = "";
        results.replaceChildren();
        status.textContent = "";
        trigger.focus();
    });
})();