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
    const pageUrl = new URL(window.location.href);

    const updateQueryValues = (key, values) => {
        pageUrl.searchParams.delete(key);
        values.forEach((value) => pageUrl.searchParams.append(key, value));
        window.history.replaceState(
            window.history.state,
            "",
            `${pageUrl.pathname}${pageUrl.search}${pageUrl.hash}`
        );
    };

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

    const getFilterGroups = (cell) => {
        if (!cell || cell.dataset.filterGroups === undefined) {
            return { "": getFilterValues(cell) };
        }

        const groups = JSON.parse(cell.dataset.filterGroups);
        return groups && typeof groups === "object" && !Array.isArray(groups)
            ? groups
            : {};
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
        const rowCells = new Map(rows.map((row) => [row, Array.from(row.cells)]));
        const emptyStateBody = table.tBodies[table.tBodies.length - 1];
        const emptyStateRow = emptyStateBody.insertRow();
        emptyStateRow.className = "table-empty-state";
        emptyStateRow.hidden = true;
        const emptyStateCell = emptyStateRow.insertCell();
        emptyStateCell.colSpan = headers.length;
        const selectedValuesByColumn = new Map();
        const sortActionsByColumn = new Map();
        const tableKey = table.id || "table";
        const itemName = table.id
            ? table.id.replace(/-table$/, "").replace(/-/g, " ")
            : "items";
        const sortParameter = `relac.sort.${tableKey}`;
        const columnOrderParameter = `relac.order.${tableKey}`;
        const hiddenColumnsParameter = `relac.columns.${tableKey}`;
        const columnKeyCounts = new Map();
        const columnKeys = headers.map((header) => {
            const label = header.textContent.trim();
            const occurrence = (columnKeyCounts.get(label) ?? 0) + 1;
            columnKeyCounts.set(label, occurrence);
            return `${label}:${occurrence}`;
        });
        const columnIndexesByKey = new Map(columnKeys.map((key, index) => [key, index]));
        let columnOrder = Array.from(headers.keys());
        try {
            const savedOrder = JSON.parse(localStorage.getItem(columnOrderParameter) ?? "[]");
            if (Array.isArray(savedOrder)) {
                const restoredOrder = [];
                savedOrder.forEach((key) => {
                    const columnIndex = columnIndexesByKey.get(key);
                    if (columnIndex !== undefined && !restoredOrder.includes(columnIndex)) {
                        restoredOrder.push(columnIndex);
                    }
                });
                columnOrder = [
                    ...restoredOrder,
                    ...Array.from(headers.keys()).filter((index) => !restoredOrder.includes(index))
                ];
            }
        } catch {
        }
        const defaultColumnWidths = headers.map((header) => header.getBoundingClientRect().width);
        const columnWidthsParameter = `relac.widths.${tableKey}`;
        const columnGroup = document.createElement("colgroup");
        const columns = headers.map(() => document.createElement("col"));
        columnGroup.append(...columns);
        table.insertBefore(columnGroup, table.firstChild);
        const applyColumnOrder = () => {
            const headerRow = table.tHead.rows[0];
            columnOrder.forEach((columnIndex) => headerRow.append(headers[columnIndex]));
            columnOrder.forEach((columnIndex) => columnGroup.append(columns[columnIndex]));
            rows.forEach((row) => {
                const cells = rowCells.get(row);
                columnOrder.forEach((columnIndex) => row.append(cells[columnIndex]));
            });
        };
        let savedColumnWidths = {};
        try {
            const parsedWidths = JSON.parse(localStorage.getItem(columnWidthsParameter) ?? "{}");
            if (parsedWidths && typeof parsedWidths === "object" && !Array.isArray(parsedWidths)) {
                savedColumnWidths = parsedWidths;
            }
        } catch {
        }
        let hasSavedColumnWidths = false;
        columns.forEach((column, columnIndex) => {
            const width = Number(savedColumnWidths[columnKeys[columnIndex]]);
            if (Number.isFinite(width) && width >= 56) {
                column.style.width = `${width}px`;
                hasSavedColumnWidths = true;
            }
        });
        if (hasSavedColumnWidths) {
            table.style.tableLayout = "fixed";
        }
        applyColumnOrder();
        let hiddenColumnKeys = new Set();
        try {
            const savedColumns = JSON.parse(localStorage.getItem(hiddenColumnsParameter) ?? "[]");
            if (Array.isArray(savedColumns)) {
                hiddenColumnKeys = new Set(savedColumns.filter((key) => typeof key === "string"));
            }
        } catch {
        }
        hiddenColumnKeys = new Set(
            Array.from(hiddenColumnKeys).filter((key) => columnKeys.includes(key))
        );
        if (columnKeys.length > 0 && hiddenColumnKeys.size === columnKeys.length) {
            hiddenColumnKeys.delete(columnKeys[0]);
        }
        const visibilityToggles = new Map();
        const clearActionsByColumn = new Map();
        const resizeHandlesByColumn = new Map();
        const minimumColumnWidth = 56;
        let draggedColumnIndex = -1;
        let suppressSortUntil = 0;
        let isRestoringState = true;
        const tableToolbar = document.createElement("div");
        tableToolbar.className = "table-toolbar";
        const tableCount = document.createElement("p");
        tableCount.className = "table-count";
        tableCount.setAttribute("aria-live", "polite");

        const settingsToggle = document.createElement("button");
        settingsToggle.type = "button";
        settingsToggle.className = "table-settings-toggle";
        settingsToggle.setAttribute("aria-label", `Table settings for ${itemName}`);
        settingsToggle.setAttribute("aria-expanded", "false");
        const settingsMenuId = `${table.id || "sortable-table"}-settings`;
        settingsToggle.setAttribute("aria-controls", settingsMenuId);

        const settingsMenu = document.createElement("div");
        settingsMenu.className = "table-settings-menu";
        settingsMenu.id = settingsMenuId;
        settingsMenu.hidden = true;
        settingsMenu.setAttribute("aria-label", `Table settings for ${itemName}`);

        const resetTableButton = document.createElement("button");
        resetTableButton.type = "button";
        resetTableButton.className = "table-settings-reset";
        resetTableButton.textContent = "Reset table";

        const visibilityHeading = document.createElement("p");
        visibilityHeading.className = "table-settings-heading";
        visibilityHeading.textContent = "Visible columns";

        const visibilityOptions = document.createElement("div");
        visibilityOptions.className = "table-column-visibility-options";
        settingsMenu.append(resetTableButton, visibilityHeading, visibilityOptions);
        tableToolbar.append(tableCount);
        const settingsHost = table.closest(".table-card")?.querySelector(".table-card-actions")
            ?? tableToolbar;
        settingsHost.append(settingsToggle, settingsMenu);
        (table.closest(".table-scroll") ?? table).before(tableToolbar);

        const getNextVisibleColumnIndex = (columnIndex) => {
            const currentPosition = columnOrder.indexOf(columnIndex);
            return columnOrder.slice(currentPosition + 1).find((candidateIndex) => {
                return !headers[candidateIndex].hidden;
            }) ?? -1;
        };

        const persistColumnOrder = () => {
            try {
                localStorage.setItem(
                    columnOrderParameter,
                    JSON.stringify(columnOrder.map((columnIndex) => columnKeys[columnIndex]))
                );
            } catch {
            }
        };

        const moveColumn = (sourceIndex, targetIndex, insertAfter) => {
            const sourcePosition = columnOrder.indexOf(sourceIndex);
            let targetPosition = columnOrder.indexOf(targetIndex);
            if (sourcePosition === -1 || targetPosition === -1 || sourceIndex === targetIndex) {
                return;
            }

            const [movedIndex] = columnOrder.splice(sourcePosition, 1);
            if (sourcePosition < targetPosition) {
                targetPosition -= 1;
            }
            columnOrder.splice(targetPosition + Number(insertAfter), 0, movedIndex);
            applyColumnOrder();
            updateColumnVisibility();
            persistColumnOrder();
        };

        const getColumnWidth = (columnIndex) => {
            return Number.parseFloat(columns[columnIndex].style.width) ||
                headers[columnIndex].getBoundingClientRect().width ||
                defaultColumnWidths[columnIndex];
        };

        const initializeColumnWidths = () => {
            headers.forEach((header, columnIndex) => {
                const width = header.hidden
                    ? getColumnWidth(columnIndex)
                    : header.getBoundingClientRect().width;
                if (width > 0) {
                    columns[columnIndex].style.width = `${width}px`;
                }
                columns[columnIndex].hidden = header.hidden;
            });
            table.style.tableLayout = "fixed";
        };

        const resizeColumnPair = (columnIndex, nextColumnIndex, firstWidth, secondWidth, delta) => {
            const appliedDelta = Math.max(
                minimumColumnWidth - firstWidth,
                Math.min(delta, secondWidth - minimumColumnWidth)
            );
            const resizedWidth = firstWidth + appliedDelta;
            columns[columnIndex].style.width = `${resizedWidth}px`;
            columns[nextColumnIndex].style.width = `${secondWidth - appliedDelta}px`;
            const handle = resizeHandlesByColumn.get(columnIndex);
            handle?.setAttribute("aria-valuenow", String(Math.round(resizedWidth)));
        };

        const persistColumnWidths = () => {
            const widths = Object.fromEntries(columns.map((column, columnIndex) => {
                return [columnKeys[columnIndex], getColumnWidth(columnIndex)];
            }));
            try {
                localStorage.setItem(columnWidthsParameter, JSON.stringify(widths));
            } catch {
            }
        };

        const updateColumnVisibility = () => {
            let visibleColumnCount = 0;
            headers.forEach((header, columnIndex) => {
                const isHidden = hiddenColumnKeys.has(columnKeys[columnIndex]);
                header.hidden = isHidden;
                columns[columnIndex].hidden = isHidden;
                rows.forEach((row) => {
                    const cell = rowCells.get(row)[columnIndex];
                    if (cell) {
                        cell.hidden = isHidden;
                    }
                });
                if (!isHidden) {
                    visibleColumnCount += 1;
                }
            });
            emptyStateCell.colSpan = Math.max(1, visibleColumnCount);
            visibilityToggles.forEach(({ checkbox, key }) => {
                checkbox.checked = !hiddenColumnKeys.has(key);
                checkbox.disabled = checkbox.checked && visibleColumnCount === 1;
            });
            resizeHandlesByColumn.forEach((handle, columnIndex) => {
                const nextColumnIndex = getNextVisibleColumnIndex(columnIndex);
                handle.hidden = nextColumnIndex === -1;
                handle.setAttribute("aria-valuenow", String(Math.round(getColumnWidth(columnIndex))));
            });
        };

        const persistColumnVisibility = () => {
            try {
                localStorage.setItem(hiddenColumnsParameter, JSON.stringify(Array.from(hiddenColumnKeys)));
            } catch {
            }
        };

        const positionSettingsMenu = () => {
            if (settingsMenu.hidden) {
                return;
            }

            const toggleRect = settingsToggle.getBoundingClientRect();
            const menuHeight = settingsMenu.offsetHeight;
            const menuWidth = settingsMenu.offsetWidth;
            const top = toggleRect.bottom + menuHeight + 8 <= window.innerHeight
                ? toggleRect.bottom + 4
                : Math.max(8, toggleRect.top - menuHeight - 4);
            const left = Math.max(
                8,
                Math.min(toggleRect.right - menuWidth, window.innerWidth - menuWidth - 8)
            );

            settingsMenu.style.top = `${top}px`;
            settingsMenu.style.left = `${left}px`;
        };

        settingsToggle.addEventListener("click", () => {
            settingsMenu.hidden = !settingsMenu.hidden;
            settingsToggle.setAttribute("aria-expanded", String(!settingsMenu.hidden));
            positionSettingsMenu();
        });

        settingsMenu.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                settingsMenu.hidden = true;
                settingsToggle.setAttribute("aria-expanded", "false");
                settingsToggle.focus();
            }
        });

        window.addEventListener("resize", positionSettingsMenu);
        window.addEventListener("scroll", positionSettingsMenu, true);

        const updateRows = () => {
            let visibleCount = 0;
            rows.forEach((row) => {
                row.hidden = Array.from(selectedValuesByColumn).some(([columnIndex, selectedValues]) => {
                    return selectedValues.size > 0 && !getFilterValues(rowCells.get(row)[columnIndex])
                        .some((value) => selectedValues.has(value));
                });
                if (!row.hidden) {
                    visibleCount += 1;
                }
            });
            const itemLabel = rows.length === 1 ? "item" : "items";
            tableCount.textContent = `${visibleCount} of ${rows.length} ${itemLabel}`;
            emptyStateCell.textContent = rows.length === 0
                ? `No ${itemName} to display.`
                : `No ${itemName} match the current filters.`;
            emptyStateRow.hidden = visibleCount > 0;
        };

        headers.forEach((header, columnIndex) => {
            if (header.tagName !== "TH") {
                return;
            }

            const label = header.textContent.trim();
            const columnLabel = document.createElement("span");
            columnLabel.className = "table-column-label";
            columnLabel.setAttribute("tabindex", "0");
            columnLabel.setAttribute("aria-keyshortcuts", "Alt+ArrowLeft Alt+ArrowRight");
            while (header.firstChild) {
                columnLabel.append(header.firstChild);
            }

            const headerControls = document.createElement("div");
            headerControls.className = "table-header-controls";

            const columnFilter = document.createElement("div");
            columnFilter.className = "table-column-filter";

            const resizeHandle = document.createElement("div");
            resizeHandle.className = "table-column-resize-handle";
            resizeHandle.setAttribute("role", "separator");
            resizeHandle.setAttribute("aria-orientation", "vertical");
            resizeHandle.setAttribute("aria-label", `Resize ${label} column`);
            resizeHandle.setAttribute("aria-valuemin", String(minimumColumnWidth));
            resizeHandle.setAttribute("tabindex", "0");
            resizeHandlesByColumn.set(columnIndex, resizeHandle);

            resizeHandle.addEventListener("pointerdown", (event) => {
                if (event.button !== 0) {
                    return;
                }

                const nextColumnIndex = getNextVisibleColumnIndex(columnIndex);
                if (nextColumnIndex === -1) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();
                const firstWidth = header.getBoundingClientRect().width;
                const secondWidth = headers[nextColumnIndex].getBoundingClientRect().width;
                initializeColumnWidths();
                const startX = event.clientX;
                resizeHandle.setPointerCapture(event.pointerId);

                const finishResize = () => {
                    resizeHandle.removeEventListener("pointermove", onPointerMove);
                    resizeHandle.removeEventListener("pointerup", finishResize);
                    resizeHandle.removeEventListener("pointercancel", finishResize);
                    if (resizeHandle.hasPointerCapture(event.pointerId)) {
                        resizeHandle.releasePointerCapture(event.pointerId);
                    }
                    persistColumnWidths();
                };

                const onPointerMove = (moveEvent) => {
                    resizeColumnPair(
                        columnIndex,
                        nextColumnIndex,
                        firstWidth,
                        secondWidth,
                        moveEvent.clientX - startX
                    );
                };

                resizeHandle.addEventListener("pointermove", onPointerMove);
                resizeHandle.addEventListener("pointerup", finishResize);
                resizeHandle.addEventListener("pointercancel", finishResize);
            });

            resizeHandle.addEventListener("keydown", (event) => {
                if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
                    return;
                }

                const nextColumnIndex = getNextVisibleColumnIndex(columnIndex);
                if (nextColumnIndex === -1) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();
                initializeColumnWidths();
                resizeColumnPair(
                    columnIndex,
                    nextColumnIndex,
                    getColumnWidth(columnIndex),
                    getColumnWidth(nextColumnIndex),
                    event.key === "ArrowRight" ? 10 : -10
                );
                persistColumnWidths();
            });

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

            const selectAllButton = document.createElement("button");
            selectAllButton.type = "button";
            selectAllButton.className = "table-column-filter-clear";
            selectAllButton.textContent = "Select all";
            selectAllButton.disabled = true;

            const selectNoneButton = document.createElement("button");
            selectNoneButton.type = "button";
            selectNoneButton.className = "table-column-filter-clear";
            selectNoneButton.textContent = "Select none";
            selectNoneButton.disabled = true;

            filterActions.append(search, selectAllButton, selectNoneButton);

            const options = document.createElement("div");
            options.className = "table-column-filter-options";

            const visibilityOption = document.createElement("label");
            visibilityOption.className = "table-column-visibility-option";
            const visibilityCheckbox = document.createElement("input");
            visibilityCheckbox.type = "checkbox";
            visibilityCheckbox.checked = !hiddenColumnKeys.has(columnKeys[columnIndex]);
            const visibilityLabel = document.createElement("span");
            visibilityLabel.textContent = label;
            visibilityOption.append(visibilityCheckbox, visibilityLabel);
            visibilityOptions.append(visibilityOption);
            visibilityToggles.set(columnIndex, {
                checkbox: visibilityCheckbox,
                key: columnKeys[columnIndex]
            });
            visibilityCheckbox.addEventListener("change", () => {
                if (visibilityCheckbox.checked) {
                    hiddenColumnKeys.delete(columnKeys[columnIndex]);
                } else {
                    const visibleCount = headers.filter((candidate, candidateIndex) => {
                        return candidateIndex !== columnIndex &&
                            !hiddenColumnKeys.has(columnKeys[candidateIndex]);
                    }).length;
                    if (visibleCount === 0) {
                        visibilityCheckbox.checked = true;
                        return;
                    }
                    hiddenColumnKeys.add(columnKeys[columnIndex]);
                }

                updateColumnVisibility();
                persistColumnVisibility();
            });

            const selectedValues = new Set();
            const filterValues = new Set();
            selectedValuesByColumn.set(columnIndex, selectedValues);
            const filterParameter = `relac.filter.${tableKey}.${columnIndex}`;
            const savedValues = new Set(pageUrl.searchParams.getAll(filterParameter));

            const valuesByGroup = new Map();
            rows.forEach((row) => {
                const cell = rowCells.get(row)[columnIndex];
                const groups = getFilterGroups(cell);
                let hasGroupedValues = false;
                Object.entries(groups).forEach(([groupLabel, groupValues]) => {
                    if (!Array.isArray(groupValues) || groupValues.length === 0) {
                        return;
                    }

                    hasGroupedValues = true;
                    if (!valuesByGroup.has(groupLabel)) {
                        valuesByGroup.set(groupLabel, new Set());
                    }
                    groupValues.forEach((value) => valuesByGroup.get(groupLabel).add(String(value)));
                });

                if (!hasGroupedValues) {
                    if (!valuesByGroup.has("")) {
                        valuesByGroup.set("", new Set());
                    }
                    getFilterValues(cell).forEach((value) => valuesByGroup.get("").add(value));
                }
            });

            const sortFilterValues = (values) => Array.from(values).sort((left, right) => {
                if (left === "") {
                    return right === "" ? 0 : -1;
                }

                if (right === "") {
                    return 1;
                }

                return collator.compare(left, right);
            });
            const checkboxes = [];
            const checkboxesByValue = new Map();
            valuesByGroup.forEach((groupValues, groupLabel) => {
                const groupOptions = document.createElement("div");
                groupOptions.className = "table-column-filter-group";
                if (groupLabel) {
                    const groupHeading = document.createElement("p");
                    groupHeading.className = "table-column-filter-group-heading";
                    groupHeading.textContent = groupLabel;
                    groupOptions.append(groupHeading);
                }

                sortFilterValues(groupValues).forEach((value) => {
                    const option = document.createElement("label");
                    option.className = "table-column-filter-option";

                    const checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.value = value;

                    const optionLabel = document.createElement("span");
                    optionLabel.textContent = value || "No value";

                    option.append(checkbox, optionLabel);
                    groupOptions.append(option);
                    const entry = { checkbox, option, value };
                    checkboxes.push(entry);
                    filterValues.add(value);
                    if (!checkboxesByValue.has(value)) {
                        checkboxesByValue.set(value, []);
                    }
                    checkboxesByValue.get(value).push(entry);

                    checkbox.addEventListener("change", () => {
                        checkboxesByValue.get(value).forEach(({ checkbox: matchingCheckbox }) => {
                            matchingCheckbox.checked = checkbox.checked;
                        });
                        if (checkbox.checked) {
                            selectedValues.add(value);
                        } else {
                            selectedValues.delete(value);
                        }

                        updateSummary();
                        updateRows();
                        updateQueryValues(filterParameter, Array.from(selectedValues));
                    });
                });

                options.append(groupOptions);
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
                    selectAllButton.disabled = count === filterValues.size;
                    selectNoneButton.disabled = count === 0;
            };

            checkboxes.forEach(({ checkbox, value }) => {
                if (savedValues.has(value)) {
                    checkbox.checked = true;
                    selectedValues.add(value);
                }
            });
            updateSummary();

            search.addEventListener("input", () => {
                const query = search.value.trim().toLocaleLowerCase();
                checkboxes.forEach(({ option }) => {
                    option.hidden = !option.textContent.toLocaleLowerCase().includes(query);
                });
                options.querySelectorAll(".table-column-filter-group").forEach((group) => {
                    group.hidden = !group.querySelector(".table-column-filter-option:not([hidden])");
                });
            });

            selectAllButton.addEventListener("click", () => {
                filterValues.forEach((value) => selectedValues.add(value));
                checkboxes.forEach(({ checkbox }) => {
                    checkbox.checked = true;
                });

                updateSummary();
                updateRows();
                updateQueryValues(filterParameter, Array.from(selectedValues));
            });

            selectNoneButton.addEventListener("click", () => {
                checkboxes.forEach(({ checkbox, value }) => {
                    checkbox.checked = false;
                    selectedValues.delete(value);
                });

                updateSummary();
                updateRows();
                updateQueryValues(filterParameter, Array.from(selectedValues));
            });
            clearActionsByColumn.set(columnIndex, selectNoneButton);

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
                if (!filterMenu.hidden) {
                    search.focus();
                }
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
            headerControls.append(columnLabel, columnFilter, resizeHandle);
            header.append(headerControls);
            header.setAttribute("aria-sort", "none");
            header.draggable = true;

            columnLabel.addEventListener("keydown", (event) => {
                if (!event.altKey || (event.key !== "ArrowLeft" && event.key !== "ArrowRight")) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();
                const currentPosition = columnOrder.indexOf(columnIndex);
                const direction = event.key === "ArrowRight" ? 1 : -1;
                const targetIndex = columnOrder[currentPosition + direction];
                if (targetIndex !== undefined) {
                    moveColumn(columnIndex, targetIndex, direction > 0);
                    columnLabel.focus();
                }
            });

            header.addEventListener("dragstart", (event) => {
                if (event.target instanceof Element && event.target.closest(
                    ".table-column-filter, .table-column-resize-handle"
                )) {
                    event.preventDefault();
                    return;
                }

                draggedColumnIndex = columnIndex;
                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData("text/plain", columnKeys[columnIndex]);
                header.classList.add("is-column-dragging");
            });

            header.addEventListener("dragover", (event) => {
                if (draggedColumnIndex === -1 || draggedColumnIndex === columnIndex) {
                    return;
                }

                event.preventDefault();
                event.dataTransfer.dropEffect = "move";
                const rect = header.getBoundingClientRect();
                header.dataset.columnDropPosition = event.clientX < rect.left + rect.width / 2
                    ? "before"
                    : "after";
            });

            header.addEventListener("dragleave", (event) => {
                if (!header.contains(event.relatedTarget)) {
                    delete header.dataset.columnDropPosition;
                }
            });

            header.addEventListener("drop", (event) => {
                if (draggedColumnIndex === -1 || draggedColumnIndex === columnIndex) {
                    return;
                }

                event.preventDefault();
                const rect = header.getBoundingClientRect();
                const insertAfter = event.clientX >= rect.left + rect.width / 2;
                moveColumn(draggedColumnIndex, columnIndex, insertAfter);
                suppressSortUntil = Date.now() + 250;
                headers.forEach((candidate) => {
                    candidate.classList.remove("is-column-dragging");
                    delete candidate.dataset.columnDropPosition;
                });
                draggedColumnIndex = -1;
            });

            header.addEventListener("dragend", () => {
                suppressSortUntil = Date.now() + 250;
                headers.forEach((candidate) => {
                    candidate.classList.remove("is-column-dragging");
                    delete candidate.dataset.columnDropPosition;
                });
                draggedColumnIndex = -1;
            });

            sortAction.addEventListener("click", () => {
                const direction = header.getAttribute("aria-sort") === "ascending" ? -1 : 1;
                const sortType = header.dataset.sortType ?? "auto";
                const values = Array.from(table.tBodies).flatMap((body) => {
                    return Array.from(body.rows, (row) => getCellValue(rowCells.get(row)?.[columnIndex]));
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
                if (!isRestoringState) {
                    updateQueryValues(sortParameter, [
                        `${columnIndex}:${direction === 1 ? "asc" : "desc"}`
                    ]);
                }

                Array.from(table.tBodies).forEach((body) => {
                    const rows = Array.from(body.rows)
                        .filter((row) => row !== emptyStateRow)
                        .map((row, originalIndex) => ({
                            row,
                            originalIndex,
                            value: getCellValue(rowCells.get(row)?.[columnIndex])
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
                emptyStateBody.append(emptyStateRow);
            });

            header.addEventListener("click", (event) => {
                if (Date.now() < suppressSortUntil) {
                    return;
                }

                if (event.target instanceof Element && event.target.closest(
                    ".table-column-filter, .table-column-resize-handle"
                )) {
                    return;
                }

                sortAction.click();
            });
        });

        updateColumnVisibility();
        resetTableButton.addEventListener("click", () => {
            hiddenColumnKeys.clear();
            columnOrder = Array.from(headers.keys());
            try {
                localStorage.removeItem(columnOrderParameter);
                localStorage.removeItem(hiddenColumnsParameter);
                localStorage.removeItem(columnWidthsParameter);
            } catch {
            }
            applyColumnOrder();
            columns.forEach((column) => column.style.removeProperty("width"));
            table.style.removeProperty("table-layout");
            updateColumnVisibility();

            clearActionsByColumn.forEach((clearAction) => clearAction.click());

            const firstColumnIndex = headers.findIndex((header) => header.tagName === "TH");
            const firstSortAction = sortActionsByColumn.get(firstColumnIndex);
            if (firstSortAction) {
                isRestoringState = true;
                headers[firstColumnIndex].setAttribute("aria-sort", "descending");
                firstSortAction.click();
                isRestoringState = false;
            }
            updateQueryValues(sortParameter, []);

            settingsMenu.hidden = true;
            settingsToggle.setAttribute("aria-expanded", "false");
        });

        updateRows();
        const savedSort = pageUrl.searchParams.get(sortParameter)?.match(/^([0-9]+):(asc|desc)$/);
        const savedSortColumnIndex = savedSort ? Number(savedSort[1]) : -1;
        const savedSortAction = sortActionsByColumn.get(savedSortColumnIndex);

        if (savedSort && savedSortAction) {
            headers[savedSortColumnIndex].setAttribute(
                "aria-sort",
                savedSort[2] === "asc" ? "descending" : "ascending"
            );
            savedSortAction.click();
        } else {
            const firstColumnIndex = headers.findIndex((header) => header.tagName === "TH");
            sortActionsByColumn.get(firstColumnIndex)?.click();
        }
        isRestoringState = false;
    });

    document.addEventListener("pointerdown", (event) => {
        const target = event.target;

        if (!(target instanceof Node)) {
            return;
        }

        document.querySelectorAll(
            ".table-column-filter-menu:not([hidden]), .table-settings-menu:not([hidden])"
        ).forEach((menu) => {
            const filter = menu.parentElement;
            if (!filter.contains(target)) {
                menu.hidden = true;
                const toggle = menu.classList.contains("table-settings-menu")
                    ? filter.querySelector(".table-settings-toggle")
                    : filter.querySelector(".table-column-filter-toggle");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    });
})();