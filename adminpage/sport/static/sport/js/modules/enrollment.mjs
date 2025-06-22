async function enroll(group_id, action, errorHandler=function(group_id){}) {
    sendResults(`/api/enrollment/${action}`, {group_id: group_id})
        .then(data => {
            goto_profile();
        })
        .catch(function (error) {
            errorHandler(group_id);
            toastr.error(error.message);
        })
}

async function training_check_in(training_id, errorHandler=function(training_id){}) {
    sendResults(`/api/training/${training_id}/check_in`)
        .then((response) => {
            if (response.ok) {
                if (response.ok) {
                    return response.text();
                }
                throw new Error('Something went wrong.');
            }
        })
        .then(() => {
            toastr.success(`You have been successfuly checked in.`, `Checked in`, 1000);
            $('#group-info-modal').modal('hide');
            calendar.refetchEvents();
        })
        .catch(function (error) {
            errorHandler(training_id);
			toastr.error(`${error.message}`, 'Server error');
        })
}

async function training_cancel_check_in(training_id, errorHandler=function(training_id){}) {
    sendResults(`/api/training/${training_id}/cancel_check_in`)
        .then((response) => {
            if (response.ok) {
                if (response.ok) {
                    return response.text();
                }
                throw new Error('Something went wrong.');
            }
        })
        .then(() => {
            toastr.success(`You have been successfuly cancelled check in.`, `Cancelled check in`, 1000);
            $('#group-info-modal').modal('hide');
            calendar.refetchEvents();
        })
        .catch(function (error) {
            errorHandler(training_id);
			toastr.error(`${error.message}`, 'Server error');
        })
}