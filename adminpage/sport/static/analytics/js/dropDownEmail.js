var studentEmails = [
    "e.valikov@innopolis.university",
    "a.katin@innopolis.university",
    "a.katin@innopolis.university",
    "e.valikov@innopolis.university",
    "a.katin@innopolis.university",
    "a.katin@innopolis.university"
];

var input = document.getElementById("name");
var emailList = document.getElementById("emailsList");
var dropDownContentEmails = document.getElementById("dropDownContentEmails");


for (var i = 0; i < studentEmails.length; i++) {
    var option = document.createElement('li');
    option.textContent = studentEmails[i];
    option.classList.add("drop-down-item");
    emailList.appendChild(option);
    option.addEventListener('click', async function () {
        input.value = this.textContent;
        dropDownContentEmails.classList.toggle('show');
    });
}


// Updating email list after inserting letters
input.addEventListener("keyup", function () {
    emailList.innerHTML = "";

    var inputValue = input.value;

    for (var i = 0; i < studentEmails.length; i++) {
        if (studentEmails[i].includes(inputValue)) {
            var emailOption = document.createElement("li");
            emailOption.classList.add("drop-down-item");
            emailOption.innerText = studentEmails[i];
            emailList.appendChild(emailOption);
            emailOption.addEventListener('click', async function () {
                input.value = this.textContent;
                dropDownContentEmails.classList.toggle('show');
            });
        }
    }
})
;

input.addEventListener('click', function () {
    dropDownContentEmails.classList.toggle('show');
});

document.addEventListener('click', function (event) {
    if (!input.contains(event.target) && !dropDownContentEmails.contains(event.target)) {
        dropDownContentEmails.classList.remove('show');
    }
});
