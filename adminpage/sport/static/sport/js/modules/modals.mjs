function prepareModal(id, size = 'modal-md') {
    const modal = $(id);
    modal.addClass('modal')
        .addClass('fade')
        .attr('tabindex', '-1')
        .attr('role', 'dialog')
        .attr('aria-labelledby', `${id}-title`);
    modal.html(`<div class="modal-dialog ${size}" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="${id}-title"></h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body text-left"></div>
          <div class="modal-footer"></div>
        </div>
      </div>`)
}


async function openModal(id, apiUrl) {
    const modal = $(id)
    const title = modal.find('.modal-title');
    const body = modal.find('.modal-body');
    const footer = modal.find('.modal-footer');
    body.empty();
    footer.empty();
    body.append($('<div class="spinner-border" role="status"></div>'));
    title.text('Loading...');
    modal.modal('show');
    let data;
    if (apiUrl) {
        if (Array.isArray(apiUrl)) {
            data = await Promise.all(apiUrl.map(url => fetch(url).then(res => res.json())));
        } else {
            data = await fetch(apiUrl).then(res => res.json());
        }
    }else{
        data = null;
    }
    body.empty();
    return {data, title, body, footer};
}

function renderGroupModalBody(body, data) {
    const {
        trainers,
        capacity,
        current_load,
        training_class,
        hours,
    } = data;

    const p = body.append('<p>').children('p:last-child');
    if (capacity) {
        p.append(`<div>Available places: <strong>${capacity - current_load}/${capacity}</strong></div>`);
    }
    if (training_class) {
        p.append(`<div>Class: <strong>${training_class}</strong></div>`);
    }

    if (trainers.length) {
        const trainers_html = trainers.map((t) => (`<li>
                                 ${t.trainer_first_name} ${t.trainer_last_name}
                                 <a href="mailto:${t.trainer_email}">${t.trainer_email}</a>
                             </li>`))
        body.append(`<strong>Teacher(s)</strong>:
                            ${trainers_html.join('\n')}
                     <p></p>`);
    }
    if (hours) {
        body.append(`<p>Marked hours: <strong>${hours.toFixed(2)}</strong></p>`);
    }
}

function formatTime(time) {
    return time.substring(0, time.length - 3);
}

async function openGroupInfoModalForStudent(apiUrl, enrollErrorCb = () => 0) {
    const {data, title, body, footer} = await openModal('#group-info-modal', apiUrl)
    const {custom_name, group_id, group_name, is_enrolled, capacity, current_load, is_primary, can_enroll, schedule} = data;

    let disabled_attr;

    if (is_enrolled) {
        footer.html(`
            <div class="container">
                <div class="row justify-content-between">
                    <div><button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button></div>
                    <div><button type="button" class="btn btn-danger ${disabled_attr}" ${disabled_attr}>Unenroll</button></div>
                </div>
            </div>
        `);
        footer.find('.btn-danger').click(() => enroll(group_id, 'unenroll'));
    } else {
        disabled_attr = (current_load >= capacity || !can_enroll) ? 'disabled' : ''
        footer.html(`
            <div class="container">
                <div class="row justify-content-between">
                    <div><button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button></div>
                    <div><button type="button" class="btn btn-success ${disabled_attr}" ${disabled_attr}
                     ${disabled_attr=='disabled' && 'data-bs-toggle="tooltip" data-bs-placement="top" title="To enroll you should unenroll from your sport group first" style="cursor: default;"'}>Enroll</button></div>
                </div>
            </div>
        `);
        footer.find('.btn-success').click(() => enroll(group_id, 'enroll', enrollErrorCb));
    }
    title.text('');
    if (!!custom_name) {
        title.append(`<h2> <span class="badge badge-info text-uppercase">${group_name}</span></h2>`);
    } else {
        title.append(`<h2> <span class="badge badge-info text-uppercase">${custom_name}</span></h2>`);
    }
    renderGroupModalBody(body, data);
    if (schedule && schedule.length > 0) {

        const days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ];
        schedule.sort(
            (a, b) => (a.weekday > b.weekday) ? 1 : (a.start > b.start) ? 1 : -1
        )
        body.append(`
            <strong>Schedule</strong>:<br>
        `)

        let currentDay = null;

        for (let training of schedule) {
            if (training.weekday !== currentDay) {
                body.append(`<i>${days[training.weekday]}</i>:`);
                currentDay = training.weekday;
            }
            body.append(`<li>${formatTime(training.start)} - ${formatTime(training.end)}</li>`);
        }

    }
    return data;
}

