/**
 * DNS Zone Form - disable the controls a catalog zone cannot use.
 *
 * A catalog zone cannot auto-create PTR records or be a member of another catalog zone, and the
 * model refuses both. On create, type is still editable, so the controls must track the select.
 * On edit, type is already disabled server-side and this script exits early.
 */

document.addEventListener("DOMContentLoaded", function () {
    const zoneTypeField = document.getElementById("id_type");

    // Edit disables type server-side; leave the other controls as the form set them.
    if (!zoneTypeField || zoneTypeField.disabled) {
        return;
    }

    function control(id, catalogHelpText, applyState) {
        const field = document.getElementById(id);
        if (!field) {
            return null;
        }

        // Nautobot render_field wraps each control in div.mb-10 with an optional span.form-text.
        const container = field.closest(".mb-10");
        const helpElement = container ? container.querySelector(".form-text") : null;

        return {
            field: field,
            helpElement: helpElement,
            defaultHelpText: helpElement ? helpElement.textContent : "",
            catalogHelpText: catalogHelpText,
            applyState: applyState,
        };
    }

    const controls = [
        control(
            "id_auto_create_ptr",
            "Catalog zones cannot enable automatic PTR creation.",
            function (field, isCatalog) {
                field.disabled = isCatalog;
                if (isCatalog) {
                    field.checked = false;
                }
            }
        ),
        control(
            "id_catalog_zone",
            "A catalog zone cannot be a member of another catalog zone.",
            function (field, isCatalog) {
                field.disabled = isCatalog;
                if (isCatalog && field.value) {
                    $(field).val(null).trigger("change");
                }
            }
        ),
    ].filter(Boolean);

    function updateControls() {
        const isCatalog = zoneTypeField.value === "catalog";

        controls.forEach(function (entry) {
            entry.applyState(entry.field, isCatalog);

            if (entry.helpElement) {
                entry.helpElement.textContent = isCatalog ? entry.catalogHelpText : entry.defaultHelpText;
            }
        });
    }

    updateControls();
    $(zoneTypeField).on("change select2:select select2:clear", updateControls);
});
