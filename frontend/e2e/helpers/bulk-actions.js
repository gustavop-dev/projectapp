/**
 * Driving the accounting bulk bar, which is one [Acciones] menu rather than a
 * row of buttons.
 *
 * Headless UI only renders the menu panel while it is open, so anything that
 * asserts about an action — that it is offered, missing or disabled — has to
 * open the menu first, or it passes for the wrong reason.
 */

/** Open the actions menu over the current selection. */
export async function openBulkMenu(page, prefix) {
  await page.getByTestId(`${prefix}-bulk-actions`).click();
}

/** Open the menu and run one action by its visible label. */
export async function bulkAction(page, prefix, label) {
  await openBulkMenu(page, prefix);
  await page.getByRole('menuitem', { name: label }).click();
}

/** The menu item for `label`, with the menu already open. */
export function bulkMenuItem(page, label) {
  return page.getByRole('menuitem', { name: label });
}
