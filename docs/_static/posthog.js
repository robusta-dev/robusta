function setupCopyListener() {
  let codeCells = document.querySelectorAll("pre[id^=codecell]");
  console.log(codeCells);
  codeCells.forEach(element => element.addEventListener('copy', (event) => {
    reportCopy(element);
  }));
  let copyButtons = document.querySelectorAll("button[data-clipboard-target*=codecell]");
  console.log(copyButtons);
  copyButtons.forEach(element => element.addEventListener('click', (event) => {
    reportCopy(element);
  }));
}

function reportCopy(baseElement) {
  let id_element = (baseElement.closest('div[id^=cb-]')); // corresponds to the :name: in the code-blocks. prefix cb-
  if (id_element) {
    let message = 'copied from codeblock: ' + id_element.getAttribute('id');
    posthog.capture(message);
  }
}
