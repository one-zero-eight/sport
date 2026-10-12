//Fetch data
function fetchGroups() {
    return fetch('/api/medical_groups')
        .then(response => response.json())
        .then(data => data);
}
var group_array = await fetchGroups();

//Create array with groups(id, name, description)
group_array = group_array["medical_groups"];

import disciplines_array from "./disciplines.js";
import attendance_chart from "./attendance.js";
import {parseData} from "./attendance.js";

//Export disciplines
export default group_array;

//Get HTML elements
var dropdown_group = document.getElementById('groupList');
var group_button = document.getElementById('groupButton');
var drop_down_content_group = document.getElementById('dropDownContentGroup');

var disciplineButton = document.getElementById('disciplinesButton');

// Generate options
for (var i = 0; i < group_array.length; i++) {

    if (i === 0) {
        var allOption = document.createElement('li');
        allOption.textContent = "All";
        allOption.classList.add("drop-down-item");
        dropdown_group.appendChild(allOption);
        allOption.id = "groupAll";
        allOption.addEventListener('click', async function () {
            group_button.textContent = this.textContent;
            drop_down_content_group.classList.toggle('show');
        });
    }

    var option = document.createElement('li');
    option.textContent = group_array[i].name;
    var text = group_array[i].name
    console.log(group_array)
    option.classList.add("drop-down-item");

    option.addEventListener('click', async function () {
        group_button.textContent = this.textContent;
        drop_down_content_group.classList.toggle('show');

        //Add functionality

        var groupName = this.textContent;
        var groupId = group_array.find(x => x.name === groupName).id;
        if (disciplineButton.textContent === "All" || disciplineButton.textContent === "Disciplines") {

            function fetchDataForClickedGroupAllSport() {
                return fetch("/api/analytics/attendance?medical_group_id=" + groupId)
                    .then(response => response.json())
                    .then(data => data);
            }

            var data = await fetchDataForClickedGroupAllSport();
            var parsedData = parseData(data);

            attendance_chart.data.datasets[0].data = parsedData;
            attendance_chart.update();
        }

        else{
            var disciplineName = disciplineButton.textContent;
            var disciplineId = disciplines_array.find(x => x.name === disciplineName).id;

            function fetchDataForClickedGroupSpecialSport() {
                return fetch("/api/analytics/attendance?sport_id=" + disciplineId +
                    "&medical_group_id=" + groupId)
                    .then(response => response.json())
                    .then(data => data);
            }

            var data = await fetchDataForClickedGroupSpecialSport();
            var parsedData = parseData(data);

            attendance_chart.data.datasets[0].data = parsedData;
            attendance_chart.update();
        }

});
    dropdown_group.appendChild(option);
}

// Show/hide dropdown content
group_button.addEventListener('click', function () {
    drop_down_content_group.classList.toggle('show');
});

// Close dropdown content when clicking outside
document.addEventListener('click', function (event) {
    if (!group_button.contains(event.target) && !drop_down_content_group.contains(event.target)) {
        drop_down_content_group.classList.remove('show');
    }
});
