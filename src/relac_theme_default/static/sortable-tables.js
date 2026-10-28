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