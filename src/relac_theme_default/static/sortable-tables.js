(() => {
    const filterTables = new Map();

    document.querySelectorAll("[data-filter-target][data-filter-key]").forEach((controls) => {
        const table = document.getElementById(controls.dataset.filterTarget);

        if (!(table instanceof HTMLTableElement) || table.tBodies.length === 0) {
            return;
        }

        if (!filterTables.has(table)) {
            filterTables.set(table, {
                rows: Array.from(table.tBodies).flatMap((body) => Array.from(body.rows)),
                groups: []
            });
        }

        filterTables.get(table).groups.push({
            key: controls.dataset.filterKey,
            buttons: Array.from(controls.querySelectorAll("button[data-filter-value]")),
            checkboxes: Array.from(controls.querySelectorAll("input[type='checkbox'][data-filter-value]")),
            multipleValues: controls.dataset.filterMultipleValues === "true",
            selectionSummary: controls.querySelector("[data-filter-selection-summary]"),
            search: controls.querySelector("[data-filter-search]"),
            options: Array.from(controls.querySelectorAll("[data-filter-option]")),
            selectedValues: new Set()
        });
    });

    filterTables.forEach(({ rows, groups }) => {
        const updateRows = () => {
            rows.forEach((row) => {
                row.hidden = groups.some(({ key, multipleValues, selectedValues }) => {
                    if (selectedValues.size === 0) {
                        return false;
                    }

                    const rowValue = row.getAttribute(`data-filter-${key}`);
                    const values = multipleValues
                        ? JSON.parse(rowValue ?? "[]")
                        : [rowValue];

                    return !values.some((value) => selectedValues.has(value));
                });
            });
        };

        groups.forEach(({ buttons, checkboxes, selectedValues, selectionSummary, search, options }) => {
            buttons.forEach((button) => {
                button.addEventListener("click", () => {
                    const value = button.dataset.filterValue;

                    if (selectedValues.has(value)) {
                        selectedValues.delete(value);
                        button.setAttribute("aria-pressed", "false");
                    } else {
                        selectedValues.add(value);
                        button.setAttribute("aria-pressed", "true");
                    }

                    updateRows();
                });
            });

            checkboxes.forEach((checkbox) => {
                checkbox.addEventListener("change", () => {
                    if (checkbox.checked) {
                        selectedValues.add(checkbox.dataset.filterValue);
                    } else {
                        selectedValues.delete(checkbox.dataset.filterValue);
                    }

                    if (selectionSummary) {
                        const count = selectedValues.size;
                        selectionSummary.textContent = count === 0
                            ? selectionSummary.dataset.emptyLabel
                            : `${count} ${count === 1 ? selectionSummary.dataset.singleLabel : selectionSummary.dataset.pluralLabel}`;
                    }

                    updateRows();
                });
            });

            if (search) {
                search.addEventListener("input", () => {
                    const query = search.value.trim().toLocaleLowerCase();
                    options.forEach((option) => {
                        option.hidden = !option.textContent.toLocaleLowerCase().includes(query);
                    });
                });
            }
        });
    });

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

        headers.forEach((header, columnIndex) => {
            if (header.tagName !== "TH") {
                return;
            }

            const label = header.textContent.trim();
            const button = document.createElement("button");
            button.type = "button";
            button.className = "sortable-table-button";
            button.setAttribute("aria-label", `Sort by ${label}`);

            while (header.firstChild) {
                button.append(header.firstChild);
            }

            header.append(button);
            header.setAttribute("aria-sort", "none");

            button.addEventListener("click", () => {
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

                headers.forEach((candidate) => {
                    if (candidate.tagName === "TH") {
                        candidate.setAttribute("aria-sort", "none");
                    }
                });
                header.setAttribute("aria-sort", direction === 1 ? "ascending" : "descending");

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
})();