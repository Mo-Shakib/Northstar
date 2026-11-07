(() => {
  const copyButton = document.getElementById("copy-command");
  const commandBlock = document.getElementById("install-commands");
  const copyStatus = document.getElementById("copy-status");

  if (!copyButton || !commandBlock) {
    return;
  }

  copyButton.hidden = false;

  const copyText = async (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const fallback = document.createElement("textarea");
    fallback.value = text;
    fallback.setAttribute("readonly", "");
    fallback.className = "clipboard-fallback";
    document.body.appendChild(fallback);
    fallback.select();
    document.execCommand("copy");
    fallback.remove();
  };

  copyButton.addEventListener("click", async () => {
    const commands = commandBlock.textContent.trim();
    const originalLabel = copyButton.textContent;

    try {
      await copyText(commands);
      copyButton.textContent = "Copied";
      copyButton.classList.add("is-copied");
      if (copyStatus) {
        copyStatus.textContent = "Install commands copied to the clipboard.";
      }
    } catch {
      copyButton.textContent = "Select to copy";
      if (copyStatus) {
        copyStatus.textContent = "Could not copy automatically. Select the commands to copy them.";
      }
    }

    window.setTimeout(() => {
      copyButton.textContent = originalLabel;
      copyButton.classList.remove("is-copied");
      if (copyStatus) {
        copyStatus.textContent = "";
      }
    }, 1800);
  });
})();
