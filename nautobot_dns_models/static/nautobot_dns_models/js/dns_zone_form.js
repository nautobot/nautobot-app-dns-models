/**
 * DNS Zone Form: disables and clears the controls that do not apply to the zone as it is filled
 * in, and swaps in help text saying why.
 *
 * 1. Only a zone in a catalog zone has a member label, so the label is emptied and disabled while
 *    no catalog zone is chosen, and restored when one is. The server drops a label submitted
 *    without a catalog zone.
 *
 * 2. A catalog zone cannot auto-create PTR records or be a member of another catalog zone, so
 *    while the type is "catalog" those controls are cleared and disabled. This runs only on
 *    create; on edit the type is fixed and the server sets these controls.
 */

document.addEventListener("DOMContentLoaded", function () {
    const zoneTypeField = document.getElementById("id_type");
    const catalogZoneField = document.getElementById("id_catalog_zone");

    // Returns a control's field, help text element and state function, or null if the field is
    // not on the page.
    function control(id, inactiveHelpText, applyState) {
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
            inactiveHelpText: inactiveHelpText,
            applyState: applyState,
        };
    }

    // Applies the state to a control and shows the matching help text.
    function update(entry, inactive) {
        entry.applyState(entry.field, inactive);

        if (entry.helpElement) {
            entry.helpElement.textContent = inactive ? entry.inactiveHelpText : entry.defaultHelpText;
        }
    }

    //
    // Rule 1: the member label.
    //

    // heldLabel keeps the label while no catalog zone is chosen. data-default-label (the zone's
    // label, or a generated one) is the fallback, since a form re-rendered after a failed submit
    // loads with the field empty.
    let heldLabel = "";
    const memberLabel = control(
        "id_member_label",
        "Only a zone in a catalog zone has a member label.",
        function (field, inactive) {
            // Save only while the field is enabled, so a repeat call does not overwrite the save.
            if (inactive && !field.disabled) {
                heldLabel = field.value;
                field.value = "";
            } else if (!inactive && field.disabled) {
                field.value = heldLabel || field.dataset.defaultLabel || "";
            }
            field.disabled = inactive;
        }
    );

    // Applies the rule on load and on each catalog zone change, unless the server disabled the
    // label, as when editing a catalog zone.
    if (memberLabel && !memberLabel.field.disabled && catalogZoneField) {
        const updateMemberLabel = function () {
            update(memberLabel, !catalogZoneField.value);
        };
        updateMemberLabel();
        $(catalogZoneField).on("change select2:select select2:clear", updateMemberLabel);
    }

    //
    // Rule 2: the controls that depend on the type.
    //

    // Stops here on edit, where the server disables the type.
    if (!zoneTypeField || zoneTypeField.disabled) {
        return;
    }

    const typeControls = [
        control(
            "id_auto_create_ptr",
            "Catalog zones cannot enable automatic PTR creation.",
            function (field, isCatalog) {
                field.disabled = isCatalog;
                // Unchecks the box to match the server, which reads a disabled checkbox as unchecked.
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
                // Clears the value and fires "change", which makes Select2 redraw and rule 1 disable the label.
                if (isCatalog && field.value) {
                    $(field).val(null).trigger("change");
                }
                // Disables the embedded Add and Search buttons; core only does so for a server-disabled field.
                const container = field.closest(".mb-10");
                if (container) {
                    container.querySelectorAll('button[data-bs-target="#embedded_action_modal"]')
                        .forEach(function (button) {
                            button.disabled = isCatalog;
                        });
                }
            }
        ),
    ].filter(Boolean);

    function updateTypeControls() {
        const isCatalog = zoneTypeField.value === "catalog";
        typeControls.forEach(function (entry) {
            update(entry, isCatalog);
        });
    }

    updateTypeControls();
    $(zoneTypeField).on("change select2:select select2:clear", updateTypeControls);
});
