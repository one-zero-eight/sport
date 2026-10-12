logout_btn = document.getElementById("logout-btn");

if (logout_btn != null) {
    logout_btn.onclick = logout;
}

function logout() {
    delete_cookie("access_token");
    delete_cookie("id_token");
    delete_cookie("refresh_token");

    location.reload();
}

function delete_cookie(name) {
    document.cookie = name + '=; Max-Age=-99999999;';
}