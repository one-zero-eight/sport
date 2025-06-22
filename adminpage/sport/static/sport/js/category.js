function mark_club_as_full(club_id) {
    $(`#club-${club_id}`).remove().insertAfter($(".club-dropdown a:last-child")).children('a span').text('0');
}

function mark_club_as_free(club_id, free_places) {
    const elem = $(`#club-${club_id}`)
    if (elem.children('a span').text() === '0') {
        elem.remove().insertBefore($(".club-dropdown a:first-child")).children('a span').text(free_places.toString());
    }
}

async function openGroupInfoModal(id) {
    const {group_id, capacity, current_load} = await openGroupInfoModalForStudent(`/api/group/${id}`);
    if (current_load >= capacity) {
        mark_club_as_full(group_id);
    } else {
        mark_club_as_free(group_id, capacity - current_load);
    }
}

$(function () {
    prepareModal('#group-info-modal');
});