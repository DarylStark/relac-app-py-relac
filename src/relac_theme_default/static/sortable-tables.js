(() => {
    document.querySelectorAll("tr[data-href]").forEach((row) => {
        row.addEventListener("click", (event) => {
            const target = event.target;

            if (!(target instanceof Element)) {
                return;
            }

            const cell = target.closest("[data-cell-href]");
            if (cell && row.contains(cell)) {
                window.location.assign(cell.dataset.cellHref);
                return;
            }

            if (target.closest("a, button, input, select, textarea, summary, [contenteditable='true']")) {
                return;
            }

            window.location.assign(row.dataset.href);
        });

        row.addEventListener("keydown", (event) => {
            const target = event.target;

            if (event.key === "Enter" && target instanceof Element && target.matches("[data-cell-href]")) {
                window.location.assign(target.dataset.cellHref);
            }
        });
    });

    const collator = new Intl.Collator(undefined, {
        numeric: true,
        sensitivity: "base"
    });

    const getCellValue = (cell) => {
        if (!cell) {
            return "";
        }

        return (cell.dataset.sortValue ?? cell.textContent ?? "").trim();
    };

    const getFilterValues = (cell) => {
        if (!cell) {
            return [""];
        }

        if (cell.dataset.filterValues !== undefined) {
            const values = JSON.parse(cell.dataset.filterValues);
            return values.length > 0 ? values : [""];
        }

        return [(cell.textContent ?? "").trim()];
    };

    const isNumeric = (value) => {
        return value !== "" && Number.isFinite(Number(value.replace(/,/g, "")));
    };

    const compareValues = (leftValue, rightValue, sortType, direction) => {
        if (leftValue === "") {
            return rightValue === "" ? 0 : 1;
        }

        if (rightValue === "") {
            return -1;
        }

        let comparison;

        if (sortType === "number") {
            comparison = Number(leftValue.replace(/,/g, "")) - Number(rightValue.replace(/,/g, ""));
        } else if (sortType === "date") {
            comparison = Date.parse(leftValue) - Date.parse(rightValue);
        } else {
            comparison = collator.compare(leftValue, rightValue);
        }

        if (!Number.isFinite(comparison)) {
            comparison = collator.compare(leftValue, rightValue);
        }

        return comparison * direction;
    };

    document.querySelectorAll("table[data-sortable]").forEach((table) => {
        if (!table.tHead || table.tBodies.length === 0 || table.tHead.rows.length === 0) {
            return;
        }

        const headers = Array.from(table.tHead.rows[0].cells);
        const rows = Array.from(table.tBodies).flatMap((body) => Array.from(body.rows));
        const selectedValuesByColumn = new Map();
        const sortActionsByColumn = new Map();

        const updateRows = () => {
            rows.forEach((row) => {
                row.hidden = Array.from(selectedValuesByColumn).some(([columnIndex, selectedValues]) => {
                    return selectedValues.size > 0 && !getFilterValues(row.cells[columnIndex])
                        .some((value) => selectedValues.has(value));
                });
            });
        };

        headers.forEach((header, columnIndex) => {
            if (header.tagName !== "TH") {
                return;
            }

            const label = header.textContent.trim();
            const columnLabel = document.createElement("span");
            columnLabel.className = "table-column-label";
            while (header.firstChild) {
                columnLabel.append(header.firstChild);
            }

            const headerControls = document.createElement("div");
            headerControls.className = "table-header-controls";

            const columnFilter = document.createElement("div");
            columnFilter.className = "table-column-filter";

            const filterToggle = document.createElement("button");
            filterToggle.type = "button";
            filterToggle.className = "table-column-filter-toggle";
            filterToggle.setAttribute("aria-label", `Column settings for ${label}`);
            filterToggle.setAttribute("aria-expanded", "false");

            const filterCount = document.createElement("span");
            filterCount.className = "table-column-filter-count";
            filterCount.hidden = true;
            filterToggle.append(filterCount);

            const filterMenuId = `${table.id || "sortable-table"}-filter-${columnIndex}`;
            filterToggle.setAttribute("aria-controls", filterMenuId);
            columnFilter.append(filterToggle);

            const filterMenu = document.createElement("div");
            filterMenu.className = "table-column-filter-menu";
            filterMenu.id = filterMenuId;
            filterMenu.hidden = true;

            const filterActions = document.createElement("div");
            filterActions.className = "table-column-filter-actions";

            const sortAction = document.createElement("button");
            sortAction.type = "button";
            sortAction.className = "table-column-sort-action";
            sortAction.textContent = "Sort ascending";
            sortActionsByColumn.set(columnIndex, sortAction);

            const search = document.createElement("input");
            search.type = "search";
            search.className = "table-column-filter-search";
            search.placeholder = "Search values";
            search.setAttribute("aria-label", `Search ${label} values`);

            const clearButton = document.createElement("button");
            clearButton.type = "button";
            clearButton.className = "table-column-filter-clear";
            clearButton.textContent = "Clear";
            clearButton.disabled = true;

            filterActions.append(search, clearButton);

            const options = document.createElement("div");
            options.className = "table-column-filter-options";

            const selectedValues = new Set();
            selectedValuesByColumn.set(columnIndex, selectedValues);

            const values = Array.from(new Set(rows.flatMap((row) => {
                return getFilterValues(row.cells[columnIndex]);
            }))).sort((left, right) => {
                if (left === "") {
                    return right === "" ? 0 : -1;
                }

                if (right === "") {
                    return 1;
                }

                return collator.compare(left, right);
            });

            const updateSummary = () => {
                const count = selectedValues.size;
                filterCount.textContent = count === 0 ? "" : String(count);
                filterCount.hidden = count === 0;
                filterToggle.setAttribute(
                    "aria-label",
                    count === 0
                        ? `Column settings for ${label}`
                        : `Column settings for ${label}, ${count} selected`
                );
                clearButton.disabled = count === 0;
            };

            const checkboxes = values.map((value) => {
                const option = document.createElement("label");
                option.className = "table-column-filter-option";

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.value = value;

                const optionLabel = document.createElement("span");
                optionLabel.textContent = value || "No value";

                option.append(checkbox, optionLabel);
                options.append(option);

                checkbox.addEventListener("change", () => {
                    if (checkbox.checked) {
                        selectedValues.add(value);
                    } else {
                        selectedValues.delete(value);
                    }

                    updateSummary();
                    updateRows();
                });

                return { checkbox, option, value };
            });

            search.addEventListener("input", () => {
                const query = search.value.trim().toLocaleLowerCase();
                checkboxes.forEach(({ option }) => {
                    option.hidden = !option.textContent.toLocaleLowerCase().includes(query);
                });
            });

            clearButton.addEventListener("click", () => {
                checkboxes.forEach(({ checkbox, value }) => {
                    checkbox.checked = false;
                    selectedValues.delete(value);
                });

                updateSummary();
                updateRows();
            });

            const positionFilterMenu = () => {
                if (filterMenu.hidden) {
                    return;
                }

                const toggleRect = filterToggle.getBoundingClientRect();
                const menuHeight = filterMenu.offsetHeight;
                const menuWidth = filterMenu.offsetWidth;
                const top = toggleRect.bottom + menuHeight + 8 <= window.innerHeight
                    ? toggleRect.bottom + 4
                    : Math.max(8, toggleRect.top - menuHeight - 4);
                const left = Math.max(
                    8,
                    Math.min(toggleRect.left, window.innerWidth - menuWidth - 8)
                );

                filterMenu.style.top = `${top}px`;
                filterMenu.style.left = `${left}px`;
            };

            filterToggle.addEventListener("click", () => {
                filterMenu.hidden = !filterMenu.hidden;
                filterToggle.setAttribute("aria-expanded", String(!filterMenu.hidden));
                positionFilterMenu();
            });

            filterMenu.addEventListener("keydown", (event) => {
                if (event.key === "Escape") {
                    filterMenu.hidden = true;
                    filterToggle.setAttribute("aria-expanded", "false");
                    filterToggle.focus();
                }
            });

            window.addEventListener("resize", positionFilterMenu);
            window.addEventListener("scroll", positionFilterMenu, true);

            filterMenu.append(sortAction, filterActions, options);
            columnFilter.append(filterMenu);
            headerControls.append(columnLabel, columnFilter);
            header.append(headerControls);
            header.setAttribute("aria-sort", "none");

            sortAction.addEventListener("click", () => {
                const direction = header.getAttribute("aria-sort") === "ascending" ? -1 : 1;
                const sortType = header.dataset.sortType ?? "auto";
                const values = Array.from(table.tBodies).flatMap((body) => {
                    return Array.from(body.rows, (row) => getCellValue(row.cells[columnIndex]));
                });
                const nonEmptyValues = values.filter((value) => value !== "");
                const numericColumn = sortType === "number" || (
                    sortType === "auto" &&
                    nonEmptyValues.length > 0 &&
                    nonEmptyValues.every(isNumeric)
                );
                const effectiveSortType = numericColumn ? "number" : sortType;

                headers.forEach((candidate, candidateIndex) => {
                    if (candidate.tagName === "TH") {
                        candidate.setAttribute("aria-sort", "none");
                    }

                    const candidateAction = sortActionsByColumn.get(candidateIndex);
                    if (candidateAction) {
                        candidateAction.textContent = "Sort ascending";
                    }
                });
                header.setAttribute("aria-sort", direction === 1 ? "ascending" : "descending");
                sortAction.textContent = direction === 1 ? "Sort descending" : "Sort ascending";

                Array.from(table.tBodies).forEach((body) => {
                    const rows = Array.from(body.rows).map((row, originalIndex) => ({
                        row,
                        originalIndex,
                        value: getCellValue(row.cells[columnIndex])
                    }));

                    rows.sort((left, right) => {
                        const comparison = compareValues(
                            left.value,
                            right.value,
                            effectiveSortType,
                            direction
                        );

                        return comparison === 0
                            ? left.originalIndex - right.originalIndex
                            : comparison;
                    });

                    rows.forEach(({ row }) => body.append(row));
                });
            });
        });
    });

    document.addEventListener("pointerdown", (event) => {
        const target = event.target;

        if (!(target instanceof Node)) {
            return;
        }

        document.querySelectorAll(".table-column-filter-menu:not([hidden])").forEach((menu) => {
            const filter = menu.parentElement;
            if (!filter.contains(target)) {
                menu.hidden = true;
                filter.querySelector(".table-column-filter-toggle").setAttribute("aria-expanded", "false");
            }
        });
    });
})();