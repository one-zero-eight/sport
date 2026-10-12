// load semesters
let CURRENT_SEMESTER = null;
let CURRENT_SEMESTER_HAS_EXERCISES = null;

function change_semester() {
	const semester_id = $('#fitness-test-semester-choose').val();
	const semester_name = $('#fitness-test-semester-choose').find('option:selected').text();
	if (semester_id != CURRENT_SEMESTER.id) {
		$("#fitness-test-session-btn").attr('class', 'btn btn-warning mr-3');
		$('#fitness-test-session-btn').text('Conduct a new retake session');
		$('#fitness-test-session-btn').attr('href', `/fitness_test/new?semester_id=${semester_id}&semester_name=${semester_name}`);
	} else if (!CURRENT_SEMESTER_HAS_EXERCISES) {
		$("#fitness-test-session-btn").attr('class', 'btn btn-danger mr-3 disabled');
		$('#fitness-test-session-btn').text('There are no exercises for this semester, please add them first');
		$('#fitness-test-session-btn').attr('href', '');
	} else {
		$("#fitness-test-session-btn").attr('class', 'btn btn-success mr-3');
		$('#fitness-test-session-btn').text('Conduct a new fitness test session');
		$('#fitness-test-session-btn').attr('href', `/fitness_test/new?semester_id=${CURRENT_SEMESTER.id}&semester_name=${semester_name}`);
	}
}

// load semesters
function load_semesters() {
	fetch("/api/semester?with_ft_exercises=true", {
		method: "GET",
		"X-CSRFToken": csrf_token,
	})
		.then((response) => {
			return response.json();
		})
		.then((options) => {
			const options_semester_ids = options.map(({id}) => id);
			CURRENT_SEMESTER_HAS_EXERCISES = options_semester_ids.some((id) => id === CURRENT_SEMESTER.id);

			if (!CURRENT_SEMESTER_HAS_EXERCISES) {
				options.push(CURRENT_SEMESTER);
			}
			options.sort((a, b) => b.id - a.id);
			options.forEach((option) => {
				$("#fitness-test-semester-choose").append(
					$(`<option value=${option.id} ${CURRENT_SEMESTER.id == option.id ? 'selected': ''}>${option.name}</option>`)
				);
			});
			change_semester();
		})
		.catch(function (error) {
			toastr.error("Error while loading semesters", `Semesters error ${error}`);
		});
}

// load current semester
fetch("/api/semester?current=true", {
	method: "GET",
	"X-CSRFToken": csrf_token,
})
	.then((response) => {
		return response.json();
	})
	.then((current_semester) => {
		CURRENT_SEMESTER = current_semester[0];
		load_semesters();
	})
	.catch(function () {
		toastr.error("Error while loading current semester", "Semester error");
	});


// load sessions
fetch("/api/fitnesstest/sessions", {
	method: "GET",
	"X-CSRFToken": csrf_token,
})
	.then((response) => {
		return response.json();
	})
	.then((data) => {
		data.forEach((session) => {
			const semester = session.semester;
			let session_row = $(
				// Temporary solution, before was with the django url:
				`<tr style="cursor: pointer" onclick="location.href='${session.id}?semester_id=${semester.id}&semester_name=${semester.name}'">
                    <td>
                        <span class="text-uppercase font-weight-bold">${semester.name} ${session.retake ? "Retake" : ""}</span>
                    </td>
                    <td>
                        <span>
                        ${new Date(session.date).toLocaleString("en-GB")}
                        </span>
                    </td>
                    <td>
                        <span class="badge badge-pill badge-light">${session.teacher}</span>
                    </td>
                </tr>`
			);
			$("#ft-session-table-body").prepend(session_row);
		});
	})
	.catch(function (err) {
		console.log(err);
	});
