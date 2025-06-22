//Fetch data
function fetchDisciplines() {
    return fetch('/api/sports')
        .then(response => response.json())
        .then(data => data);
}
var disciplines_array = await fetchDisciplines();
import attendance_chart from "./attendance.js";
import {parseData} from "./attendance.js";
import group_array from "./group.js";

//Create array with disciplines(id, name, special)
disciplines_array = disciplines_array["sports"];

//Export disciplines
export default disciplines_array;

//Get HTML elements
var dropdown_disciplines = document.getElementById('disciplinesList');
var disciplines_button = document.getElementById('disciplinesButton');
var drop_down_content_disciplines = document.getElementById('dropDownContentDisciplines');
var group_button = document.getElementById('groupButton');

// Generate options for disciplines dropdown
for (var i = 0; i < disciplines_array.length; i++) {

    if (i === 0) {
        var allOption = document.createElement('li');
        allOption.textContent = "All";
        allOption.classList.add("drop-down-item");
        dropdown_disciplines.appendChild(allOption);
        allOption.id = "disciplinesAll";
        allOption.addEventListener('click', async function () {
            disciplines_button.textContent = this.textContent;
            drop_down_content_disciplines.classList.toggle('show');
        });
    }

    var option = document.createElement('li');
    option.textContent = disciplines_array[i].name;
    option.classList.add("drop-down-item");
    dropdown_disciplines.appendChild(option);
    option.addEventListener('click', async function () {
        disciplines_button.textContent = this.textContent;
        drop_down_content_disciplines.classList.toggle('show');

        //Add functionality

        var disciplineName = this.textContent;
        var disciplineId = disciplines_array.find(x => x.name === disciplineName).id;
        if (group_button.textContent === "All" || group_button.textContent === "Groups") {

                function fetchDataForClickedDisciplineAllGroups() {
                    return fetch("/api/analytics/attendance?sport_id=" + disciplineId)
                        .then(response => response.json())
                        .then(data => data);
                }
                var data = await fetchDataForClickedDisciplineAllGroups();
                var parsedData = parseData(data);

                attendance_chart.data.datasets[0].data = parsedData;
                attendance_chart.update();
        } else {
            var groupName = group_button.textContent;
            if (groupName === "All" || groupName === "Group") {
                function fetchDataForClickedGroupAndDiscipline() {
                    return fetch("/api/analytics/attendance?sport_id=" + disciplineId)
                        .then(response => response.json())
                        .then(data => data);
                }

                var data = await fetchDataForClickedGroupAndDiscipline();
                var parsedData = parseData(data);
                console.log(data)
                console.log(parsedData)

                attendance_chart.data.datasets[0].data = parsedData;
                attendance_chart.update();
            } else {
                var groupId = group_array.find(x => x.name === groupName).id;
                function fetchDataForClickedGroupAndDiscipline() {
                    return fetch("/api/analytics/attendance?medical_group_id=" + groupId + "&sport_id=" + disciplineId)
                        .then(response => response.json())
                        .then(data => data);
                }

                var data = await fetchDataForClickedGroupAndDiscipline();
                var parsedData = parseData(data);
                console.log(parsedData)

                attendance_chart.data.datasets[0].data = parsedData;
                attendance_chart.update();
            }
        }
    });
}

// Show/hide dropdown content
disciplines_button.addEventListener('click', function () {
    drop_down_content_disciplines.classList.toggle('show');
});

// Close dropdown content when clicking outside
document.addEventListener('click', function (event) {
    if (!disciplines_button.contains(event.target) &&
        !drop_down_content_disciplines.contains(event.target)) {
        drop_down_content_disciplines.classList.remove('show');
    }
});
