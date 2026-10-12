class ApiError extends Error {
    constructor(message, code, status) {
        super(message);
        this.code = code;
        this.status = status;
    }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrf_token = getCookie('csrftoken');

async function sendResults(url, data, method = 'POST', asJSON = true) {
    const headers = {"X-CSRFToken": csrf_token};
    if (asJSON) {
        headers['Content-Type'] = 'application/json';
    }
    const response = await fetch(url, {
        method: method,
        body: asJSON ? JSON.stringify(data) : data,
        headers,
    });
    const responseData = await response.json()
    if (!response.ok) {
        throw new ApiError(
            responseData.detail,
            responseData.code,
            response.status
        );
    }
    return responseData;
}

function goto_profile() {
    window.location.href = "/profile";
}

function reload_page() {
    window.location.reload();
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.addEventListener("load", () => resolve(img));
    img.addEventListener("error", err => reject(err));
    img.src = src;
  });
}
