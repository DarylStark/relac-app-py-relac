(() => {
    const formatter = new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeZone: "UTC"
    });

    document.querySelectorAll("time[data-local-date]").forEach((element) => {
        const date = new Date(`${element.dateTime}T00:00:00Z`);

        if (!Number.isNaN(date.valueOf())) {
            element.textContent = formatter.format(date);
        }
    });
})();