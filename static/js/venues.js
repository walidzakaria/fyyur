// this is to apply delete button events
const deleteBtns = document.querySelectorAll('.delete-button');
for (let i=0; i < deleteBtns.length; i++) {
    const btn = deleteBtns[i];
    btn.onclick = function(e) {

        const venueId = e.target.dataset['id'];
        fetch(`/venues/${venueId}`, {
            method: 'DELETE'
        })
        .then(function() {
            window.location.href = '/';
        })
        .catch(function(e){
            console.log(e);
        });
    }
}