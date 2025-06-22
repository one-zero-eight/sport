//Fetch default analytics data for all sports and all groups
function fetchDefaultAnalytics() {
    return fetch('/api/analytics/attendance')
        .then(response => response.json())
        .then(data => data);
}

//Create default array for all sports and all groups with date + number
var all_analytics_array = await fetchDefaultAnalytics();

//Create array with date + number as a dictionary

function parseData(data) {
    var parsedData = [];
    for (let key in data) {
        var dict = {};
        dict["date"] = key;
        dict["students"] = data[key];
        parsedData.push(dict);
    }
    var parsedData2 = parsedData.map(item => ({
        x: new Date(item["date"]),
        y: item["students"],
    }));
    return parsedData2;
}


var default_array_with_dicts = [];
for (let key in all_analytics_array) {
    var dict = {};
    dict["date"] = key;
    dict["students"] = all_analytics_array[key];
    default_array_with_dicts.push(dict);
}

// Convert date strings to actual Date objects
var parsedDataDefault = default_array_with_dicts.map(item => ({
    x: new Date(item["date"]),
    y: item["students"],
}));

//Get HTML elements
const ctx = document.getElementById('attendanceChart').getContext('2d');

// Create a line chart
const attendance_chart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [{
            label: 'Number of Students',
            data: parsedDataDefault,
            borderColor: '#008141',
            backgroundColor: '#00814122',
            pointRadius: 3,
            pointBackgroundColor: '#008141',
            pointBorderColor: '#ffffff',
            pointHoverRadius: 5,
            lineTension: 0,
            borderWidth: 2
        }]
    },
    options: {
        scales: {
             x: {
              type: 'time',
                 time: {
                     unit: 'week'
                 },
                  ticks: {
                      source: 'data' // Force x-axis ticks to be based on data points
                  }
             },
            y: {
                type: 'linear',
                ticks: {
                    beginAtZero: true // Start y-axis from zero
                }
            }
        }
    }
});

//Import data
import disciplines_array from './disciplines.js';
import group_array from './group.js';

//Export data
export default attendance_chart;
export {parseData};

//All buttons functionality

//Get li HTML elements

var groupAll = document.getElementById("groupAll");
var disciplineAll = document.getElementById("disciplinesAll");

//Get HTML elements

var groupButton = document.getElementById("groupButton");
var disciplineButton = document.getElementById("disciplinesButton");

groupAll.addEventListener('click', async function () {

    if (disciplineButton.textContent === "All" || disciplineButton.textContent === "Disciplines") {
        attendance_chart.data.datasets[0].data = parsedDataDefault;
        attendance_chart.update();
    }
    else{
        var disciplineName = disciplineButton.textContent;
        var disciplineId = disciplines_array.find(x => x.name === disciplineName).id;

        function fetchDataForAllGroupsSpecialSport() {
        return fetch("/api/analytics/attendance?sport_id=" + disciplineId)
        .then(response => response.json())
        .then(data => data);
        }

        var data = await fetchDataForAllGroupsSpecialSport();
        var parsedData = parseData(data);

        attendance_chart.data.datasets[0].data = parsedData;
        attendance_chart.update();
    }
});

disciplineAll.addEventListener('click', async function () {
    if (groupButton.textContent === "All" || groupButton.textContent === "Group") {
        attendance_chart.data.datasets[0].data = parsedDataDefault;
        attendance_chart.update();
    }
    else{
        var groupName = groupButton.textContent;
        var groupId = group_array.find(x => x.name === groupName).id;

        function fetchDataForAllSportsSpecialGroup() {
            return fetch("/api/analytics/attendance?sport_id=" + groupId)
                .then(response => response.json())
                .then(data => data);
        }

        var data = await fetchDataForAllSportsSpecialGroup();
        var parsedData = parseData(data);

        attendance_chart.data.datasets[0].data = parsedData;
        attendance_chart.update();
    }
});


