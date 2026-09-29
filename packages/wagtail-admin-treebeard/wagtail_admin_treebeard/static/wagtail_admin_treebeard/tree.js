// Stimulus controller for the listing. Drop a row on the middle of another one to nest it under
// it, or near its top or bottom edge to place it before or after it at the same level. Anywhere
// else on the page drops it at the root level. On a sorted model (treebeard's node_order_by) the
// edges are not offered: siblings cannot be reordered by hand. The server does the move; the
// page reloads.
const EDGE = 0.25; // fraction of the row height, from the top or bottom, that means before / after
const depthOf = (row) => Number(row.style.getPropertyValue("--tb-depth"));

class TreeController extends window.StimulusModule.Controller {
  static values = { moveUrl: String, sorted: Boolean };
  static targets = ["bar"];

  // A row followed by the rows of its subtree: the next rows that are deeper than it.
  subtree(row) {
    const rows = [row];
    const depth = depthOf(row);
    for (let next = row.nextElementSibling; next && depthOf(next) > depth; next = next.nextElementSibling) {
      rows.push(next);
    }
    return rows;
  }

  start(event) {
    const row = event.target.closest("tr[data-node]");
    if (!row) return;
    this.dragged = row;
    this.blocked = new Set(this.subtree(row)); // a row cannot land on itself or its descendants
    row.classList.add("is-dragging");
    event.dataTransfer.effectAllowed = "move";
    // Firefox and Safari only start a drag when some data is set.
    event.dataTransfer.setData("text/plain", row.dataset.node);
  }

  end() {
    this.clear();
    this.dragged?.classList.remove("is-dragging");
    this.dragged = null;
  }

  over(event) {
    const drop = this.dropAt(event);
    if (!drop) return this.clear();
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    this.show(drop);
  }

  async drop(event) {
    const drop = this.dropAt(event);
    if (!drop) return;
    event.preventDefault();
    await fetch(this.moveUrlValue, {
      method: "POST",
      body: new URLSearchParams({
        node: this.dragged.dataset.node,
        target: drop.row.dataset.node,
        position: drop.position,
      }),
      headers: {
        "X-CSRFToken": window.wagtailConfig.CSRF_TOKEN,
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    window.location.reload(); // success or error, the server left a message to display
  }

  // Where the dragged row would land: a row and "before", "after" or "child". Outside the rows it
  // goes to the root level, before the first row or after the last root.
  dropAt(event) {
    if (!this.dragged) return null;
    const rows = Array.from(this.element.querySelectorAll("tr[data-node]"));
    let row = event.target.closest?.("tr[data-node]");
    let position;
    if (row && this.element.contains(row)) {
      const rect = row.getBoundingClientRect();
      const y = (event.clientY - rect.top) / rect.height;
      position = "child";
      if (!this.sortedValue && y < EDGE) position = "before";
      if (!this.sortedValue && y > 1 - EDGE) position = "after";
    } else if (event.clientY < rows[0].getBoundingClientRect().top) {
      [row, position] = [rows[0], "before"];
    } else {
      [row, position] = [rows.findLast((r) => depthOf(r) === 0), "after"];
    }
    return this.blocked.has(row) ? null : { row, position };
  }

  show({ row, position }) {
    this.clear();
    if (position === "child") return row.classList.add("is-drop-target");
    // "after" a row means after its whole subtree, so draw the bar below its last descendant.
    const edge = position === "before" ? row : this.subtree(row).at(-1);
    const rect = edge.getBoundingClientRect();
    const origin = this.element.getBoundingClientRect();
    const title = row.querySelector("td.title").getBoundingClientRect();
    const bar = this.barTarget;
    bar.style.top = `${(position === "before" ? rect.top : rect.bottom) - origin.top}px`;
    bar.style.setProperty("--tb-x", title.left - origin.left);
    bar.style.setProperty("--tb-depth", depthOf(row));
    bar.hidden = false;
  }

  clear() {
    this.barTarget.hidden = true;
    this.element.querySelectorAll(".is-drop-target").forEach((el) => el.classList.remove("is-drop-target"));
  }
}

window.wagtail.app.register("tb-tree", TreeController);
