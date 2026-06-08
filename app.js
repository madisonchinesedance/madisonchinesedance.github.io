/* Add a global helper for adding nav items at runtime (optional) */
function addNavItem(routeId, label, parentId = null) {
  const header = headerConfig; // headerConfig is defined later in the script
  if (!header) return;

  const nav = header.nav || [];
  if (!parentId) {
    nav.push({ route: routeId, label });
  } else {
    const parent = nav.find((item) => item.route === parentId);
    if (parent) {
      parent.items = parent.items || [];
      parent.items.push({ route: routeId, label });
    } else {
      // If parent not found, add as top-level
      nav.push({ route: routeId, label });
    }
  }
  header.nav = nav;
  // Re-render header
  renderHeader();
}