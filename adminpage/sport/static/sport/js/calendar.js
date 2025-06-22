async function openGroupInfoModal(info) {
    const {group_id, current_load} = await openGroupInfoModalForStudent(
        `/api/group/${info.event.extendedProps.group_id}`,
        update_rendered_events_load
    )
    update_rendered_events_load(group_id, current_load, false);
}

function update_rendered_events_load(group_id, load=0, set_max = true) {
    calendar.getEvents().filter(event => event.extendedProps.group_id === group_id).forEach(
        event => event.setExtendedProp(
            'current_load',
            (set_max) ? event.extendedProps.capacity : load
        )
    );
}

function render(info) {
    let element = info.el;
    let event = info.event;

    let props = event.extendedProps;
    element.style.fontSize = "99";
    element.style.backgroundColor = (props.load >= props.capacity) ? '#f00' : get_color(props.group_id)
    element.style.cursor = 'pointer';
}

let calendar;
$(function () {
    prepareModal('#group-info-modal');
    let calendarEl = document.getElementById('calendar');

    calendar = new FullCalendar.Calendar(calendarEl, {
        plugins: ['timeGrid'],
        defaultView: 'timeGridWeek',
        header: {
            left: 'title',
            center: '',
            right: ''
            // right: 'today, prev, next'
        },
        height: 'auto',
        timeZone: 'Europe/Moscow',
        firstDay: 1,
        allDaySlot: false,
        slotDuration: '00:30:00',
        minTime: '07:00:00',
        maxTime: '23:00:00',
        defaultTimedEventDuration: '01:30',
        eventClick: openGroupInfoModal,
        eventRender: render,
        // Event format: yyyy-mm-dd
        events: '/api/calendar/' + calendarEl.getAttribute('data-sport') + '/schedule',
        eventTimeFormat: { // like '14:30'
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }
    });

    calendar.render();
});

async function submit_sport_type() {
    const parser = document.createElement('a');
    parser.href = document.URL;
    url = parser.pathname;
    const sport_id = Number(url.match(/[^calendar\/sport\/](.*)/g)[0]);
    try {
        await sendResults('/api/select_sport', {"sport_id": sport_id}, 'POST',  asJSON = true)
        toastr.success("You have successfully chosen " + sport_name + " for current semester!")
    } catch (error) {
        toastr.error(error.message);
    }
    return false;
}