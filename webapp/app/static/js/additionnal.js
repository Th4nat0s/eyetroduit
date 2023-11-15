// Miracle here https://jsfiddle.net/fx6a6n6x/
// Copies a string to the clipboard. Must be called from within an event handler such as click.
// May return false if it failed, but this is not always
// possible. Browser support for Chrome 43+, Firefox 42+, Edge and IE 10+.
// No Safari support, as of (Nov. 2015). Returns false.
// IE: The clipboard feature may be disabled by an adminstrator. By default a prompt is
// shown the first time the clipboard is used (per session).
function copyToClipboard(text) {
    if (window.clipboardData && window.clipboardData.setData) {
        // IE specific code path to prevent textarea being shown while dialog is visible.
        clipboardData.setData("Text", text);
        showAlert();
    } else if (document.queryCommandSupported && document.queryCommandSupported("copy")) {
        var textarea = document.createElement("textarea");
        textarea.textContent = text;
        textarea.style.position = "fixed";  // Prevent scrolling to bottom of page in MS Edge.
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand("copy");  // Security exception may be thrown by some browsers.
            showAlert();
        } catch (ex) {
            console.warn("Copy to clipboard failed.", ex);
        } finally {
            setTimeout(function() {
                document.body.removeChild(textarea);
            }, 1000); // 1000 milliseconds (1 second) delay
        }
    }
}


function showAlert() {
    var alertDiv = document.createElement("div");
    alertDiv.textContent = "Url Copied";
    alertDiv.style.position = "fixed";
    alertDiv.style.top = "50%";
    alertDiv.style.left = "50%";
    alertDiv.style.transform = "translate(-50%, -50%)";
    alertDiv.style.padding = "10px";
    alertDiv.style.background = "#4CAF50";
    alertDiv.style.color = "white";
    alertDiv.style.borderRadius = "5px";
    document.body.appendChild(alertDiv);

    setTimeout(function() {
        document.body.removeChild(alertDiv);
    }, 1000); // 1000 milliseconds (1 second) delay
}


function openLinkInExistingTab(link) {
       window.open(link, 'Telegram Web'); // Utilisez le même nom de fenêtre que le site B
}


function switchmodal(idmodal, textmodal){
  image = document.getElementById('view_modal_img');
  image.src = "/screen/" + idmodal;
  ref = document.getElementById('view_modal_href');
  ref.href = "/screen/" + idmodal;
  mtext = document.getElementById('view_modal_text');
  mtext.textContent = textmodal;
  }
