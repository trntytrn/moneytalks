let ENDPOINT_URL = "http://localhost:3000";

document.getElementById('fetch-data-btn').addEventListener('click', fetchData);

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.endsWith('dashboard.html')) {
        fetchSpendingHabits();
    }
});

function fetchData() {
    fetch(ENDPOINT_URL + "/data") // Replace with your backend API URL
        .then(response => response.json())
        .then(data => {
            document.getElementById('api-result').innerText = JSON.stringify(data, null, 2);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('api-result').innerText = 'Error fetching data';
        });
}

function fetchSpendingHabits() {
    const token = getCookie('jwt');
    fetch(ENDPOINT_URL + "/get-spending-habits", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 0) {
            document.getElementById('spending-habits-content').innerText = JSON.stringify(data.spending_habits, null, 2);
        } else {
            document.getElementById('spending-habits-content').innerText = 'Unable to fetch spending habits';
        }
    })
    .catch(error => {
        console.error('Error fetching spending habits:', error);
        document.getElementById('spending-habits-content').innerText = 'Error fetching spending habits';
    });
}