async function openTrainingInfoModalForStudent(apiUrl, checkinErrorCb = () => 0) {
    const {data, title, body, footer} = await openModal('#group-info-modal', apiUrl)
    const { training, can_check_in, checked_in, hours } = data;
    const group = training.group;
    const date = (new Date(training.start)).toLocaleDateString('en-GB');
    const start_time = new Date(training.start);
    const end_time = new Date(training.end);
    let disabled_attr = (training.load >= group.capacity || !can_check_in) ? 'disabled' : ''

    if (checked_in) {
        footer.html(`
            <div class="container">
                <div class="row justify-content-between">
                    <div><button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button></div>
                    <div><button type="button" class="btn btn-danger">Cancel check in</button></div>
                </div>
            </div>
        `);
        footer.find('.btn-danger').click(() => training_cancel_check_in(training.id));
    } else {
        footer.html(`
            <div class="container">
                <div class="row justify-content-between">
                    <div><button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button></div>
                    <div><button type="button" class="btn btn-success ${disabled_attr}" ${disabled_attr}>Check in</button></div>
                </div>
            </div>
        `);
        footer.find('.btn-success').click(() => training_check_in(training.id));
    }

    title.text(''); // To clear after loading
    if (!!training.custom_name) {
        title.append(`<h2> <span class="badge badge-info text-uppercase">${training.custom_name}</span></h2>`);
    } else {
        title.append(`<h2> <span class="badge badge-info text-uppercase">${group.name}</span></h2>`);
    }

    if (hours) {
        body.append(`<div class="alert alert-success" role="alert">You got <strong>${hours}</strong> hour${hours > 1 ? 's': ''}.</div>`);
    }

    body.append(`<div>Time and date: <b>${formatTime(start_time.toLocaleTimeString('en-GB'))} - ${formatTime(end_time.toLocaleTimeString('en-GB'))}, ${date}</b></div>`);
    if (group.capacity) {
        body.append(`<div>Available places: <b>${group.capacity - training.load}/${group.capacity}</b></div>`);
    }
    if (training.place) {
        body.append(`<div>Place: <b>${training.place}</b></div>`);
    }
    body.append(`<div>Accredited: <b>${group.accredited ? 'Yes' : 'No'}</b></div>`);
    body.append('<br>')
    if (!group.accredited) {
        body.append(`<div class="alert alert-warning" role="alert">You <b>can't get</b> sport hours for this training.</div>`);
    }
        

    body.append('<br><b>Description</b>:')
    if (group.sport.description) {
        body.append(`<div>${group.sport.description}</div>`);
    }
    body.append('<br>')

    let teachers_html = [];
    group.teachers.forEach((teacher) => {
        teachers_html.push(`<li>${teacher.first_name} ${teacher.last_name} <a href="mailto:${teacher.email}">${teacher.email}</a></li>`);
    });
    body.append(`<b>Teacher${group.teachers.length > 1 ? 's': ''}</b>: ${teachers_html.join('\n')}`);

    return data;
}

async function unenroll_by_trainer(group_id, student_id) {
    await sendResults('/api/enrollment/unenroll_by_trainer', { group_id, student_id })
    $(`#enrolled-student-${student_id}`).remove()
}

async function openGroupInfoModalForTrainer(apiUrl) {
    const {data, title, body, footer} = await openModal('#group-info-modal', apiUrl);
    footer.html('<div><button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button></div>');
    title.html(`<h2><span class="badge badge-info text-uppercase">${data[0].group_name}</span></h2>`);
    renderGroupModalBody(body, data[0]);
    const tbody = body.append(`<p>Enrolled students:
                    <table class="table table-hover table-responsive-md">
                        <thead>
                            <th>Student name</th>
                            <th>Last attended</th>
                            <th>Unenroll</th>
                        </thead>
                    </table>
                 </p>`).find('table').append('<tbody>');
    const last_attended_dates = data[1].last_attended_dates.sort(
        (a, b) => new Date(b.last_attended) - new Date(a.last_attended)
    );
    const icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
      <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
      <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4L4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
    </svg>`
    last_attended_dates.forEach(info => {
        tbody.append(`<tr id="enrolled-student-${info.student_id}">
            <td>${info.full_name}</td>
            <td>${info.last_attended ? info.last_attended.split('T')[0] : 'N/A'}</td>
            <td>
                <button class="btn btn-outline-danger" onclick="unenroll_by_trainer(${data[0].group_id}, ${info.student_id})">${icon}</button>
            </td>
        </tr>`)
    });
}
