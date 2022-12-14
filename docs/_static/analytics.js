

// noinspection DuplicatedCode
function setupCopyListener() {
  let codeCells = document.querySelectorAll("pre[id^=codecell]");
  codeCells.forEach(element => element.addEventListener('copy', (event) => {
    reportCopy(element);
  }));
  let copyButtons = document.querySelectorAll("button[data-clipboard-target*=codecell]");
  copyButtons.forEach(element => element.addEventListener('click', (event) => {
    reportCopy(element);
  }));
}

function trackPageViewEvent() {
  const pageUrl = window.location.href;
  trackEvent('DocsPageview', {'pageUrl': pageUrl});
  if (pageUrl.endsWith('/installation.html')) {
    trackEvent('InstallationPageview', {'pageUrl': pageUrl});
  }
  if (pageUrl.endsWith('/argocd-installation.html')) {
    trackEvent('ArgoCDInstallationPageview', {'pageUrl': pageUrl});
  }
}

function trackEvent(event, properties) {
  posthog.capture(event, properties)
  analytics.track(event, properties)
}

function reportCopy(baseElement) {
  // don’t track users who ask not to be tracked
  if (navigator.doNotTrack === "1") {
    return
  }
  let id_element = (baseElement.closest('div[id^=cb-]')); // corresponds to the :name: in the code-blocks. prefix cb-
  if (id_element) {
    const path = window.location.pathname;
    const page = path.split("/").pop();
    if (page && page.endsWith('html')) {
      trackEvent('copied from a codeblock on: ' + page)
    }
    trackEvent('copied from codeblock: ' + id_element.getAttribute('id'))
  }
}
