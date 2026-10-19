"use strict";

const brief = document.querySelector("#brief-form");
if (brief) {
  const brand = brief.querySelector("#brand");
  const filterProducts = () => {
    brief.querySelectorAll(".product-choice").forEach((label) => {
      const active = label.dataset.brand === brand.value;
      label.hidden = !active;
      const input = label.querySelector("input");
      input.disabled = !active;
      if (!active) input.checked = false;
    });
  };
  brand.addEventListener("change", filterProducts);
  filterProducts();

  const rows = brief.querySelector("#criteria");
  const renumber = () => {
    rows.querySelectorAll(".criterion-row").forEach((row, index) => {
      row.querySelectorAll("[name]").forEach((input) => {
        input.name = input.name.replace(/^criterion_\d+_/, `criterion_${index}_`);
      });
    });
    brief.elements.criterion_count.value = rows.children.length;
  };
  brief.querySelector("#add-criterion").addEventListener("click", () => {
    const index = rows.children.length;
    if (index >= 30) return;
    const template = document.querySelector("#criterion-template");
    const container = document.createElement("div");
    container.innerHTML = template.innerHTML.replaceAll("__index__", String(index));
    const row = container.firstElementChild;
    row.querySelector('input[type="hidden"]').value = `criterion-${crypto.randomUUID()}`;
    rows.append(row);
    renumber();
    row.querySelector('input:not([type="hidden"])').focus();
  });
  rows.addEventListener("click", (event) => {
    const remove = event.target.closest("[data-remove-criterion]");
    if (remove && rows.children.length > 1) {
      remove.closest(".criterion-row").remove();
      renumber();
    }
  });
}

const shortlist = document.querySelector("#shortlist-form");
if (shortlist) {
  const confirmation = shortlist.querySelector('button[value="confirm"]');
  const reviewed = shortlist.elements.reviewed;
  const requiresNewBrief = confirmation.disabled;
  const update = () => { confirmation.disabled = requiresNewBrief || !reviewed.checked; };
  reviewed.addEventListener("change", update);
  update();
}
