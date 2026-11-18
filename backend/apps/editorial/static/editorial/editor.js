document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('textarea[data-editorial-richtext="true"]').forEach((textarea) => {
    const editor = document.createElement("div");
    editor.className = "editorial-richtext";
    editor.contentEditable = "true";
    editor.setAttribute("role", "textbox");
    editor.setAttribute("aria-multiline", "true");
    editor.setAttribute("aria-label", "متن خبر");
    editor.dir = "rtl";
    editor.innerHTML = textarea.value;

    const toolbar = document.createElement("div");
    toolbar.className = "editorial-toolbar";
    toolbar.setAttribute("role", "toolbar");
    toolbar.setAttribute("aria-label", "قالب‌بندی متن خبر");
    const controls = [
      ["پاراگراف", "formatBlock", "p"],
      ["تیتر", "formatBlock", "h2"],
      ["زیرتیتر", "formatBlock", "h3"],
      ["ضخیم", "bold"],
      ["مورب", "italic"],
      ["نقل‌قول", "formatBlock", "blockquote"],
      ["فهرست", "insertUnorderedList"],
      ["فهرست شماره‌دار", "insertOrderedList"],
      ["پیوند", "createLink"],
    ];
    controls.forEach(([label, command, value]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.setAttribute("aria-label", label);
      button.addEventListener("mousedown", (event) => event.preventDefault());
      button.addEventListener("click", () => {
        editor.focus();
        let argument = value || null;
        if (command === "createLink") {
          argument = window.prompt("آدرس پیوند (http یا https)");
          if (!argument || !/^https?:\/\//i.test(argument)) return;
        }
        document.execCommand(command, false, argument);
        textarea.value = editor.innerHTML;
      });
      toolbar.appendChild(button);
    });
    editor.addEventListener("input", () => { textarea.value = editor.innerHTML; });
    editor.addEventListener("paste", (event) => {
      event.preventDefault();
      document.execCommand("insertText", false, event.clipboardData.getData("text/plain"));
    });
    textarea.form?.addEventListener("submit", () => { textarea.value = editor.innerHTML; });
    textarea.hidden = true;
    textarea.parentNode.insertBefore(toolbar, textarea);
    toolbar.after(editor);
  });
});
