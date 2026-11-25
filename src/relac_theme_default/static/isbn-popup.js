(() => {
    const trigger = document.querySelector(".isbn-popup-trigger");
    const dialog = document.querySelector(".isbn-dialog");
    const closeButton = document.querySelector(".isbn-popup-close");

    if (
        !(trigger instanceof HTMLButtonElement) ||
        !(dialog instanceof HTMLDialogElement) ||
        !(closeButton instanceof HTMLButtonElement)
    ) {
        return;
    }

    trigger.addEventListener("click", () => {
        if (!dialog.open) {
            dialog.showModal();
        }
        closeButton.focus();
    });

    closeButton.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) {
            dialog.close();
        }
    });
    dialog.addEventListener("close", () => trigger.focus());
})();
